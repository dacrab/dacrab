#!/usr/bin/env python3
import os
import sys
from typing import Dict, Any
from datetime import datetime, timedelta, timezone
import requests


GITHUB_API = "https://api.github.com"


def env(name: str, default: str = "") -> str:
	value = os.getenv(name)
	return value if value is not None else default


def env_int(name: str, default: int) -> int:
	value = os.getenv(name)
	if value is None or not str(value).strip().isdigit():
		return default
	try:
		return int(str(value).strip())
	except Exception:
		return default


def gh_get(path: str, token: str) -> Any:
	headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
	resp = requests.get(f"{GITHUB_API}{path}", headers=headers, timeout=30)
	resp.raise_for_status()
	return resp.json()


# Removed icon helpers along with the tech stack section


def limit_text(text: str, max_len: int) -> str:
	if len(text) <= max_len:
		return text
	return text[: max_len - 3] + "..."


def build_working_on(events: Any, username: str, limit: int = 4) -> str:
	repos: list[str] = []
	for e in events:
		if e.get("type") in {"PushEvent", "PullRequestEvent", "CreateEvent"}:
			repo_name = e.get("repo", {}).get("name")
			if repo_name and repo_name not in repos:
				repos.append(repo_name)
				if len(repos) >= limit:
					break

	lines = []
	for full in repos:
		name = full.split("/")[-1]
		if full == f"{username}/{username}":
			desc = "My custom dynamic GitHub profile"
		elif full == f"{username}/{username}.github.io":
			desc = "Portfolio built with Astro"
		elif full.lower().endswith("/clubos"):
			desc = "POS system demo using Next.js & NeonDB"
		else:
			desc = "Recent project"
		lines.append(f"* [{name}](https://github.com/{full}) - {desc}")
	return "\n".join(lines)


def build_latest_projects(repos: Any, limit: int = 3) -> str:
    items = [r for r in repos if not r.get("fork") and r.get("size", 0) > 0]
    items = items[:limit]
	return "\n".join(
		f"* [**{r['name']}**]({r['html_url']}) - {r.get('description') or 'No description available'}"
		for r in items
	)


def build_recent_prs(prs_payload: Any) -> str:
	items = (prs_payload or {}).get("items", [])
	if not items:
		return "* No recent pull requests - time to contribute! 🔀"
	lines = []
	for it in items[:5]:
		title = limit_text(it.get("title", "Untitled"), 60)
		repo_api = it.get("repository_url", "")
		repo_name = repo_api.split("/")[-1] if repo_api else "repo"
		lines.append(f"* [{title}]({it.get('html_url')}) on [{repo_name}]({repo_api})")
	return "\n".join(lines)


def build_recent_stars(stars: Any) -> str:
	if not stars:
		return "* No recent stars - discover some awesome repos! ⭐"
	lines = []
	for s in stars[:5]:
		desc = limit_text(s.get("description") or "No description available", 80)
		owner = (s.get("owner") or {}).get("login", "owner")
		name = s.get("name", "repo")
		lines.append(f"* [{owner}/{name}]({s.get('html_url')}) - {desc}")
	return "\n".join(lines)


def build_social_links(username: str) -> str:
	website = env("WEBSITE_URL", "")
	linkedin = env("LINKEDIN_URL", "")
	instagram = env("INSTAGRAM_URL", "")
	parts: list[str] = []
	# GitHub link always available
	parts.append(
		'<a href="https://github.com/%s" target="_blank" rel="noreferrer"><picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/danielcranney/readme-generator/main/public/icons/socials/github-dark.svg" /><source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/danielcranney/readme-generator/main/public/icons/socials/github.svg" /><img src="https://raw.githubusercontent.com/danielcranney/readme-generator/main/public/icons/socials/github.svg" width="32" height="32" /></picture></a>'
		% username
	)
	if linkedin:
		parts.append(
			'<a href="%s" target="_blank" rel="noreferrer"><picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/danielcranney/readme-generator/main/public/icons/socials/linkedin-dark.svg" /><source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/danielcranney/readme-generator/main/public/icons/socials/linkedin.svg" /><img src="https://raw.githubusercontent.com/danielcranney/readme-generator/main/public/icons/socials/linkedin.svg" width="32" height="32" /></picture></a>'
			% linkedin
		)
	if instagram:
		parts.append(
			'<a href="%s" target="_blank" rel="noreferrer"><picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/danielcranney/readme-generator/main/public/icons/socials/instagram-dark.svg" /><source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/danielcranney/readme-generator/main/public/icons/socials/instagram.svg" /><img src="https://raw.githubusercontent.com/danielcranney/readme-generator/main/public/icons/socials/instagram.svg" width="32" height="32" /></picture></a>'
			% instagram
		)
	if website:
		parts.append(
			'<a href="%s" target="_blank" rel="noreferrer"><img src="https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/globe.svg" width="32" height="32" /></a>'
			% website
		)
	return '<p align="left">' + " ".join(parts) + "</p>"


# Removed tech stack section rendering per user request


def generate_readme(template_path: str, output_path: str, username: str, token: str) -> None:
	user = gh_get(f"/users/{username}", token)
	events = gh_get(f"/users/{username}/events?per_page=50", token)
	repos_newest = gh_get(f"/users/{username}/repos?sort=created&direction=desc&per_page=5", token)
	stars = gh_get(f"/users/{username}/starred?sort=created&direction=desc&per_page=5", token)
	prs_days = env_int("PRS_DAYS", 30)
	cutoff = (datetime.now(timezone.utc) - timedelta(days=prs_days)).strftime("%Y-%m-%d")
	prs = gh_get(f"/search/issues?q=author:{username}+type:pr+created:>={cutoff}&sort=created&order=desc&per_page=5", token)
	# repos_all removed since TECH_STACK is not rendered

	user_name = user.get("name") or env("FALLBACK_NAME", username)
	user_bio = user.get("bio") or env("FALLBACK_BIO", "Passionate developer building amazing projects")
	repo_count = str(user.get("public_repos", "0"))
	location = user.get("location") or env("FALLBACK_LOCATION", "📍 Unknown location")
	coding_since_year = (user.get("created_at") or "").split("-")[0] or "Unknown"
	coding_since = f"💻 Coding since {coding_since_year}"

	# Build socials dynamically (optional links come from envs)
	social_links = build_social_links(username)

	replacements = {
		"{{USERNAME}}": username,
		"{{USER_NAME}}": user_name,
		"{{USER_BIO}}": user_bio,
		"{{REPO_COUNT}}": repo_count,
		"{{LOCATION}}": location,
		"{{CODING_SINCE}}": coding_since,
		"{{SOCIAL_LINKS}}": social_links,
		"{{WORKING_ON}}": build_working_on(events, username, env_int("WORKING_ON_LIMIT", 4)),
		"{{LATEST_PROJECTS}}": build_latest_projects(repos_newest, env_int("LATEST_PROJECTS_LIMIT", 3)),
		"{{RECENT_PRS}}": build_recent_prs(prs),
		"{{RECENT_STARS}}": build_recent_stars(stars),
		# TECH_STACK removed and CONTACT_INFO unused
	}

	with open(template_path, "r", encoding="utf-8") as f:
		content = f.read()
	for placeholder, value in replacements.items():
		content = content.replace(placeholder, value)
	with open(output_path, "w", encoding="utf-8") as f:
		f.write(content)


def main() -> int:
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



