#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any
import requests

GITHUB_API = "https://api.github.com"


def env(name: str, default: str = "") -> str:
    """Get environment variable with fallback."""
    return os.getenv(name) or default


def env_int(name: str, default: int) -> int:
    """Get environment variable as integer with fallback."""
    value = os.getenv(name)
    if not value or not value.strip().isdigit():
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default


def gh_get(path: str, token: str) -> Any:
    """Make authenticated GitHub API request."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }
    resp = requests.get(f"{GITHUB_API}{path}", headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def limit_text(text: str, max_len: int) -> str:
    """Truncate text to max length with ellipsis."""
    return text if len(text) <= max_len else text[:max_len-3] + "..."


def build_working_on(events: Any, username: str, limit: int = 4) -> str:
    """Build working on section from recent events."""
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
        if repo == f"{username}/{username}":
            desc = "My custom dynamic GitHub profile"
        elif repo == f"{username}/{username}.github.io":
            desc = "Portfolio built with Astro"
        elif repo.lower().endswith("/clubos"):
            desc = "POS system demo using Next.js & NeonDB"
        else:
            desc = "Recent project"
        lines.append(f"* [{name}](https://github.com/{repo}) - {desc}")
    
    return "\n".join(lines)


def build_latest_projects(repos: Any, limit: int = 3) -> str:
    """Build latest projects section."""
    items = [r for r in repos if not r.get("fork") and r.get("size", 0) > 0][:limit]
    return "\n".join(
        f"* [**{r['name']}**]({r['html_url']}) - {r.get('description') or 'No description available'}"
        for r in items
    )


def build_recent_prs(prs_payload: Any) -> str:
    """Build recent pull requests section."""
    items = (prs_payload or {}).get("items", [])
    if not items:
        return "* No recent pull requests - time to contribute! 🔀"
    
    lines = []
    for item in items[:5]:
        title = limit_text(item.get("title", "Untitled"), 60)
        repo_url = item.get("repository_url", "")
        repo_name = repo_url.split("/")[-1] if repo_url else "repo"
        lines.append(f"* [{title}]({item.get('html_url')}) on [{repo_name}]({repo_url})")
    
    return "\n".join(lines)


def build_recent_stars(stars: Any) -> str:
    """Build recent stars section."""
    if not stars:
        return "* No recent stars - discover some awesome repos! ⭐"
    
    lines = []
    for star in stars[:5]:
        desc = limit_text(star.get("description") or "No description available", 80)
        owner = star.get("owner", {}).get("login", "owner")
        name = star.get("name", "repo")
        lines.append(f"* [{owner}/{name}]({star.get('html_url')}) - {desc}")
    
    return "\n".join(lines)


def build_social_links(username: str, user: Any) -> str:
    """Build social media links section."""
    website = (user.get("blog") or "").strip()
    # Normalize website to include scheme for correct linking in README
    if website and not (website.startswith("http://") or website.startswith("https://")):
        website = f"https://{website}"
    twitter = (user.get("twitter_username") or "").strip()
    
    links = [
        f'<a href="https://github.com/{username}" target="_blank" rel="noopener noreferrer">'
        '<img alt="GitHub" src="https://cdn.simpleicons.org/github/181717" width="28" height="28" />'
        '</a>'
    ]
    
    if twitter:
        links.append(
            f'<a href="https://twitter.com/{twitter}" target="_blank" rel="noopener noreferrer">'
            '<img alt="Twitter" src="https://cdn.simpleicons.org/twitter/1DA1F2" width="28" height="28" />'
            '</a>'
        )
    
    if website:
        links.append(
            f'<a href="{website}" target="_blank" rel="noopener noreferrer">'
            '<img alt="Website" src="https://cdn.simpleicons.org/globe/0EA5E9" width="28" height="28" />'
            '</a>'
        )
    
    return f'<p align="left">{" ".join(links)}</p>'


def generate_readme(template_path: str, output_path: str, username: str, token: str) -> None:
    """Generate README from template with GitHub data."""
    # Fetch GitHub data
    user = gh_get(f"/users/{username}", token)
    events = gh_get(f"/users/{username}/events?per_page=50", token)
    repos_newest = gh_get(f"/users/{username}/repos?sort=created&direction=desc&per_page=5", token)
    stars = gh_get(f"/users/{username}/starred?sort=created&direction=desc&per_page=5", token)
    
    # Calculate PR cutoff date
    prs_days = env_int("PRS_DAYS", 30)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=prs_days)).strftime("%Y-%m-%d")
    prs = gh_get(f"/search/issues?q=author:{username}+type:pr+created:>={cutoff}&sort=created&order=desc&per_page=5", token)

    # Extract user data
    user_name = user.get("name") or env("FALLBACK_NAME", username)
    user_bio = user.get("bio") or env("FALLBACK_BIO", "Passionate developer building amazing projects")
    repo_count = str(user.get("public_repos", "0"))
    location = user.get("location") or env("FALLBACK_LOCATION", "📍 Unknown location")
    coding_since_year = (user.get("created_at") or "").split("-")[0] or "Unknown"
    coding_since = f"💻 Coding since {coding_since_year}"

    # Build sections
    social_links = build_social_links(username, user)
    working_on = build_working_on(events, username, env_int("WORKING_ON_LIMIT", 4))
    latest_projects = build_latest_projects(repos_newest, env_int("LATEST_PROJECTS_LIMIT", 3))
    recent_prs = build_recent_prs(prs)
    recent_stars = build_recent_stars(stars)

    # Template replacements
    replacements = {
        "{{USERNAME}}": username,
        "{{USER_NAME}}": user_name,
        "{{USER_BIO}}": user_bio,
        "{{REPO_COUNT}}": repo_count,
        "{{LOCATION}}": location,
        "{{CODING_SINCE}}": coding_since,
        "{{SOCIAL_LINKS}}": social_links,
        "{{WORKING_ON}}": working_on,
        "{{LATEST_PROJECTS}}": latest_projects,
        "{{RECENT_PRS}}": recent_prs,
        "{{RECENT_STARS}}": recent_stars,
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
    username = env("GH_USERNAME", "dacrab")
    token = env("GH_PAT") or env("GITHUB_TOKEN")
    
    if not token:
        print("Missing GitHub token in GH_PAT or GITHUB_TOKEN", file=sys.stderr)
        return 2
    
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(root, "README.gtpl")
    output_path = os.path.join(root, "README.md")
    
    generate_readme(template_path, output_path, username, token)
    return 0


if __name__ == "__main__":
    sys.exit(main())
