#!/usr/bin/env python3
import os
import sys
import json
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone
from typing import Any

GITHUB_API = "https://api.github.com"
RECENT_LIMIT = 5


def env(name: str, default: str = "") -> str:
    return os.getenv(name) or default


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value or not value.strip().isdigit():
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}

def gh_get(path: str, token: str) -> Any:
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
    return text if len(text) <= max_len else text[: max_len - 3] + "..."


def build_working_on(events: Any, username: str, token: str, limit: int = 4) -> str:
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
            desc = limit_text(data.get("description") or "No description available", 80)
            lines.append(f"* [{name}](https://github.com/{repo}) - {desc}")
        except Exception:
            lines.append(f"* [{name}](https://github.com/{repo})")
    
    return "\n".join(lines)


def build_latest_projects(repos: Any, limit: int = 3) -> str:
    items = [r for r in repos if not r.get("fork") and r.get("size", 0) > 0][:limit]
    return "\n".join(
        f"* [**{r['name']}**]({r['html_url']}) - {r.get('description') or 'No description available'}"
        for r in items
    )


def build_recent_prs(prs_payload: Any) -> str:
    items = (prs_payload or {}).get("items", [])
    if not items:
        return "* No recent pull requests - time to contribute! 🔀"
    
    lines = []
    for item in items[:RECENT_LIMIT]:
        title = limit_text(item.get("title", "Untitled"), 60)
        api_repo_url = item.get("repository_url", "")
        repo_name = api_repo_url.split("/")[-1] if api_repo_url else "repo"
        # Convert API repo URL to github.com URL for nicer display links
        repo_html_url = (
            api_repo_url.replace("api.github.com/repos", "github.com") if api_repo_url else ""
        )
        lines.append(f"* [{title}]({item.get('html_url')}) on [{repo_name}]({repo_html_url})")
    
    return "\n".join(lines)


def build_recent_stars(stars: Any) -> str:
    if not stars:
        return "* No recent stars - discover some awesome repos! ⭐"
    
    lines = []
    for star in stars[:RECENT_LIMIT]:
        desc = limit_text(star.get("description") or "No description available", 80)
        owner = star.get("owner", {}).get("login", "owner")
        name = star.get("name", "repo")
        lines.append(f"* [{owner}/{name}]({star.get('html_url')}) - {desc}")
    
    return "\n".join(lines)


def build_social_links(username: str, user: Any, token: str) -> str:
    website = (user.get("blog") or "").strip()
    # Normalize website to include scheme for correct linking in README
    if website and not (website.startswith("http://") or website.startswith("https://")):
        website = f"https://{website}"
    twitter = (user.get("twitter_username") or "").strip()
    show_github = env_bool("SHOW_GITHUB_LINK", False)

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
        links.append(
            f'<a href="{website}" target="_blank" rel="noopener noreferrer">'
            f'<img alt="{alt}" src="https://cdn.simpleicons.org/{slug}/{color}" width="28" height="28" />'
            "</a>"
        )

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
            links.append(
                f'<a href="{url}" target="_blank" rel="noopener noreferrer">'
                f'<img alt="{alt}" src="https://cdn.simpleicons.org/{slug}/{color}" width="28" height="28" />'
                "</a>"
            )

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
        links.append(
            f'<a href="mailto:{email}" target="_blank" rel="noopener noreferrer">'
            f'<img alt="{alt}" src="https://cdn.simpleicons.org/{slug}/{color}" width="28" height="28" />'
            "</a>"
        )

    if show_github:
        slug, color, alt = icons["github"]
        links.append(
            f'<a href="https://github.com/{username}" target="_blank" rel="noopener noreferrer">'
            f'<img alt="{alt}" src="https://cdn.simpleicons.org/{slug}/{color}" width="28" height="28" />'
            "</a>"
        )

    return f'<p align="left">{" ".join(links)}</p>' if links else ""


def generate_readme(template_path: str, output_path: str, username: str, token: str) -> None:
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
    prs_days = env_int("PRS_DAYS", 30)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=prs_days)).strftime("%Y-%m-%d")
    prs = gh_get(
        f"/search/issues?q=author:{username}+type:pr+created:>={cutoff}&sort=created&order=desc&per_page={RECENT_LIMIT}",
        token,
    )

    # Extract user data
    user_name = user.get("name") or env("FALLBACK_NAME", username)
    user_bio = user.get("bio") or env("FALLBACK_BIO", "Passionate developer building amazing projects")
    repo_count = str(user.get("public_repos", "0"))
    location = user.get("location") or env("FALLBACK_LOCATION", "📍 Unknown location")
    coding_since_year = (user.get("created_at") or "").split("-")[0] or "Unknown"
    coding_since = f"💻 Coding since {coding_since_year}"

    # Build sections
    social_links = build_social_links(username, user, token)
    working_on = build_working_on(events, username, token, env_int("WORKING_ON_LIMIT", 4))
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
