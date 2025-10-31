#!/usr/bin/env python3
"""Generate README.md from template using GitHub API data."""
import os
import sys
import json
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone
from typing import Any

GITHUB_API = "https://api.github.com"
SKILLICONS_BASE = "https://skillicons.dev/icons"

# Language to skillicon mapping
LANG_MAP = {
    "TypeScript": "ts", "JavaScript": "javascript", "Python": "python", "PHP": "php",
    "HTML": "html", "CSS": "css", "C": "c", "C++": "cpp", "C#": "cs", "Go": "go",
    "Rust": "rust", "Java": "java", "Svelte": "svelte", "ShaderLab": "unity",
    "shaderlab": "unity", "Shell": "bash", "SCSS": "sass", "Sass": "sass",
}

# Social provider to icon mapping
SOCIAL_ICONS = {
    "x": "twitter", "twitter": "twitter", "instagram": "instagram", "linkedin": "linkedin",
    "youtube": "youtube", "twitch": "twitch", "facebook": "facebook", "mastodon": "mastodon",
    "reddit": "reddit", "stackoverflow": "stackoverflow", "dev.to": "devto", "medium": "medium",
    "bluesky": "bluesky", "github": "github",
}

DOMAIN_MAP = {
    "x.com": "x", "twitter.com": "x", "instagram.com": "instagram", "linkedin.com": "linkedin",
    "youtube.com": "youtube", "youtu.be": "youtube", "twitch.tv": "twitch",
    "mastodon.social": "mastodon", "medium.com": "medium", "dev.to": "devto",
    "bsky.app": "bluesky", "bluesky.social": "bluesky",
}


def env(name: str, default: str = "") -> str:
    """Get environment variable."""
    return os.getenv(name) or default


def env_int(name: str, default: int) -> int:
    """Get integer environment variable."""
    try:
        return int(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


def env_bool(name: str, default: bool = False) -> bool:
    """Get boolean environment variable."""
    val = os.getenv(name, "").strip().lower()
    return val in {"1", "true", "yes", "y", "on"} if val else default


def gh_get(path: str, token: str) -> Any:
    """Fetch from GitHub API."""
    req = Request(
        f"{GITHUB_API}{path}",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "readme-generator",
        },
    )
    with urlopen(req, timeout=30) as resp:
        return json.load(resp)


def truncate(text: str, max_len: int) -> str:
    """Truncate text with ellipsis."""
    return text if len(text) <= max_len else text[:max_len - 3] + "..."


def get_lang_icon(lang: str) -> str | None:
    """Convert language name to skillicon slug."""
    if lang in LANG_MAP:
        return LANG_MAP[lang]
    lang_lower = lang.lower()
    for key, value in LANG_MAP.items():
        if key.lower() == lang_lower:
            return value
    return None


def build_top_languages(username: str, token: str, limit: int = 8) -> str:
    """Build top languages section."""
    repos = []
    page = 1
    
    # Fetch repositories
    while len(repos) < 200:
        try:
            page_repos = gh_get(
                f"/users/{username}/repos?sort=updated&per_page=100&page={page}",
                token
            )
            if not page_repos:
                break
            repos.extend([r for r in page_repos if not r.get("fork") and not r.get("private")])
            if len(page_repos) < 100:
                break
            page += 1
        except Exception:
            break
    
    # Aggregate languages
    lang_bytes: dict[str, int] = {}
    for repo in repos[:100]:
        try:
            langs = gh_get(f"/repos/{repo.get('full_name')}/languages", token) or {}
            for lang, bytes_count in langs.items():
                lang_bytes[lang] = lang_bytes.get(lang, 0) + bytes_count
        except Exception:
            continue
    
    if not lang_bytes:
        return '<div align="center"><p>No language data available</p></div>'
    
    # Map to icons
    icons = []
    for lang, _ in sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True):
        icon = get_lang_icon(lang)
        if icon:
            icons.append(icon)
            if len(icons) >= limit:
                break
    
    if not icons:
        return '<div align="center"><p>No languages found</p></div>'
    
    icon_list = ",".join(icons)
    return f'<div align="center"><img src="{SKILLICONS_BASE}?i={icon_list}" alt="Top Languages" /></div>'


def build_social_links(username: str, user: Any, token: str) -> str:
    """Build social links section."""
    links = []
    
    # Get social accounts from API
    socials = []
    try:
        api_socials = gh_get(f"/users/{username}/social_accounts", token) or []
        for s in api_socials:
            provider = (s.get("provider") or "").strip().lower()
            url = (s.get("url") or "").strip()
            if provider and url:
                socials.append({"provider": provider, "url": url})
    except Exception:
        pass
    
    # Add Twitter fallback
    twitter = (user.get("twitter_username") or "").strip()
    if twitter and all(s.get("provider") not in {"twitter", "x"} for s in socials):
        socials.append({"provider": "twitter", "url": f"https://x.com/{twitter}"})
    
    # Build social links
    for s in socials:
        provider = s.get("provider", "").lower()
        url = s.get("url", "")
        if not url:
            continue
        
        # Try domain mapping if provider not found
        if provider not in SOCIAL_ICONS:
            try:
                host = urlparse(url).netloc.lower()
                provider = DOMAIN_MAP.get(host, provider)
            except Exception:
                pass
        
        if provider in SOCIAL_ICONS:
            icon = SOCIAL_ICONS[provider]
            alt = provider.replace(".", " ").title()
            links.append(
                f'<a href="{url}" target="_blank" rel="noopener noreferrer" style="margin: 0 24px; display: inline-block;">'
                f'<img alt="{alt}" src="{SKILLICONS_BASE}?i={icon}" width="48" height="48" style="transition: transform 0.2s;" />'
                "</a>"
            )
    
    # Add website
    website = (user.get("blog") or "").strip()
    if website:
        if not website.startswith(("http://", "https://")):
            website = f"https://{website}"
        try:
            host = urlparse(website).netloc.lower().lstrip("www.")
            icon = "github"
            if "github.io" in host:
                icon = "github"
            elif "gitlab.com" in host:
                icon = "gitlab"
            elif "vercel.app" in host:
                icon = "vercel"
            elif "netlify.app" in host:
                icon = "netlify"
            links.append(
                f'<a href="{website}" target="_blank" rel="noopener noreferrer" style="margin: 0 24px; display: inline-block;">'
                f'<img alt="Website" src="{SKILLICONS_BASE}?i={icon}" width="48" height="48" style="transition: transform 0.2s;" />'
                "</a>"
            )
        except Exception:
            pass
    
    # Add email
    email = (user.get("email") or "").strip()
    if not email:
        try:
            me = gh_get("/user", token) or {}
            if (me.get("login") or "").lower() == username.lower():
                emails = gh_get("/user/emails", token) or []
                email = next((e.get("email") for e in emails if e.get("primary")), None) or \
                        next((e.get("email") for e in emails if e.get("verified")), None) or \
                        (emails[0].get("email") if emails else "")
        except Exception:
            pass
    
    if email:
        links.append(
            f'<a href="mailto:{email}" target="_blank" rel="noopener noreferrer" style="margin: 0 24px; display: inline-block;">'
            f'<img alt="Email" src="{SKILLICONS_BASE}?i=gmail" width="48" height="48" style="transition: transform 0.2s;" />'
            "</a>"
        )
    
    # Add GitHub link if enabled
    if env_bool("SHOW_GITHUB_LINK", False):
        links.append(
            f'<a href="https://github.com/{username}" target="_blank" rel="noopener noreferrer" style="margin: 0 24px; display: inline-block;">'
            f'<img alt="GitHub" src="{SKILLICONS_BASE}?i=github" width="48" height="48" style="transition: transform 0.2s;" />'
            "</a>"
        )
    
    if not links:
        return ""
    
    icons_html = "".join(links)
    return f'<div align="center">\n  <p>\n    {icons_html}\n  </p>\n</div>'


def build_working_on(events: Any, token: str, limit: int = 4) -> str:
    """Build active projects list."""
    repos = []
    for event in events:
        if event.get("type") in {"PushEvent", "PullRequestEvent", "CreateEvent"}:
            repo_name = event.get("repo", {}).get("name")
            if repo_name and repo_name not in repos:
                repos.append(repo_name)
                if len(repos) >= limit:
                    break
    
    lines = []
    for repo in repos:
        name = repo.split("/")[-1]
        try:
            data = gh_get(f"/repos/{repo}", token) or {}
            if data.get("private"):
                continue
            desc = truncate(data.get("description") or "No description available", 80)
            lines.append(f"* [{name}](https://github.com/{repo}) - {desc}")
        except Exception:
            lines.append(f"* [{name}](https://github.com/{repo})")
    
    return "\n".join(lines) if lines else "* No active projects"


def build_latest_projects(repos: Any, limit: int = 3) -> str:
    """Build latest repositories list."""
    items = [
        r for r in repos
        if not r.get("fork") and not r.get("private") and r.get("size", 0) > 0
    ][:limit]
    
    if not items:
        return "* No repositories found"
    
    return "\n".join(
        f"* [**{r['name']}**]({r['html_url']}) - {r.get('description') or 'No description available'}"
        for r in items
    )


def build_recent_prs(prs: Any, token: str) -> str:
    """Build recent pull requests list."""
    items = (prs or {}).get("items", [])
    if not items:
        return "* No recent pull requests - time to contribute! 🔀"
    
    lines = []
    for item in items[:5]:
        title = truncate(item.get("title", "Untitled"), 60)
        api_repo_url = item.get("repository_url", "")
        
        # Skip private repos
        if api_repo_url:
            try:
                path = api_repo_url.replace("https://api.github.com", "")
                repo_meta = gh_get(path, token) or {}
                if repo_meta.get("private"):
                    continue
            except Exception:
                pass
        
        repo_name = api_repo_url.split("/")[-1] if api_repo_url else "repo"
        repo_html_url = api_repo_url.replace("api.github.com/repos", "github.com") if api_repo_url else ""
        lines.append(f"* [{title}]({item.get('html_url')}) on [{repo_name}]({repo_html_url})")
    
    return "\n".join(lines) if lines else "* No recent pull requests - time to contribute! 🔀"


def build_recent_stars(stars: Any) -> str:
    """Build recently starred repositories list."""
    if not stars:
        return "* No recent stars - discover some awesome repos! ⭐"
    
    return "\n".join(
        f"* [{star.get('owner', {}).get('login', 'owner')}/{star.get('name', 'repo')}]"
        f"({star.get('html_url')}) - {truncate(star.get('description') or 'No description available', 80)}"
        for star in stars[:5]
    )


def generate_readme(template_path: str, output_path: str, username: str, token: str) -> None:
    """Generate README.md from template."""
    # Fetch data
    user = gh_get(f"/users/{username}", token)
    events = gh_get(f"/users/{username}/events?per_page=50", token)
    repos_newest = gh_get(
        f"/users/{username}/repos?sort=created&direction=desc&per_page=5", token
    )
    stars = gh_get(
        f"/users/{username}/starred?sort=created&direction=desc&per_page=5", token
    )
    
    # Get recent PRs
    prs_days = env_int("PRS_DAYS", 30)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=prs_days)).strftime("%Y-%m-%d")
    prs = gh_get(
        f"/search/issues?q=author:{username}+type:pr+created:>={cutoff}&sort=created&order=desc&per_page=5",
        token,
    )
    
    # Extract first name
    full_name = user.get("name") or env("FALLBACK_NAME", username)
    user_name = full_name.split()[0] if full_name else username
    
    # Build replacements
    replacements = {
        "{{USER_NAME}}": user_name,
        "{{TOP_LANGUAGES}}": build_top_languages(username, token, env_int("TOP_LANGUAGES_LIMIT", 8)),
        "{{SOCIAL_LINKS}}": build_social_links(username, user, token),
        "{{WORKING_ON}}": build_working_on(events, token, env_int("WORKING_ON_LIMIT", 4)),
        "{{LATEST_PROJECTS}}": build_latest_projects(repos_newest, env_int("LATEST_PROJECTS_LIMIT", 3)),
        "{{RECENT_PRS}}": build_recent_prs(prs, token),
        "{{RECENT_STARS}}": build_recent_stars(stars),
    }
    
    # Generate README
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


def main() -> int:
    """Main entry point."""
    username = env("GH_USERNAME") or env("GITHUB_ACTOR")
    token = env("GH_PAT") or env("GITHUB_TOKEN")
    
    if not username:
        print("Missing username: set GH_USERNAME or GITHUB_ACTOR", file=sys.stderr)
        return 2
    
    if not token:
        print("Missing GitHub token: set GH_PAT or GITHUB_TOKEN", file=sys.stderr)
        return 2
    
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(root, "README.gtpl")
    output_path = os.path.join(root, "README.md")
    
    generate_readme(template_path, output_path, username, token)
    return 0


if __name__ == "__main__":
    sys.exit(main())
