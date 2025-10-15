#!/usr/bin/env python3
import os
import sys
import textwrap
from dataclasses import dataclass
from typing import Dict, Any
import re
from datetime import datetime, timedelta, timezone
import requests


GITHUB_API = "https://api.github.com"


def env(name: str, default: str = "") -> str:
	value = os.getenv(name)
	return value if value is not None else default


def gh_get(path: str, token: str) -> Any:
	headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
	resp = requests.get(f"{GITHUB_API}{path}", headers=headers, timeout=30)
	resp.raise_for_status()
	return resp.json()


def normalize_slug(name: str) -> str:
	"""Normalize language names to CDN icon slug candidates."""
	slug = name.strip().lower()
	slug = slug.replace(" ", "")
	slug = slug.replace("+", "plusplus").replace("#", "sharp")
	slug = slug.replace(".", "")
	# Special common cases for devicon/simple-icons
	if slug == "html":
		return "html5"
	if slug == "css":
		return "css3"
	if slug in {"shell", "sh"}:
		return "bash"
	if slug == "jupyternotebook":
		return "jupyter"
	return slug


def pick_first_available(url_candidates: list[str]) -> str | None:
	for url in url_candidates:
		try:
			res = requests.head(url, timeout=8)
			if res.status_code < 400:
				return url
		except Exception:
			pass
	return None


def limit_text(text: str, max_len: int) -> str:
	if len(text) <= max_len:
		return text
	return text[: max_len - 3] + "..."


def build_working_on(events: Any, username: str) -> str:
	repos: list[str] = []
	for e in events:
		if e.get("type") in {"PushEvent", "PullRequestEvent", "CreateEvent"}:
			repo_name = e.get("repo", {}).get("name")
			if repo_name and repo_name not in repos:
				repos.append(repo_name)
				if len(repos) >= 4:
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


def build_latest_projects(repos: Any) -> str:
	items = [r for r in repos if not r.get("fork") and r.get("size", 0) > 0]
	items = items[:3]
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


# Removed tech stack section rendering per user request


def generate_readme(template_path: str, output_path: str, username: str, token: str) -> None:
	user = gh_get(f"/users/{username}", token)
	events = gh_get(f"/users/{username}/events?per_page=50", token)
	repos_newest = gh_get(f"/users/{username}/repos?sort=created&direction=desc&per_page=5", token)
	stars = gh_get(f"/users/{username}/starred?sort=created&direction=desc&per_page=5", token)
	cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
	prs = gh_get(f"/search/issues?q=author:{username}+type:pr+created:>={cutoff}&sort=created&order=desc&per_page=5", token)
    # repos_all removed since TECH_STACK is not rendered

	user_name = user.get("name") or env("FALLBACK_NAME", "Vaggelis Kavouras")
	user_bio = user.get("bio") or env("FALLBACK_BIO", "Passionate developer building amazing projects")
	repo_count = str(user.get("public_repos", "23"))

	replacements = {
		"{{USERNAME}}": username,
		"{{USER_NAME}}": user_name,
		"{{USER_BIO}}": user_bio,
		"{{REPO_COUNT}}": repo_count,
		"{{SOCIAL_LINKS}}": env("SOCIAL_LINKS", ""),
		"{{WORKING_ON}}": build_working_on(events, username),
		"{{LATEST_PROJECTS}}": build_latest_projects(repos_newest),
		"{{RECENT_PRS}}": build_recent_prs(prs),
		"{{RECENT_STARS}}": build_recent_stars(stars),
        # TECH_STACK removed
        "{{CONTACT_INFO}}": env("CONTACT_INFO", ""),
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



