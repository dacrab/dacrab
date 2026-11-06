#!/usr/bin/env python3
"""Generate README.md from README.gtpl using GitHub API data."""

import hashlib
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape as escape_xml

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

# The language bar keeps the chart readable by folding the long tail into one
# neutral slice.
LANGUAGE_BAR_LIMIT = 5
OTHER_LANGUAGE = "Other"

BAR_THEMES = {
    False: {
        "text": "#1B1A17",
        "muted": "#7B7569",
        "track": "#E4DCCD",
        "colors": (
            "#A07D48", "#8D8475", "#C6BCAB", "#6C665B", "#A9A090", "#D6CEC0",
        ),
    },
    True: {
        "text": "#F2EDE3",
        "muted": "#8B8478",
        "track": "#2A2824",
        "colors": (
            "#C9A66B", "#A9A090", "#6F685D", "#C2B9A9", "#8A8276", "#5A564D",
        ),
    },
}

FONT_MONO = (
    "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
)

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


def _percentages(sizes: list[int]) -> list[int]:
    """Split sizes into whole percentages that always add up to 100."""
    total = sum(sizes)
    if total <= 0:
        return [0] * len(sizes)

    raw = [size * 100 / total for size in sizes]
    percentages = [int(value) for value in raw]
    leftover = 100 - sum(percentages)
    ranked = sorted(
        range(len(sizes)),
        key=lambda index: (-(raw[index] - percentages[index]), -sizes[index], index),
    )
    for index in ranked[:leftover]:
        percentages[index] += 1

    # A visible slice should never read as zero percent in the legend.
    for index, percentage in enumerate(percentages):
        if percentage:
            continue
        donor = max(range(len(percentages)), key=lambda i: percentages[i])
        if percentages[donor] > 1:
            percentages[donor] -= 1
            percentages[index] = 1
    return percentages


def language_distribution(
    counts: Counter[str],
) -> list[tuple[str, int, int]]:
    """Return the largest languages plus an Other slice, with percentages."""
    ranked = sorted(
        ((name, size) for name, size in counts.items() if size > 0),
        key=lambda item: (-item[1], item[0]),
    )
    if not ranked:
        return []

    if len(ranked) > LANGUAGE_BAR_LIMIT:
        rest = sum(size for _, size in ranked[LANGUAGE_BAR_LIMIT:])
        ranked = ranked[:LANGUAGE_BAR_LIMIT] + [(OTHER_LANGUAGE, rest)]

    percentages = _percentages([size for _, size in ranked])
    return [
        (name, size, percentage)
        for (name, size), percentage in zip(ranked, percentages)
    ]


def describe_language_mix(slices: list[tuple[str, int, int]]) -> str:
    if not slices:
        return "No language data available."
    details = ", ".join(f"{name} {percentage}%" for name, _, percentage in slices)
    return f"Language mix: {details}."


def render_language_bar(counts: Counter[str], *, dark: bool = False) -> str:
    """Render a compact, theme-aware SVG bar for the public language mix."""
    theme = BAR_THEMES[dark]
    track = theme["track"]
    text_color = theme["text"]
    muted = theme["muted"]
    colors = theme["colors"]
    slices = language_distribution(counts)
    description = escape_xml(describe_language_mix(slices))
    common = (
        'xmlns="http://www.w3.org/2000/svg" width="1200" height="64" '
        'viewBox="0 0 1200 64" role="img" aria-labelledby="bar-title bar-desc"'
    )
    title = '<title id="bar-title">Language mix</title>'
    desc = f'<desc id="bar-desc">{description}</desc>'

    if not slices:
        return (
            f"<svg {common}>"
            f"{title}{desc}"
            '<rect x="0" y="4" width="1200" height="16" rx="8" '
            f'fill="{track}"/>'
            f'<text x="0" y="48" font-family="{FONT_MONO}" font-size="15" '
            f'letter-spacing="1.4" fill="{muted}">'
            "LANGUAGE DATA UNAVAILABLE</text>"
            "</svg>"
        )

    gap = 3
    available = 1200 - gap * (len(slices) - 1)
    bar = [
        '<rect x="0" y="4" width="1200" height="16" rx="8" '
        f'fill="{track}"/>'
    ]
    legend = []
    x = 0.0
    for index, (name, _, percentage) in enumerate(slices):
        width = available * percentage / 100
        if index:
            x += gap
        color = colors[index % len(colors)]
        bar.append(
            f'<rect x="{x:.2f}" y="4" width="{width:.2f}" height="16" '
            f'fill="{color}"/>'
        )

        label_x = index * (1200 / len(slices))
        legend.append(
            f'<rect x="{label_x:.2f}" y="37" width="8" height="8" rx="1.5" '
            f'fill="{color}"/>'
            f'<text x="{label_x + 14:.2f}" y="48" font-family="{FONT_MONO}" '
            f'font-size="15" fill="{text_color}">{escape_xml(name)} '
            f'<tspan fill="{muted}">{percentage}%</tspan></text>'
        )
        x += width

    return (
        f"<svg {common}>"
        f"{title}{desc}"
        '<defs><clipPath id="bar-clip">'
        '<rect x="0" y="4" width="1200" height="16" rx="8"/>'
        "</clipPath></defs>"
        f'<g clip-path="url(#bar-clip)">{"".join(bar)}</g>'
        f'{"".join(legend)}'
        "</svg>"
    )


def render_featured_table(repos: list[dict]) -> str:
    if not repos:
        return "_No projects to show._"

    rows = [
        "| Project | About |",
        "| :--- | :--- |",
    ]
    for repo in repos:
        description = truncate(repo.get("description") or "No description", 110)
        meta = [
            part
            for part in (
                repo.get("language"),
                f"★ {repo['stargazers_count']}" if repo.get("stargazers_count") else "",
            )
            if part
        ]
        label = f"<br><sub>{' · '.join(escape_xml(part) for part in meta)}</sub>" if meta else ""
        rows.append(
            f"| **[{repo.get('name', '?')}]({repo.get('html_url', '')})**{label} "
            f"| {escape_markdown(description)} |"
        )
    return "\n".join(rows)


def render_project_list(repos: list[dict]) -> str:
    if not repos:
        return "_No recent projects._"

    lines = []
    for repo in repos:
        description = truncate(repo.get("description") or "No description", 180)
        language = repo.get("language")
        meta = f" <sub>{escape_xml(language)}</sub>" if language else ""
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
        meta = f"<sub>{status} · {escape_xml(repo)}</sub>"
        lines.append(f"- [**{title}**]({item.get('html_url', '')}) — {meta}")
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

    stack_light = render_language_bar(languages)
    stack_dark = render_language_bar(languages, dark=True)
    stack_version = hashlib.sha256(
        f"{stack_light}{stack_dark}".encode("utf-8")
    ).hexdigest()[:8]
    language_alt = escape_xml(
        describe_language_mix(language_distribution(languages))
    )

    sections = {
        "{{USER_NAME}}": (user.get("name") or username).split()[0],
        "{{TOP_LANGUAGES}}": format_languages(languages),
        "{{FEATURED_WORK}}": render_featured_table(active),
        "{{RECENT_PRS}}": render_pull_requests(pulls),
        "{{LATEST_PROJECTS}}": render_project_list(latest),
        "{{LANGUAGE_ALT}}": language_alt,
        "{{STACK_VERSION}}": stack_version,
    }

    content = template.read_text(encoding="utf-8")
    for placeholder, value in sections.items():
        content = content.replace(placeholder, value)

    assets = root / "assets"
    try:
        assets.mkdir(parents=True, exist_ok=True)
        (assets / "stack-light.svg").write_text(stack_light, encoding="utf-8")
        (assets / "stack-dark.svg").write_text(stack_dark, encoding="utf-8")
        output.write_text(content, encoding="utf-8")
    except OSError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Done → {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
