#!/usr/bin/env python3
"""Generate README.md from template using GitHub API data."""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

GITHUB_API = "https://api.github.com"
SHIELDS = "https://img.shields.io/badge"
SKILLICONS = "https://skillicons.dev/icons"

LANG_MAP: dict[str, str] = {
    "C#": "cs", "C++": "cpp", "C": "c",
    "CSS": "css", "Dart": "dart", "Go": "go",
    "HTML": "html", "Java": "java", "JavaScript": "javascript",
    "Kotlin": "kotlin", "Lua": "lua", "PHP": "php",
    "Python": "python", "Ruby": "ruby", "Rust": "rust",
    "Sass": "sass", "SCSS": "sass", "ShaderLab": "unity",
    "Shell": "bash", "Svelte": "svelte", "Swift": "swift",
    "TypeScript": "ts", "Vue": "vue",
}

# Maps provider name → skillicons slug
SOCIAL_ICONS: dict[str, str] = {
    "bluesky": "bluesky", "dev.to": "devto", "discord": "discord",
    "facebook": "facebook", "github": "github", "gitlab": "gitlab",
    "instagram": "instagram", "linkedin": "linkedin", "mastodon": "mastodon",
    "medium": "medium", "netlify": "netlify", "reddit": "reddit",
    "stackoverflow": "stackoverflow", "twitch": "twitch", "twitter": "twitter",
    "vercel": "vercel", "x": "twitter", "youtube": "youtube",
}

# Maps URL domain → provider key in SOCIAL_ICONS
DOMAIN_MAP: dict[str, str] = {
    "bsky.app": "bluesky", "bluesky.social": "bluesky",
    "dev.to": "dev.to", "github.com": "github", "gitlab.com": "gitlab",
    "instagram.com": "instagram", "linkedin.com": "linkedin",
    "mastodon.social": "mastodon", "medium.com": "medium",
    "netlify.app": "netlify", "twitch.tv": "twitch",
    "twitter.com": "x", "vercel.app": "vercel",
    "x.com": "x", "youtu.be": "youtube", "youtube.com": "youtube",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def gh_fetch(path: str, token: str) -> object:
    url = path if path.startswith("http") else f"{GITHUB_API}{path}"
    req = Request(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "readme-generator",
    })
    try:
        with urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except (URLError, json.JSONDecodeError) as e:
        print(f"Warning: Failed to fetch {url}: {e}", file=sys.stderr)
        return None


def truncate(text: str, max_len: int) -> str:
    return text if len(text) <= max_len else f"{text[:max_len - 3]}..."


def domain_to_provider(url: str) -> str | None:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return DOMAIN_MAP.get(host) or DOMAIN_MAP.get(".".join(host.split(".")[-2:]))


def flat_badge(label: str, color: str) -> str:
    label = label.replace(" ", "%20").replace("-", "--")
    return f"![](https://img.shields.io/badge/{label}-{color}?style=flat-square&labelColor=0d0d1a)"


def lang_badge(lang: str, color: str = "5865F2") -> str:
    return flat_badge(f"-{lang}", color)


def stars_badge(count: int, color: str = "555") -> str:
    return flat_badge(f"stars-{count:,}", color)


def repo_card(name: str, url: str, desc: str, lang: str = "", star_count: int = 0, lang_color: str = "5865F2") -> str:
    badges = (lang_badge(lang, lang_color) + " " if lang else "") + \
             (stars_badge(star_count) + " " if star_count > 0 else "")
    return f'<div align="left">\n\n**[{name}]({url})**&nbsp; {badges}\n\n{desc}\n\n</div>'


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def build_top_languages(username: str, token: str) -> str:
    repos, page = [], 1
    while len(repos) < 200:
        batch = gh_fetch(f"/users/{username}/repos?sort=updated&per_page=100&page={page}", token)
        if not batch:
            break
        repos.extend(r for r in batch if not r.get("fork") and not r.get("private"))
        if len(batch) < 100:
            break
        page += 1

    lang_bytes: dict[str, int] = {}
    for repo in repos[:50]:
        for lang, count in (gh_fetch(f"/repos/{repo['full_name']}/languages", token) or {}).items():
            lang_bytes[lang] = lang_bytes.get(lang, 0) + count

    icons = [
        LANG_MAP[lang]
        for lang, _ in sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)
        if lang in LANG_MAP
    ][:8]

    if not icons:
        return '<div align="center"><p>No language data available</p></div>'
    return f'<div align="center"><img src="{SKILLICONS}?i={",".join(icons)}" alt="Top Languages" /></div>'


def build_social_links(username: str, user_data: dict, token: str) -> str:
    links: list[str] = []
    seen: set[str] = set()

    def add_link(provider: str, url: str) -> None:
        if not url or provider in seen:
            return
        slug = SOCIAL_ICONS.get(provider) or SOCIAL_ICONS.get(domain_to_provider(url) or "")
        if slug:
            seen.add(provider)
            label = provider.replace(".", " ").title()
            links.append(
                f'<a href="{url}" target="_blank" rel="noopener noreferrer" style="margin: 0 12px;">'
                f'<img alt="{label}" src="{SKILLICONS}?i={slug}" width="48" height="48" /></a>'
            )

    for s in gh_fetch(f"/users/{username}/social_accounts", token) or []:
        add_link(s.get("provider", ""), s.get("url", ""))

    if twitter := user_data.get("twitter_username"):
        if "twitter" not in seen and "x" not in seen:
            add_link("x", f"https://x.com/{twitter}")

    if blog := user_data.get("blog", "").strip():
        blog = blog if blog.startswith("http") else f"https://{blog}"
        add_link(domain_to_provider(blog) or "website", blog)

    # Fetch email (only works when token belongs to this user)
    email = user_data.get("email")
    if not email:
        me = gh_fetch("/user", token)
        if me and me.get("login", "").lower() == username.lower():
            emails = gh_fetch("/user/emails", token) or []
            email = (
                next((e["email"] for e in emails if e.get("primary")), None)
                or next((e["email"] for e in emails if e.get("verified")), None)
                or (emails[0]["email"] if emails else None)
            )
    if email:
        links.append(
            f'<a href="mailto:{email}" target="_blank" rel="noopener noreferrer" style="margin: 0 12px;">'
            f'<img alt="Email" src="{SKILLICONS}?i=gmail" width="48" height="48" /></a>'
        )

    if not links:
        return '<p align="center"><em>No social links available</em></p>'
    return f'<div align="center">\n  <p>\n    {"".join(links)}\n  </p>\n</div>'


def build_active_projects(username: str, token: str) -> str:
    seen: set[str] = set()
    cards: list[str] = []

    for event in gh_fetch(f"/users/{username}/events?per_page=50", token) or []:
        if len(cards) >= 4:
            break
        if event.get("type") not in {"PushEvent", "PullRequestEvent", "CreateEvent"}:
            continue
        repo_name = event.get("repo", {}).get("name", "")
        if not repo_name or repo_name in seen:
            continue
        seen.add(repo_name)
        repo = gh_fetch(f"/repos/{repo_name}", token)
        if repo and not repo.get("private"):
            cards.append(repo_card(
                name=repo_name.split("/")[-1],
                url=repo["html_url"],
                desc=truncate(repo.get("description") or "No description available", 80),
                lang=repo.get("language", ""),
                star_count=repo.get("stargazers_count", 0),
            ))

    return "\n\n".join(cards) if cards else "<p><em>No active projects at the moment</em></p>"


def build_latest_repos(username: str, token: str) -> str:
    repos = gh_fetch(f"/users/{username}/repos?sort=created&direction=desc&per_page=10", token) or []
    items = [r for r in repos if not r.get("fork") and not r.get("private")][:3]

    if not items:
        return "<p><em>No repositories found</em></p>"

    return "\n\n".join(
        repo_card(
            name=r["name"],
            url=r["html_url"],
            desc=truncate(r.get("description") or "No description", 100),
            lang=r.get("language", ""),
            star_count=r.get("stargazers_count", 0),
        )
        for r in items
    )


def build_recent_prs(username: str, token: str) -> str:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    data = gh_fetch(
        f"/search/issues?q=author:{username}+type:pr+created:>={cutoff}&sort=created&order=desc&per_page=5",
        token,
    )
    items = (data or {}).get("items", [])

    lines = []
    for item in items:
        parts = item.get("repository_url", "").rstrip("/").rsplit("/", 2)
        if len(parts) < 3:
            continue
        repo_name = f"{parts[-2]}/{parts[-1]}"
        is_merged = bool(item.get("pull_request", {}).get("merged_at"))
        state = item.get("state", "open")
        if is_merged:
            badge = flat_badge("merged", "5865F2")
        elif state == "open":
            badge = flat_badge("open", "238636")
        else:
            badge = flat_badge("closed", "555")
        title = truncate(item.get("title", "Untitled"), 60)
        lines.append(
            f'<div align="left">\n\n'
            f'{badge} **[{title}]({item["html_url"]})**\\\n'
            f'<sub>[{repo_name}](https://github.com/{repo_name})</sub>\n\n'
            f'</div>'
        )

    return "\n\n".join(lines) if lines else "<p><em>No recent pull requests.</em></p>"


def build_recent_stars(username: str, token: str) -> str:
    items = gh_fetch(f"/users/{username}/starred?sort=created&direction=desc&per_page=5", token) or []

    if not items:
        return "<p><em>No recent stars.</em></p>"

    return "\n\n".join(
        repo_card(
            name=s.get("full_name", "Unknown"),
            url=s.get("html_url", ""),
            desc=truncate(s.get("description") or "No description", 80),
            lang=s.get("language", ""),
            star_count=s.get("stargazers_count", 0),
            lang_color="555",
        )
        for s in items
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    username = os.getenv("GH_USERNAME") or os.getenv("GITHUB_ACTOR", "")
    token = os.getenv("GH_PAT") or os.getenv("GITHUB_TOKEN", "")

    if not username or not token:
        print("Error: GH_USERNAME and GH_PAT (or GITHUB_TOKEN) are required.", file=sys.stderr)
        return 1

    root = Path(__file__).parent.parent
    template_path = root / "README.gtpl"
    output_path = root / "README.md"

    if not template_path.exists():
        print(f"Error: Template not found at {template_path}", file=sys.stderr)
        return 1

    print(f"Generating README for {username}...")

    user_data = gh_fetch(f"/users/{username}", token)
    if not user_data:
        print("Error: Could not fetch user data.", file=sys.stderr)
        return 1

    display_name = (user_data.get("name") or username).split()[0]

    replacements = {
        "{{USER_NAME}}":       display_name,
        "{{USER_LOGIN}}":      username,
        "{{TOP_LANGUAGES}}":   build_top_languages(username, token),
        "{{SOCIAL_LINKS}}":    build_social_links(username, user_data, token),
        "{{WORKING_ON}}":      build_active_projects(username, token),
        "{{LATEST_PROJECTS}}": build_latest_repos(username, token),
        "{{RECENT_PRS}}":      build_recent_prs(username, token),
        "{{RECENT_STARS}}":    build_recent_stars(username, token),
    }

    content = template_path.read_text(encoding="utf-8")
    for key, value in replacements.items():
        content = content.replace(key, value)

    try:
        output_path.write_text(content, encoding="utf-8")
        print(f"Successfully generated {output_path}")
        return 0
    except OSError as e:
        print(f"Error writing README: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
