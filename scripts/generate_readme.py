#!/usr/bin/env python3
"""Generate README.md from template using GitHub API data."""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen

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


def gh_fetch(url: str, token: str) -> object:
    if not url.startswith("http"):
        url = f"{GITHUB_API}{url}"
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
    return text if len(text) <= max_len else f"{text[:max_len-3]}..."


def icon_slug(name: str, mapping: dict) -> str | None:
    return mapping.get(name) or mapping.get(name.lower()) or next(
        (v for k, v in mapping.items() if k.lower() == name.lower()), None
    )


def build_top_languages(username: str, token: str) -> str:
    repos, page = [], 1
    while len(repos) < 200:
        data = gh_fetch(f"/users/{username}/repos?sort=updated&per_page=100&page={page}", token)
        if not data:
            break
        repos.extend(r for r in data if not r.get("fork") and not r.get("private"))
        if len(data) < 100:
            break
        page += 1

    lang_stats: dict[str, int] = {}
    for repo in repos[:50]:
        langs = gh_fetch(f"/repos/{repo['full_name']}/languages", token)
        if langs:
            for lang, count in langs.items():
                lang_stats[lang] = lang_stats.get(lang, 0) + count

    if not lang_stats:
        return '<div align="center"><p>No language data available</p></div>'

    icons = []
    for lang, _ in sorted(lang_stats.items(), key=lambda x: x[1], reverse=True):
        slug = icon_slug(lang, LANG_MAP)
        if slug:
            icons.append(slug)
        if len(icons) >= 8:
            break

    if not icons:
        return '<div align="center"><p>No languages found</p></div>'

    return f'<div align="center"><img src="{SKILLICONS_BASE}?i={",".join(icons)}" alt="Top Languages" /></div>'


def build_social_links(username: str, user_data: dict, token: str) -> str:
    links: list[str] = []
    seen: set[str] = set()

    def add_link(provider: str, url: str):
        if not url or provider in seen:
            return
        slug = icon_slug(provider, SOCIAL_ICONS)
        if not slug:
            # try to guess from URL domain
            try:
                from urllib.parse import urlparse
                host = urlparse(url).netloc.lower().lstrip("www.")
                guessed = DOMAIN_MAP.get(host) or DOMAIN_MAP.get(".".join(host.split(".")[-2:]))
                slug = SOCIAL_ICONS.get(guessed) if guessed else None
                if guessed:
                    provider = guessed
            except Exception:
                return
        if slug:
            seen.add(provider)
            name = provider.replace(".", " ").title()
            links.append(
                f'<a href="{url}" target="_blank" rel="noopener noreferrer" style="margin: 0 12px;">'
                f'<img alt="{name}" src="{SKILLICONS_BASE}?i={slug}" width="48" height="48" /></a>'
            )

    for s in gh_fetch(f"/users/{username}/social_accounts", token) or []:
        add_link(s.get("provider", ""), s.get("url", ""))

    twitter = user_data.get("twitter_username")
    if twitter and "twitter" not in seen and "x" not in seen:
        add_link("x", f"https://x.com/{twitter}")

    website = user_data.get("blog", "").strip()
    if website:
        if not website.startswith(("http://", "https://")):
            website = f"https://{website}"
        add_link("website", website)

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
            f'<img alt="Email" src="{SKILLICONS_BASE}?i=gmail" width="48" height="48" /></a>'
        )

    if not links:
        return '<p align="center"><em>No social links available</em></p>'

    return f'<div align="center">\n  <p>\n    {"".join(links)}\n  </p>\n</div>'


def build_active_projects(username: str, token: str) -> str:
    events = gh_fetch(f"/users/{username}/events?per_page=50", token) or []
    active_repos = []
    seen: set[str] = set()

    for event in events:
        if len(active_repos) >= 4:
            break
        if event.get("type") not in {"PushEvent", "PullRequestEvent", "CreateEvent"}:
            continue
        repo_name = event.get("repo", {}).get("name", "")
        if not repo_name or repo_name in seen:
            continue
        seen.add(repo_name)
        repo = gh_fetch(f"/repos/{repo_name}", token)
        if repo and not repo.get("private"):
            desc = truncate(repo.get("description") or "No description available", 80)
            name = repo_name.split("/")[-1]
            stars = repo.get("stargazers_count", 0)
            stars_badge = f"⭐ {stars}" if stars > 0 else ""
            active_repos.append(
                f'<div align="left">\n'
                f'  <h4>🔹 <a href="{repo["html_url"]}">{name}</a> {stars_badge}</h4>\n'
                f"  <p>{desc}</p>\n"
                f"</div>"
            )

    if not active_repos:
        return "<p><em>No active projects at the moment</em></p>"
    return "\n\n".join(active_repos)


def build_latest_repos(username: str, token: str) -> str:
    repos = gh_fetch(f"/users/{username}/repos?sort=created&direction=desc&per_page=10", token) or []
    items = [r for r in repos if not r.get("fork") and not r.get("private")][:3]

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
            f'<div align="left">\n'
            f'  <h4>🔹 <a href="{r["html_url"]}"><strong>{r["name"]}</strong></a></h4>\n'
            f"  <p>{desc}</p>\n"
            f"  <p>{badges}</p>\n"
            f"</div>"
        )
    return "\n\n".join(lines)


def build_recent_prs(username: str, token: str) -> str:
    date_cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    data = gh_fetch(
        f"/search/issues?q=author:{username}+type:pr+created:>={date_cutoff}"
        f"&sort=created&order=desc&per_page=5",
        token,
    )
    items = data.get("items", []) if data else []

    lines = []
    for item in items:
        # repo name is embedded in repository_url: .../repos/{owner}/{repo}
        repo_url = item.get("repository_url", "")
        parts = repo_url.rstrip("/").rsplit("/", 2)
        if len(parts) < 3:
            continue
        repo_name = f"{parts[-2]}/{parts[-1]}"
        repo_html_url = f"https://github.com/{repo_name}"
        title = truncate(item.get("title", "Untitled"), 60)
        state = item.get("state", "open")
        state_emoji = "✅" if state == "merged" else "🔀" if state == "open" else "❌"
        lines.append(
            f'<div align="left">\n'
            f'  <p>{state_emoji} <a href="{item["html_url"]}"><strong>{title}</strong></a><br/>\n'
            f'  <sub>in <a href="{repo_html_url}">{repo_name}</a></sub></p>\n'
            f"</div>"
        )

    if not lines:
        return "<p><em>No recent pull requests - time to contribute! 🔀</em></p>"
    return "\n".join(lines)


def build_recent_stars(username: str, token: str) -> str:
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
            f'<div align="left">\n'
            f'  <p>⭐ <a href="{star.get("html_url")}"><strong>{repo_name}</strong></a> {stars_badge}<br/>\n'
            f"  <sub>{desc}</sub></p>\n"
            f"</div>"
        )
    return "\n".join(lines)


def main() -> int:
    username = os.getenv("GH_USERNAME") or os.getenv("GITHUB_ACTOR", "")
    token = os.getenv("GH_PAT") or os.getenv("GITHUB_TOKEN", "")

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

    full_name = user_data.get("name") or username
    display_name = full_name.split()[0]

    replacements = {
        "{{USER_NAME}}": display_name,
        "{{USER_LOGIN}}": username,
        "{{TOP_LANGUAGES}}": build_top_languages(username, token),
        "{{SOCIAL_LINKS}}": build_social_links(username, user_data, token),
        "{{WORKING_ON}}": build_active_projects(username, token),
        "{{LATEST_PROJECTS}}": build_latest_repos(username, token),
        "{{RECENT_PRS}}": build_recent_prs(username, token),
        "{{RECENT_STARS}}": build_recent_stars(username, token),
    }

    try:
        with open(template_path, encoding="utf-8") as f:
            content = f.read()
        for key, value in replacements.items():
            content = content.replace(key, value)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Successfully generated {output_path}")
        return 0
    except OSError as e:
        print(f"Error writing README: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
