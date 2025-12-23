#!/usr/bin/env python3
"""Generate README.md from template using GitHub API data."""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional, Set

# --- Configuration ---
GITHUB_API = "https://api.github.com"
SKILLICONS_BASE = "https://skillicons.dev/icons"

LANG_MAP = {
    "TypeScript": "ts", "JavaScript": "javascript", "Python": "python", "PHP": "php",
    "HTML": "html", "CSS": "css", "C": "c", "C++": "cpp", "C#": "cs", "Go": "go",
    "Rust": "rust", "Java": "java", "Svelte": "svelte", "ShaderLab": "unity",
    "Shell": "bash", "SCSS": "sass", "Sass": "sass", "Vue": "vue", "Kotlin": "kotlin",
    "Swift": "swift", "Dart": "dart", "Ruby": "ruby", "Lua": "lua",
}

SOCIAL_ICONS = {
    "x": "twitter", "twitter": "twitter", "instagram": "instagram", "linkedin": "linkedin",
    "youtube": "youtube", "twitch": "twitch", "facebook": "facebook", "mastodon": "mastodon",
    "reddit": "reddit", "stackoverflow": "stackoverflow", "dev.to": "devto", "medium": "medium",
    "bluesky": "bluesky", "github": "github", "gitlab": "gitlab", "vercel": "vercel",
    "netlify": "netlify", "discord": "discord",
}

DOMAIN_MAP = {
    "x.com": "x", "twitter.com": "x", "instagram.com": "instagram", "linkedin.com": "linkedin",
    "youtube.com": "youtube", "youtu.be": "youtube", "twitch.tv": "twitch",
    "mastodon.social": "mastodon", "medium.com": "medium", "dev.to": "devto",
    "bsky.app": "bluesky", "bluesky.social": "bluesky", "github.com": "github",
    "gitlab.com": "gitlab", "vercel.app": "vercel", "netlify.app": "netlify",
}

# --- Helpers ---

def get_env(name: str, default: Any = "") -> Any:
    """Get environment variable with type conversion."""
    val = os.getenv(name, "")
    if not val:
        return default
    if isinstance(default, bool):
        return val.lower() in {"1", "true", "yes", "y", "on"}
    if isinstance(default, int):
        try:
            return int(val)
        except ValueError:
            return default
    return val

def gh_fetch(url: str, token: str) -> Optional[Any]:
    """Fetch data from GitHub API."""
    if not url.startswith("http"):
        url = f"{GITHUB_API}{url}"
    
    req = Request(
        url,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "readme-generator",
        },
    )
    try:
        with urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except (URLError, json.JSONDecodeError) as e:
        print(f"Warning: Failed to fetch {url}: {e}", file=sys.stderr)
        return None

def truncate(text: str, max_len: int) -> str:
    """Truncate text to max length."""
    return text if len(text) <= max_len else f"{text[:max_len-3]}..."

def get_icon_slug(name: str, mapping: Dict[str, str]) -> Optional[str]:
    """Case-insensitive icon lookup."""
    if name in mapping:
        return mapping[name]
    name_lower = name.lower()
    return next((v for k, v in mapping.items() if k.lower() == name_lower), None)

def guess_provider_from_url(url: str) -> Optional[str]:
    """Guess social provider from URL domain."""
    try:
        host = urlparse(url).netloc.lower().lstrip("www.")
        return DOMAIN_MAP.get(host) or DOMAIN_MAP.get(".".join(host.split(".")[-2:]))
    except Exception:
        return None

# --- Content Builders ---

def build_top_languages(username: str, token: str) -> str:
    """Build top languages section."""
    repos = []
    page = 1
    while len(repos) < 200:
        data = gh_fetch(f"/users/{username}/repos?sort=updated&per_page=100&page={page}", token)
        if not data:
            break
        repos.extend([r for r in data if not r.get("fork") and not r.get("private")])
        if len(data) < 100:
            break
        page += 1

    lang_stats: Dict[str, int] = {}
    for repo in repos[:50]:  # Limit to save API calls
        langs = gh_fetch(f"/repos/{repo['full_name']}/languages", token)
        if langs:
            for lang, count in langs.items():
                lang_stats[lang] = lang_stats.get(lang, 0) + count

    if not lang_stats:
        return '<div align="center"><p>No language data available</p></div>'

    limit = get_env("TOP_LANGUAGES_LIMIT", 8)
    sorted_langs = sorted(lang_stats.items(), key=lambda x: x[1], reverse=True)
    icons = []
    for lang, _ in sorted_langs:
        slug = get_icon_slug(lang, LANG_MAP)
        if slug:
            icons.append(slug)
        if len(icons) >= limit:
            break

    if not icons:
        return '<div align="center"><p>No languages found</p></div>'
    
    icons_str = ",".join(icons)
    return f'<div align="center"><img src="{SKILLICONS_BASE}?i={icons_str}" alt="Top Languages" /></div>'

def build_social_links(username: str, user_data: Dict[str, Any], token: str) -> str:
    """Build social links section."""
    links: List[str] = []
    seen_providers: Set[str] = set()

    def add_link(provider: str, url: str):
        if not url or provider in seen_providers:
            return
        
        slug = get_icon_slug(provider, SOCIAL_ICONS)
        if not slug:
            guessed = guess_provider_from_url(url)
            if guessed:
                slug = SOCIAL_ICONS.get(guessed)
                provider = guessed
        
        if slug:
            seen_providers.add(provider)
            name = provider.replace(".", " ").title()
            links.append(
                f'<a href="{url}" target="_blank" rel="noopener noreferrer" '
                f'style="margin: 0 12px; display: inline-block;">'
                f'<img alt="{name}" src="{SKILLICONS_BASE}?i={slug}" width="48" height="48" '
                f'style="transition: transform 0.2s;" /></a>'
            )

    # Fetch social accounts from API
    socials = gh_fetch(f"/users/{username}/social_accounts", token) or []
    for s in socials:
        add_link(s.get("provider", ""), s.get("url", ""))

    # Twitter/X fallback
    twitter = user_data.get("twitter_username")
    if twitter and "twitter" not in seen_providers and "x" not in seen_providers:
        add_link("x", f"https://x.com/{twitter}")

    # Blog/Website
    website = user_data.get("blog", "").strip()
    if website:
        if not website.startswith(("http://", "https://")):
            website = f"https://{website}"
        add_link("website", website)

    # Email
    email = user_data.get("email")
    if not email:
        me = gh_fetch("/user", token)
        if me and me.get("login", "").lower() == username.lower():
            emails = gh_fetch("/user/emails", token) or []
            email = (
                next((e["email"] for e in emails if e.get("primary")), None) or
                next((e["email"] for e in emails if e.get("verified")), None) or
                (emails[0]["email"] if emails else None)
            )
    
    if email:
        links.append(
            f'<a href="mailto:{email}" target="_blank" rel="noopener noreferrer" '
            f'style="margin: 0 12px; display: inline-block;">'
            f'<img alt="Email" src="{SKILLICONS_BASE}?i=gmail" width="48" height="48" '
            f'style="transition: transform 0.2s;" /></a>'
        )

    # GitHub link (optional)
    if get_env("SHOW_GITHUB_LINK", False):
        add_link("github", f"https://github.com/{username}")

    if not links:
        return "<p align=\"center\"><em>No social links available</em></p>"
    
    links_html = "".join(links)
    return f'<div align="center">\n  <p>\n    {links_html}\n  </p>\n</div>'

def build_active_projects(username: str, token: str) -> str:
    """Build active projects section."""
    events = gh_fetch(f"/users/{username}/events?per_page=50", token) or []
    active_repos = []
    seen = set()
    limit = get_env("WORKING_ON_LIMIT", 4)

    for event in events:
        if len(active_repos) >= limit:
            break
        if event.get("type") in {"PushEvent", "PullRequestEvent", "CreateEvent"}:
            repo_name = event.get("repo", {}).get("name", "")
            if repo_name and repo_name not in seen:
                seen.add(repo_name)
                repo_data = gh_fetch(f"/repos/{repo_name}", token)
                if repo_data and not repo_data.get("private"):
                    desc = truncate(repo_data.get("description") or "No description available", 80)
                    name = repo_name.split("/")[-1]
                    stars = repo_data.get("stargazers_count", 0)
                    stars_badge = f"⭐ {stars}" if stars > 0 else ""
                    active_repos.append(
                        f"<div align=\"left\">\n"
                        f"  <h4>🔹 <a href=\"{repo_data['html_url']}\">{name}</a> {stars_badge}</h4>\n"
                        f"  <p>{desc}</p>\n"
                        f"</div>"
                    )

    if not active_repos:
        return "<p><em>No active projects at the moment</em></p>"
    return "\n\n".join(active_repos)

def build_latest_repos(username: str, token: str) -> str:
    """Build latest repositories section."""
    repos = gh_fetch(f"/users/{username}/repos?sort=created&direction=desc&per_page=10", token) or []
    items = [r for r in repos if not r.get("fork") and not r.get("private")][:get_env("LATEST_PROJECTS_LIMIT", 3)]
    
    if not items:
        return "<p><em>No repositories found</em></p>"

    lines = []
    for r in items:
        stars = r.get("stargazers_count", 0)
        language = r.get("language", "")
        lang_badge = f"<code>{language}</code>" if language else ""
        stars_badge = f"⭐ {stars}" if stars > 0 else ""
        badges = " ".join(filter(None, [lang_badge, stars_badge]))
        desc = truncate(r.get("description") or "No description", 100)
        lines.append(
            f"<div align=\"left\">\n"
            f"  <h4>🔹 <a href=\"{r['html_url']}\"><strong>{r['name']}</strong></a></h4>\n"
            f"  <p>{desc}</p>\n"
            f"  <p>{badges}</p>\n"
            f"</div>"
        )
    return "\n\n".join(lines)

def build_recent_prs(username: str, token: str) -> str:
    """Build recent pull requests section."""
    days = get_env("PRS_DAYS", 30)
    date_cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    
    data = gh_fetch(
        f"/search/issues?q=author:{username}+type:pr+created:>={date_cutoff}"
        f"&sort=created&order=desc&per_page=5",
        token
    )
    items = data.get("items", []) if data else []

    lines = []
    for item in items:
        repo_url = item.get("repository_url", "")
        if repo_url:
            repo_meta = gh_fetch(repo_url.replace("https://api.github.com", ""), token)
            if repo_meta and not repo_meta.get("private"):
                repo_name = repo_meta.get("full_name", "repo")
                title = truncate(item.get("title", "Untitled"), 60)
                state = item.get("state", "open")
                state_emoji = "✅" if state == "merged" else "🔀" if state == "open" else "❌"
                lines.append(
                    f"<div align=\"left\">\n"
                    f"  <p>{state_emoji} <a href=\"{item['html_url']}\"><strong>{title}</strong></a><br/>\n"
                    f"  <sub>in <a href=\"{repo_meta['html_url']}\">{repo_name}</a></sub></p>\n"
                    f"</div>"
                )

    if not lines:
        return "<p><em>No recent pull requests - time to contribute! 🔀</em></p>"
    return "\n".join(lines)

def build_recent_stars(username: str, token: str) -> str:
    """Build recent stars section."""
    stars = gh_fetch(f"/users/{username}/starred?sort=created&direction=desc&per_page=5", token) or []
    
    if not stars:
        return "<p><em>No recent stars - discover some awesome repos! ⭐</em></p>"
    
    lines = []
    for star in stars:
        repo_name = star.get("full_name", "Unknown")
        desc = truncate(star.get("description") or "No description", 80)
        star_count = star.get("stargazers_count", 0)
        stars_badge = f"⭐ {star_count:,}" if star_count > 0 else ""
        lines.append(
            f"<div align=\"left\">\n"
            f"  <p>⭐ <a href=\"{star.get('html_url')}\"><strong>{repo_name}</strong></a> {stars_badge}<br/>\n"
            f"  <sub>{desc}</sub></p>\n"
            f"</div>"
        )
    return "\n".join(lines)

# --- Main ---

def main() -> int:
    """Main execution."""
    username = get_env("GH_USERNAME") or get_env("GITHUB_ACTOR")
    token = get_env("GH_PAT") or get_env("GITHUB_TOKEN")

    if not username or not token:
        print("Error: GH_USERNAME and GH_PAT (or GITHUB_TOKEN) are required.", file=sys.stderr)
        return 1

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(root_dir, "README.gtpl")
    output_path = os.path.join(root_dir, "README.md")

    if not os.path.exists(template_path):
        print(f"Error: Template not found at {template_path}", file=sys.stderr)
        return 1

    print(f"Generating README for {username}...")

    user_data = gh_fetch(f"/users/{username}", token)
    if not user_data:
        print("Error: Could not fetch user data.", file=sys.stderr)
        return 1

    full_name = user_data.get("name") or get_env("FALLBACK_NAME", username)
    display_name = full_name.split()[0] if full_name else username

    replacements = {
        "{{USER_NAME}}": display_name,
        "{{TOP_LANGUAGES}}": build_top_languages(username, token),
        "{{SOCIAL_LINKS}}": build_social_links(username, user_data, token),
        "{{WORKING_ON}}": build_active_projects(username, token),
        "{{LATEST_PROJECTS}}": build_latest_repos(username, token),
        "{{RECENT_PRS}}": build_recent_prs(username, token),
        "{{RECENT_STARS}}": build_recent_stars(username, token),
    }

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        for key, value in replacements.items():
            content = content.replace(key, value)
            
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"Successfully generated {output_path}")
        return 0
    except Exception as e:
        print(f"Error writing README: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
