#!/usr/bin/env python3
"""Generate README.md from template using GitHub API data."""
import os
import sys
import json
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone
from typing import Any

# Constants
GITHUB_API = "https://api.github.com"
RECENT_LIMIT = 5
MAX_REPOS_FOR_LANGUAGES = 100
MAX_REPOS_FETCH = 200
REPOS_PER_PAGE = 100
DEFAULT_PR_DAYS = 30
ICON_SIZE = 32  # Larger default size for better visibility
SOCIAL_ICON_SIZE = 40  # Larger size for social icons
SKILLICONS_BASE = "https://skillicons.dev/icons"
SIMPLICONS_BASE = "https://cdn.simpleicons.org"


# Curated language-to-skillicon slug mapping (mainstream only)
LANGUAGE_MAPPING = {
    # Web and scripting
    "TypeScript": "ts",
    "JavaScript": "javascript",
    "Python": "python",
    "PHP": "php",
    "Ruby": "ruby",
    "Shell": "bash",
    "PowerShell": "powershell",
    "HTML": "html",
    "CSS": "css",
    "Markdown": "markdown",
    "JSON": "json",

    # Systems and general purpose
    "C": "c",
    "C++": "cpp",
    "C#": "cs",
    "Go": "go",
    "Rust": "rust",
    "Java": "java",
    "Kotlin": "kotlin",
    "Swift": "swift",
    "Dart": "dart",
    "R": "r",
    "Scala": "scala",
    "Objective-C": "objc",
    "Lua": "lua",

    # Databases (when present in Linguist language list)
    "PostgreSQL": "postgres",
    "MySQL": "mysql",
    "MongoDB": "mongodb",
    "Redis": "redis",
    "GraphQL": "graphql",
    "Node.js": "nodejs",
    "Deno": "deno",
    "Bun": "bun",
    "Next.js": "nextjs",
    "Nuxt": "nuxt",
    "Tailwind CSS": "tailwind",
    "Astro": "astro",
    "SvelteKit": "svelte",
    "Laravel": "laravel",
    "Django": "django",
    "Flask": "flask",
    "FastAPI": "fastapi",
    "Rails": "rails",
    "Spring": "spring",
    "NestJS": "nestjs",
    "Supabase": "supabase",
    "Firebase": "firebase",
    "Vercel": "vercel",
    "Netlify": "netlify",
    "AWS": "amazonaws",
    "Azure": "azure",
    "GCP": "googlecloud",
    "Kubernetes": "kubernetes",
    "Terraform": "terraform",
    "Git": "git",
    "GitHub": "github",
    "GitLab": "gitlab",
    "Linux": "linux",
    "ShaderLab": "unity",  # Unity's shader language
    "shaderlab": "unity",  # Unity's shader language (lowercase variant)
    "HLSL": "hlsl",
    "GLSL": "glsl",
    "ShaderLab": "unity",
    
    # Frontend meta-languages frequently reported by Linguist
    "Svelte": "svelte",
    "SCSS": "sass",
    "Sass": "sass",
    "Less": "less",
}


def env(name: str, default: str = "") -> str:
    """Get environment variable with default value."""
    return os.getenv(name) or default


def env_int(name: str, default: int) -> int:
    """Get integer environment variable with default value."""
    value = os.getenv(name)
    if not value or not value.strip().isdigit():
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default


def env_bool(name: str, default: bool = False) -> bool:
    """Get boolean environment variable with default value."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def gh_get(path: str, token: str) -> Any:
    """Fetch data from GitHub API."""
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


def limit_text(text: str, max_len: int) -> str:
    """Truncate text to max length with ellipsis."""
    return text if len(text) <= max_len else text[: max_len - 3] + "..."


def normalize_lang_name(lang_name: str) -> str | None:
    """Convert GitHub language name to skillicons.dev format.
    
    Returns None if the language doesn't have a valid icon mapping.
    Handles case-insensitive matching.
    """
    # Try exact match first
    mapped = LANGUAGE_MAPPING.get(lang_name)
    if mapped:
        return mapped
    
    # Try case-insensitive match
    for key, value in LANGUAGE_MAPPING.items():
        if key.lower() == lang_name.lower():
            return value
    
    # Return None for unmapped languages to filter them out
    return None


def create_icon_link(url: str, slug: str, color: str, alt: str, size: int = None) -> str:
    """Create HTML link with colorful icon image."""
    icon_size = size or ICON_SIZE
    return (
        f'<a href="{url}" target="_blank" rel="noopener noreferrer" style="margin: 0 10px;">'
        f'<img alt="{alt}" src="{SIMPLICONS_BASE}/{slug}/{color}" width="{icon_size}" height="{icon_size}" style="transition: transform 0.2s;" />'
        "</a>"
    )


def build_working_on(events: Any, token: str, limit: int = 4) -> str:
    """Build list of repositories user is actively working on."""
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
            desc = limit_text(data.get("description") or "No description available", 80)
            lines.append(f"* [{name}](https://github.com/{repo}) - {desc}")
        except Exception:
            lines.append(f"* [{name}](https://github.com/{repo})")
    
    return "\n".join(lines) if lines else "* No active projects"


def build_latest_projects(repos: Any, limit: int = 3) -> str:
    """Build list of latest repositories."""
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


def build_recent_prs(prs_payload: Any, token: str) -> str:
    """Build list of recent pull requests."""
    items = (prs_payload or {}).get("items", [])
    if not items:
        return "* No recent pull requests - time to contribute! 🔀"
    
    lines = []
    for item in items[:RECENT_LIMIT]:
        title = limit_text(item.get("title", "Untitled"), 60)
        api_repo_url = item.get("repository_url", "")
        repo_name = api_repo_url.split("/")[-1] if api_repo_url else "repo"
        
        # Skip private repositories
        try:
            if api_repo_url:
                path = api_repo_url.replace("https://api.github.com", "")
                repo_meta = gh_get(path, token) or {}
                if repo_meta.get("private"):
                    continue
        except Exception:
            pass
        
        # Convert API repo URL to github.com URL for nicer display links
        repo_html_url = (
            api_repo_url.replace("api.github.com/repos", "github.com") if api_repo_url else ""
        )
        lines.append(f"* [{title}]({item.get('html_url')}) on [{repo_name}]({repo_html_url})")
    
    return "\n".join(lines) if lines else "* No recent pull requests - time to contribute! 🔀"


def build_recent_stars(stars: Any) -> str:
    """Build list of recently starred repositories."""
    if not stars:
        return "* No recent stars - discover some awesome repos! ⭐"
    
    lines = []
    for star in stars[:RECENT_LIMIT]:
        desc = limit_text(star.get("description") or "No description available", 80)
        owner = star.get("owner", {}).get("login", "owner")
        name = star.get("name", "repo")
        lines.append(f"* [{owner}/{name}]({star.get('html_url')}) - {desc}")
    
    return "\n".join(lines)


def build_top_languages(username: str, token: str, limit: int = 8) -> str:
    """Build top languages section using skillicons.dev."""
    # Fetch repositories (paginated)
    repos = []
    page = 1
    
    while len(repos) < MAX_REPOS_FETCH:
        try:
            page_repos = gh_get(
                f"/users/{username}/repos?sort=updated&per_page={REPOS_PER_PAGE}&page={page}",
                token
            )
            if not page_repos:
                break
            repos.extend([r for r in page_repos if not r.get("fork") and not r.get("private")])
            if len(page_repos) < REPOS_PER_PAGE:
                break
            page += 1
        except Exception:
            break
    
    # Aggregate languages from repositories
    language_bytes: dict[str, int] = {}
    for repo in repos[:MAX_REPOS_FOR_LANGUAGES]:
        repo_name = repo.get("full_name", "")
        if not repo_name:
            continue
        try:
            langs = gh_get(f"/repos/{repo_name}/languages", token) or {}
            for lang, bytes_count in langs.items():
                language_bytes[lang] = language_bytes.get(lang, 0) + bytes_count
        except Exception:
            continue
    
    if not language_bytes:
        return "<p align=\"left\">No language data available</p>"
    
    # Sort by bytes and get top languages
    sorted_langs = sorted(language_bytes.items(), key=lambda x: x[1], reverse=True)
    
    # Map to skillicons.dev format, filtering out unmapped languages
    icon_names = []
    for lang_name, _ in sorted_langs:
        icon_name = normalize_lang_name(lang_name)
        if icon_name:
            icon_names.append(icon_name)
            if len(icon_names) >= limit:
                break
    
    if not icon_names:
        return "<p align=\"left\">No languages found</p>"
    
    # Use skillicons.dev combined format
    icon_list = ",".join(icon_names)
    return f'<p align="left"><img src="{SKILLICONS_BASE}?i={icon_list}" alt="Top Languages" /></p>'


def build_social_links(username: str, user: Any, token: str) -> str:
    """Build social links section with icons."""
    website = (user.get("blog") or "").strip()
    # Normalize website to include scheme for correct linking in README
    if website and not (website.startswith("http://") or website.startswith("https://")):
        website = f"https://{website}"
    twitter = (user.get("twitter_username") or "").strip()
    show_github = env_bool("SHOW_GITHUB_LINK", False)

    # Social platform icons configuration: (slug, color_hex, alt_text)
    icons = {
        "x": ("x", "000000", "X"),
        "twitter": ("x", "000000", "X"),
        "instagram": ("instagram", "E4405F", "Instagram"),
        "linkedin": ("linkedin", "0A66C2", "LinkedIn"),
        "youtube": ("youtube", "FF0000", "YouTube"),
        "twitch": ("twitch", "9146FF", "Twitch"),
        "facebook": ("facebook", "1877F2", "Facebook"),
        "mastodon": ("mastodon", "6364FF", "Mastodon"),
        "reddit": ("reddit", "FF4500", "Reddit"),
        "stackoverflow": ("stackoverflow", "F48024", "Stack Overflow"),
        "dev.to": ("devdotto", "0A0A0A", "DEV"),
        "devto": ("devdotto", "0A0A0A", "DEV"),
        "medium": ("medium", "12100E", "Medium"),
        "bluesky": ("bluesky", "0285FF", "Bluesky"),
        # default website fallback icon uses Google Chrome brand
        "website": ("googlechrome", "4285F4", "Website"),
        "github": ("github", "181717", "GitHub"),
    }

    domain_to_provider = {
        "x.com": "x",
        "twitter.com": "x",
        "instagram.com": "instagram",
        "linkedin.com": "linkedin",
        "twitch.tv": "twitch",
        "youtube.com": "youtube",
        "youtu.be": "youtube",
        "facebook.com": "facebook",
        "mastodon.social": "mastodon",
        "medium.com": "medium",
        "dev.to": "dev.to",
        "stackoverflow.com": "stackoverflow",
        "bsky.app": "bluesky",
        "bluesky.social": "bluesky",
    }

    # Collect socials from GitHub API
    socials: list[dict[str, str]] = []
    try:
        api_socials = gh_get(f"/users/{username}/social_accounts", token) or []
        for s in api_socials:
            provider = (s.get("provider") or "").strip().lower()
            url = (s.get("url") or "").strip()
            if provider and url:
                socials.append({"provider": provider, "url": url})
    except Exception:
        pass

    # Add twitter handle fallback if missing
    if twitter and all(s.get("provider") not in {"twitter", "x"} for s in socials):
        socials.append({"provider": "twitter", "url": f"https://x.com/{twitter}"})

    links: list[str] = []

    # Website from profile (choose icon by domain, fallback to Chrome)
    if website:
        try:
            host = urlparse(website).netloc.lower().lstrip("www.")
        except Exception:
            host = ""
        site_icon_map = {
            "github.io": ("github", "181717", "GitHub Pages"),
            "github.com": ("github", "181717", "GitHub"),
            "gitlab.com": ("gitlab", "FC6D26", "GitLab"),
            "vercel.app": ("vercel", "000000", "Vercel"),
            "netlify.app": ("netlify", "00C7B7", "Netlify"),
            "pages.dev": ("cloudflare", "F38020", "Cloudflare Pages"),
            "medium.com": ("medium", "12100E", "Medium"),
            "dev.to": ("devdotto", "0A0A0A", "DEV"),
            "notion.site": ("notion", "000000", "Notion"),
            "notion.so": ("notion", "000000", "Notion"),
            "wordpress.com": ("wordpress", "21759B", "WordPress"),
            "blogspot.com": ("blogger", "FF5722", "Blogger"),
            "hashnode.dev": ("hashnode", "2962FF", "Hashnode"),
            "hashnode.com": ("hashnode", "2962FF", "Hashnode"),
            "substack.com": ("substack", "FF6719", "Substack"),
            "about.me": ("aboutdotme", "00A98F", "About.me"),
        }
        slug, color, alt = icons["website"]
        for domain, icon in site_icon_map.items():
            if host.endswith(domain):
                slug, color, alt = icon
                break
        links.append(create_icon_link(website, slug, color, alt, SOCIAL_ICON_SIZE))

    # Build icons from socials
    for s in socials:
        provider = s.get("provider", "").lower()
        url = s.get("url", "")
        if not url:
            continue
        # Infer provider from domain if unknown
        if provider not in icons:
            try:
                host = urlparse(url).netloc.lower()
                provider = domain_to_provider.get(host, provider)
            except Exception:
                pass
        if provider in icons:
            slug, color, alt = icons[provider]
            links.append(create_icon_link(url, slug, color, alt, SOCIAL_ICON_SIZE))

    # Email (public or primary for self)
    email = (user.get("email") or "").strip()
    if not email:
        try:
            me = gh_get("/user", token) or {}
            if (me.get("login") or "").lower() == username.lower():
                emails = gh_get("/user/emails", token) or []
                primary = next((e.get("email") for e in emails if e.get("primary")), None)
                verified = next((e.get("email") for e in emails if e.get("verified")), None)
                email = primary or verified or (emails[0].get("email") if emails else "")
        except Exception:
            pass

    if email:
        domain = email.split("@")[-1].lower()
        email_icons = {
            "gmail.com": ("gmail", "EA4335", "Gmail"),
            "googlemail.com": ("gmail", "EA4335", "Gmail"),
            "outlook.com": ("microsoftoutlook", "0078D4", "Outlook"),
            "hotmail.com": ("microsoftoutlook", "0078D4", "Outlook"),
            "live.com": ("microsoftoutlook", "0078D4", "Outlook"),
            "office365.com": ("microsoftoutlook", "0078D4", "Outlook"),
            "yahoo.com": ("yahoo", "6001D2", "Yahoo Mail"),
            "proton.me": ("protonmail", "6D4AFF", "Proton"),
            "protonmail.com": ("protonmail", "6D4AFF", "Proton"),
            "icloud.com": ("icloud", "3693F3", "iCloud Mail"),
            "me.com": ("icloud", "3693F3", "iCloud Mail"),
            "mac.com": ("icloud", "3693F3", "iCloud Mail"),
        }
        slug, color, alt = email_icons.get(domain, ("minutemailer", "0EA5E9", "Email"))
        links.append(create_icon_link(f"mailto:{email}", slug, color, alt, SOCIAL_ICON_SIZE))

    if show_github:
        slug, color, alt = icons["github"]
        links.append(create_icon_link(f"https://github.com/{username}", slug, color, alt, SOCIAL_ICON_SIZE))

    if not links:
        return ""
    
    # Professional centered layout with better spacing
    icons_html = "".join(links)
    return (
        '<div align="center">\n'
        '  <p>\n'
        f'    {icons_html}\n'
        '  </p>\n'
        '</div>'
    )


def generate_readme(template_path: str, output_path: str, username: str, token: str) -> None:
    """Generate README.md from template using GitHub API data."""
    # Fetch GitHub data
    user = gh_get(f"/users/{username}", token)
    events = gh_get(f"/users/{username}/events?per_page=50", token)
    repos_newest = gh_get(
        f"/users/{username}/repos?sort=created&direction=desc&per_page={RECENT_LIMIT}", token
    )
    stars = gh_get(
        f"/users/{username}/starred?sort=created&direction=desc&per_page={RECENT_LIMIT}", token
    )
    
    # Calculate PR cutoff date
    prs_days = env_int("PRS_DAYS", DEFAULT_PR_DAYS)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=prs_days)).strftime("%Y-%m-%d")
    prs = gh_get(
        f"/search/issues?q=author:{username}+type:pr+created:>={cutoff}&sort=created&order=desc&per_page={RECENT_LIMIT}",
        token,
    )

    # Extract only first name
    full_name = user.get("name") or env("FALLBACK_NAME", username)
    user_name = full_name.split()[0] if full_name else username

    # Build sections
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
