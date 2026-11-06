#!/usr/bin/env python3
"""Generate README.md from README.gtpl using GitHub API data."""

import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

API = "https://api.github.com"
GRAPHQL_API = f"{API}/graphql"

# Curated showcase order. Repos that are private, archived, forked or missing
# are skipped, so the section can safely fall back to recent activity.
FEATURED = [
    "clubOS",
    "telestash",
    "craftops",
    "topos",
    "reddit-gallery-dl",
    "dragon-blaze",
]

# Markup and shell languages say little about the stack, so leave them out of
# the intro sentence.
DISPLAY_LANGUAGES = {
    "C", "C#", "C++", "Dart", "Go", "Java", "JavaScript", "Kotlin", "Lua",
    "PHP", "Python", "Ruby", "Rust", "Svelte", "Swift", "TypeScript", "Vue",
}

ACTIVITY_EVENTS = {"PushEvent", "PullRequestEvent", "CreateEvent"}

# One GraphQL request replaces the two REST pages plus the per-repo language
# requests the previous implementation made.
LANGUAGES_QUERY = """
query TopLanguages($login: String!) {
  user(login: $login) {
    repositories(
      first: 50
      ownerAffiliations: OWNER
      privacy: PUBLIC
      isFork: false
      orderBy: {field: PUSHED_AT, direction: DESC}
    ) {
      nodes {
        languages(first: 20, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
            }
          }
        }
      }
    }
  }
}
"""


# --- GitHub API ---

def request_json(url: str, token: str, payload: dict[str, Any] | None = None) -> Any:
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "readme-gen",
    }
    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")

    request = Request(url, data=body, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        print(f"Warning: {url} — {error}", file=sys.stderr)
        return None


def fetch(path: str, token: str) -> Any:
    url = path if path.startswith("http") else f"{API}{path}"
    return request_json(url, token)


def is_public_repo(repo: dict | None) -> bool:
    return bool(repo) and not any(
        repo.get(key) for key in ("private", "archived", "fork")
    )


def fetch_top_languages(username: str, token: str) -> Counter[str]:
    data = request_json(
        GRAPHQL_API, token, {"query": LANGUAGES_QUERY, "variables": {"login": username}}
    )
    if not data:
        return Counter()
    if errors := data.get("errors"):
        print(f"Warning: GraphQL — {errors}", file=sys.stderr)
        return Counter()

    payload = data.get("data") or {}
    user = payload.get("user") or {}
    repositories = user.get("repositories") or {}
    repos = repositories.get("nodes") or []

    counts: Counter[str] = Counter()
    for repo in repos:
        for edge in (repo.get("languages") or {}).get("edges") or []:
            language = (edge.get("node") or {}).get("name")
            if language:
                counts[language] += edge.get("size", 0)
    return counts


def fetch_active_repos(username: str, token: str, limit: int = 6) -> list[dict]:
    """Return curated work first, then recently used repos, without duplicates."""
    repos: list[dict] = []
    seen: set[str] = set()

    def add(repo: dict | None) -> None:
        if not is_public_repo(repo):
            return
        name = repo.get("name")
        if not name or name in seen:
            return
        seen.add(name)
        repos.append(repo)

    for name in FEATURED:
        if len(repos) >= limit:
            break
        add(fetch(f"/repos/{username}/{name}", token))

    if len(repos) < limit:
        events = fetch(f"/users/{username}/events?per_page=50", token) or []
        for event in events:
            if len(repos) >= limit:
                break
            if event.get("type") not in ACTIVITY_EVENTS:
                continue
            full_name = (event.get("repo") or {}).get("name", "")
            if not full_name or full_name.rsplit("/", 1)[-1] in seen:
                continue
            add(fetch(f"/repos/{full_name}", token))

    return repos


def fetch_latest_repos(username: str, token: str) -> list[dict]:
    repos = fetch(
        f"/users/{username}/repos?sort=created&direction=desc&per_page=10", token
    ) or []
    # Skip forks, private, archived, language-less repos (config/asset dumps) and
    # anything already in FEATURED, so the two sections never repeat a project.
    return [
        repo
        for repo in repos
        if is_public_repo(repo)
        and repo.get("language")
        and repo.get("name") not in FEATURED
    ][:3]


def fetch_recent_prs(username: str, token: str) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    data = fetch(
        f"/search/issues?q=author:{username}+type:pr+created:>={since}"
        "&sort=created&order=desc&per_page=5",
        token,
    )
    return (data or {}).get("items", [])


# --- Rendering ---

def truncate(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    head = text[: limit - 1]
    if " " in head:
        head = head.rsplit(" ", 1)[0]
    return head.rstrip(" ,.;:") + "…"


def escape_markdown(text: str) -> str:
    for character in "\\`*_{}[]<>|":
        text = text.replace(character, f"\\{character}")
    return text


def format_languages(counts: Counter[str]) -> str:
    languages = [
        language
        for language, _ in counts.most_common()
        if language in DISPLAY_LANGUAGES
    ][:6]
    if not languages:
        return "a range of languages"
    if len(languages) == 1:
        return languages[0]
    if len(languages) == 2:
        return " and ".join(languages)
    return f"{', '.join(languages[:-1])}, and {languages[-1]}"


def render_featured_table(repos: list[dict]) -> str:
    if not repos:
        return "_No projects to show._"

    rows = [
        "| Project | Description | Language |",
        "| :--- | :--- | :--- |",
    ]
    for repo in repos:
        description = truncate(repo.get("description") or "No description", 120)
        rows.append(
            f"| [{repo.get('name', '?')}]({repo.get('html_url', '')}) "
            f"| {escape_markdown(description)} "
            f"| {escape_markdown(repo.get('language') or '—')} |"
        )
    return "\n".join(rows)


def render_project_list(repos: list[dict]) -> str:
    if not repos:
        return "_No recent projects._"

    lines = []
    for repo in repos:
        description = truncate(repo.get("description") or "No description", 180)
        language = repo.get("language")
        meta = f" ({escape_markdown(language)})" if language else ""
        lines.append(
            f"- [{repo.get('name', '?')}]({repo.get('html_url', '')}) — "
            f"{escape_markdown(description)}{meta}"
        )
    return "\n".join(lines)


def render_pull_requests(items: list[dict]) -> str:
    lines = []
    for item in items:
        repo = "/".join(item.get("repository_url", "").rsplit("/", 2)[-2:])
        if "/" not in repo:
            continue

        if (item.get("pull_request") or {}).get("merged_at"):
            status = "Merged"
        elif item.get("state") == "open":
            status = "Open"
        else:
            status = "Closed"

        title = escape_markdown(truncate(item.get("title", "Untitled"), 90))
        lines.append(
            f"- [{title}]({item.get('html_url', '')}) — {status} · `{repo}`"
        )
    return "\n".join(lines) or "_No recent pull requests._"


# --- Main ---

def main() -> int:
    username = os.getenv("GH_USERNAME") or os.getenv("GITHUB_ACTOR", "")
    token = os.getenv("GH_PAT") or os.getenv("GITHUB_TOKEN", "")

    if not username or not token:
        print("Error: GH_USERNAME and GH_PAT/GITHUB_TOKEN required.", file=sys.stderr)
        return 1

    root = Path(__file__).resolve().parent.parent
    template = root / "README.gtpl"
    output = root / "README.md"
    if not template.exists():
        print(f"Error: {template} not found.", file=sys.stderr)
        return 1

    user = fetch(f"/users/{username}", token)
    if not user:
        print("Error: Could not fetch user data.", file=sys.stderr)
        return 1

    print(f"Generating README for {username}...")
    languages = fetch_top_languages(username, token)
    active = fetch_active_repos(username, token)
    latest = fetch_latest_repos(username, token)
    pulls = fetch_recent_prs(username, token)

    sections = {
        "{{USER_NAME}}": (user.get("name") or username).split()[0],
        "{{TOP_LANGUAGES}}": format_languages(languages),
        "{{FEATURED_WORK}}": render_featured_table(active),
        "{{RECENT_PRS}}": render_pull_requests(pulls),
        "{{LATEST_PROJECTS}}": render_project_list(latest),
    }

    content = template.read_text(encoding="utf-8")
    for placeholder, value in sections.items():
        content = content.replace(placeholder, value)

    try:
        output.write_text(content, encoding="utf-8")
    except OSError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Done → {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
