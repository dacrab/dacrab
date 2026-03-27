#!/usr/bin/env python3
"""Generate README.md from README.gtpl using GitHub API data."""
import json, os, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

API = "https://api.github.com"
ICONS = "https://skillicons.dev/icons"

LANG_ICONS = {
    "C": "c", "C#": "cs", "C++": "cpp", "CSS": "css", "Dart": "dart",
    "Go": "go", "HTML": "html", "Java": "java", "JavaScript": "javascript",
    "Kotlin": "kotlin", "Lua": "lua", "PHP": "php", "Python": "python",
    "Ruby": "ruby", "Rust": "rust", "Sass": "sass", "SCSS": "sass",
    "ShaderLab": "unity", "Shell": "bash", "Svelte": "svelte",
    "Swift": "swift", "TypeScript": "ts", "Vue": "vue",
}


def fetch(path: str, token: str):
    url = path if path.startswith("http") else f"{API}{path}"
    req = Request(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "readme-gen",
    })
    try:
        with urlopen(req, timeout=30) as r:
            return json.load(r)
    except (URLError, json.JSONDecodeError) as e:
        print(f"Warning: {url} — {e}", file=sys.stderr)
        return None


def cut(text: str, n: int) -> str:
    return text if len(text) <= n else text[:n - 3] + "..."


def badge(label: str, color: str) -> str:
    return f"![](https://img.shields.io/badge/{label.replace(' ', '%20').replace('-', '--')}-{color}?style=flat-square&labelColor=0d0d1a)"


def card(name: str, url: str, desc: str, lang: str = "", stars: int = 0, lang_color: str = "5865F2") -> str:
    b = (f"{badge(f'-{lang}', lang_color)} " if lang else "") + \
        (f"{badge(f'stars-{stars:,}', '555')} " if stars else "")
    return f'<div align="left">\n\n**[{name}]({url})**&nbsp; {b}\n\n{desc}\n\n</div>'


# --- Section builders ---

def top_languages(username: str, token: str) -> str:
    repos, page = [], 1
    while len(repos) < 200:
        batch = fetch(f"/users/{username}/repos?sort=updated&per_page=100&page={page}", token)
        if not batch: break
        repos += [r for r in batch if not r.get("fork") and not r.get("private")]
        if len(batch) < 100: break
        page += 1

    counts: dict[str, int] = {}
    for repo in repos[:50]:
        for lang, n in (fetch(f"/repos/{repo['full_name']}/languages", token) or {}).items():
            counts[lang] = counts.get(lang, 0) + n

    icons = [LANG_ICONS[l] for l, _ in sorted(counts.items(), key=lambda x: -x[1]) if l in LANG_ICONS][:8]
    return f'<div align="center"><img src="{ICONS}?i={",".join(icons)}" alt="Languages" /></div>' if icons \
        else "<p>No language data.</p>"



def active_projects(username: str, token: str) -> str:
    seen, cards = set(), []
    for event in fetch(f"/users/{username}/events?per_page=50", token) or []:
        if len(cards) >= 4: break
        if event.get("type") not in {"PushEvent", "PullRequestEvent", "CreateEvent"}: continue
        name = event.get("repo", {}).get("name", "")
        if not name or name in seen: continue
        seen.add(name)
        if (r := fetch(f"/repos/{name}", token)) and not r.get("private"):
            cards.append(card(name.split("/")[-1], r["html_url"],
                              cut(r.get("description") or "No description", 80),
                              r.get("language", ""), r.get("stargazers_count", 0)))
    return "\n\n".join(cards) or "<p><em>No active projects.</em></p>"


def latest_repos(username: str, token: str) -> str:
    repos = fetch(f"/users/{username}/repos?sort=created&direction=desc&per_page=10", token) or []
    items = [r for r in repos if not r.get("fork") and not r.get("private")][:3]
    return "\n\n".join(card(r["name"], r["html_url"],
                            cut(r.get("description") or "No description", 100),
                            r.get("language", ""), r.get("stargazers_count", 0))
                       for r in items) or "<p><em>No repositories found.</em></p>"


def recent_prs(username: str, token: str) -> str:
    since = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    data = fetch(f"/search/issues?q=author:{username}+type:pr+created:>={since}&sort=created&order=desc&per_page=5", token)
    items = (data or {}).get("items", [])

    lines = []
    for item in items:
        parts = item.get("repository_url", "").rstrip("/").rsplit("/", 2)
        if len(parts) < 3: continue
        repo = f"{parts[-2]}/{parts[-1]}"
        is_merged = bool(item.get("pull_request", {}).get("merged_at"))
        state = item.get("state", "open")
        b = badge("merged", "5865F2") if is_merged else badge("open", "238636") if state == "open" else badge("closed", "555")
        lines.append(
            f'<div align="left">\n\n'
            f'{b} **[{cut(item.get("title", "Untitled"), 60)}]({item["html_url"]})**\\\n'
            f'<sub>[{repo}](https://github.com/{repo})</sub>\n\n</div>'
        )
    return "\n\n".join(lines) or "<p><em>No recent pull requests.</em></p>"


def recent_stars(username: str, token: str) -> str:
    items = fetch(f"/users/{username}/starred?sort=created&direction=desc&per_page=5", token) or []
    return "\n\n".join(card(s.get("full_name", "?"), s.get("html_url", ""),
                            cut(s.get("description") or "No description", 80),
                            s.get("language", ""), s.get("stargazers_count", 0), "555")
                       for s in items) or "<p><em>No recent stars.</em></p>"


# --- Main ---

def main() -> int:
    username = os.getenv("GH_USERNAME") or os.getenv("GITHUB_ACTOR", "")
    token    = os.getenv("GH_PAT") or os.getenv("GITHUB_TOKEN", "")

    if not username or not token:
        print("Error: GH_USERNAME and GH_PAT/GITHUB_TOKEN required.", file=sys.stderr)
        return 1

    root = Path(__file__).parent.parent
    tpl  = root / "README.gtpl"
    out  = root / "README.md"

    if not tpl.exists():
        print(f"Error: {tpl} not found.", file=sys.stderr)
        return 1

    user = fetch(f"/users/{username}", token)
    if not user:
        print("Error: Could not fetch user data.", file=sys.stderr)
        return 1

    print(f"Generating README for {username}...")

    name = (user.get("name") or username).split()[0]
    content = tpl.read_text(encoding="utf-8")
    for key, val in {
        "{{USER_NAME}}":       name,
        "{{USER_LOGIN}}":      username,
        "{{TOP_LANGUAGES}}":   top_languages(username, token),
        "{{WORKING_ON}}":      active_projects(username, token),
        "{{LATEST_PROJECTS}}": latest_repos(username, token),
        "{{RECENT_PRS}}":      recent_prs(username, token),
        "{{RECENT_STARS}}":    recent_stars(username, token),
    }.items():
        content = content.replace(key, val)

    try:
        out.write_text(content, encoding="utf-8")
        print(f"Done → {out}")
        return 0
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
