import sys
import unittest
import xml.etree.ElementTree as ET
from collections import Counter
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import generate_readme as gen  # noqa: E402


class RenderingTests(unittest.TestCase):
    def test_truncate(self) -> None:
        self.assertEqual(gen.truncate("short", 10), "short")
        self.assertEqual(gen.truncate("abcdefghijkl", 10), "abcdefghi…")
        self.assertEqual(gen.truncate("one two three four", 10), "one two…")
        self.assertEqual(gen.truncate("  extra \n whitespace ", 30), "extra whitespace")

    def test_escape_markdown(self) -> None:
        self.assertEqual(gen.escape_markdown("a | b"), "a \\| b")
        self.assertEqual(
            gen.escape_markdown("*star* [link] `code`"),
            "\\*star\\* \\[link\\] \\`code\\`",
        )

    def test_format_languages(self) -> None:
        self.assertEqual(gen.format_languages(Counter()), "a range of languages")
        self.assertEqual(gen.format_languages(Counter({"Go": 10})), "Go")
        self.assertEqual(
            gen.format_languages(Counter({"Go": 10, "TypeScript": 5})),
            "Go and TypeScript",
        )
        self.assertEqual(
            gen.format_languages(
                Counter({"Go": 10, "TypeScript": 5, "Rust": 4, "C#": 3})
            ),
            "Go, TypeScript, Rust, and C#",
        )

    def test_format_languages_skips_markup_and_shell(self) -> None:
        counts = Counter({"CSS": 100, "Shell": 80, "Go": 10})
        self.assertEqual(gen.format_languages(counts), "Go")

    def test_percentages_sum_to_100(self) -> None:
        self.assertEqual(gen._percentages([50, 30, 20]), [50, 30, 20])
        self.assertEqual(gen._percentages([0, 0]), [0, 0])
        self.assertEqual(sum(gen._percentages([100, 1, 1])), 100)

    def test_language_distribution_folds_the_tail_into_other(self) -> None:
        counts = Counter(
            {
                "TypeScript": 60,
                "Kotlin": 20,
                "Go": 10,
                "C#": 5,
                "Java": 3,
                "Rust": 2,
            }
        )
        slices = gen.language_distribution(counts)

        self.assertEqual(
            [name for name, _, _ in slices],
            ["TypeScript", "Kotlin", "Go", "C#", "Java", "Other"],
        )
        self.assertEqual(slices[-1][1], 2)
        self.assertEqual(sum(percentage for _, _, percentage in slices), 100)

    def test_language_distribution_empty(self) -> None:
        self.assertEqual(gen.language_distribution(Counter()), [])

    def test_describe_language_mix(self) -> None:
        slices = [("Go", 60, 60), ("Rust", 40, 40)]
        self.assertEqual(
            gen.describe_language_mix(slices),
            "Language mix: Go 60%, Rust 40%.",
        )
        self.assertEqual(
            gen.describe_language_mix([]),
            "No language data available.",
        )

    def test_render_language_bar_light_and_dark(self) -> None:
        counts = Counter({"TypeScript": 60, "Go": 40})
        light = gen.render_language_bar(counts)
        dark = gen.render_language_bar(counts, dark=True)

        self.assertIn('fill="#A07D48"', light)
        self.assertIn('fill="#C9A66B"', dark)
        self.assertIn("TypeScript", light)
        self.assertIn("60%", light)
        self.assertEqual(ET.fromstring(light).tag, "{http://www.w3.org/2000/svg}svg")
        self.assertEqual(ET.fromstring(dark).tag, "{http://www.w3.org/2000/svg}svg")
        self.assertNotEqual(light, dark)

    def test_render_language_bar_empty(self) -> None:
        svg = gen.render_language_bar(Counter())
        self.assertIn("LANGUAGE DATA UNAVAILABLE", svg)
        ET.fromstring(svg)

    def test_render_language_bar_escapes_names(self) -> None:
        svg = gen.render_language_bar(Counter({"A&B": 1}))
        self.assertIn("A&amp;B", svg)
        ET.fromstring(svg)

    def test_render_featured_table(self) -> None:
        repos = [
            {
                "name": "clubOS",
                "html_url": "https://github.com/dacrab/clubOS",
                "description": "A POS for clubs | venues",
                "language": "TypeScript",
            }
        ]
        table = gen.render_featured_table(repos)
        self.assertIn("| Project | About |", table)
        self.assertIn(
            "**[clubOS](https://github.com/dacrab/clubOS)**"
            "<br><sub>TypeScript</sub>",
            table,
        )
        self.assertIn("A POS for clubs \\| venues", table)

    def test_render_featured_table_truncates(self) -> None:
        repos = [
            {
                "name": "long",
                "html_url": "u",
                "description": "word " * 40,
                "language": "Go",
            }
        ]
        self.assertIn("…", gen.render_featured_table(repos))

    def test_render_featured_table_empty(self) -> None:
        self.assertEqual(gen.render_featured_table([]), "_No projects to show._")

    def test_render_project_list(self) -> None:
        repos = [
            {
                "name": "pardus",
                "html_url": "https://github.com/dacrab/pardus",
                "description": "A landing page",
                "language": "CSS",
            }
        ]
        self.assertEqual(
            gen.render_project_list(repos),
            "- [pardus](https://github.com/dacrab/pardus) — A landing page "
            "<sub>CSS</sub>",
        )
        self.assertEqual(gen.render_project_list([]), "_No recent projects._")

    def test_render_pull_requests_statuses(self) -> None:
        items = [
            {
                "repository_url": "https://api.github.com/repos/a/b",
                "html_url": "https://github.com/a/b/pull/1",
                "title": "Merged PR",
                "state": "closed",
                "pull_request": {"merged_at": "2026-01-01"},
            },
            {
                "repository_url": "https://api.github.com/repos/a/b",
                "html_url": "https://github.com/a/b/pull/2",
                "title": "Open PR",
                "state": "open",
                "pull_request": {},
            },
            {
                "repository_url": "https://api.github.com/repos/a/b",
                "html_url": "https://github.com/a/b/pull/3",
                "title": "Closed PR",
                "state": "closed",
                "pull_request": {},
            },
        ]
        html = gen.render_pull_requests(items)
        self.assertIn("— <sub>Merged · a/b</sub>", html)
        self.assertIn("— <sub>Open · a/b</sub>", html)
        self.assertIn("— <sub>Closed · a/b</sub>", html)

    def test_render_pull_requests_skips_malformed_repos(self) -> None:
        items = [{"repository_url": "", "html_url": "x", "title": "Broken"}]
        self.assertEqual(
            gen.render_pull_requests(items),
            "_No recent pull requests._",
        )


class FetchingTests(unittest.TestCase):
    def test_is_public_repo(self) -> None:
        self.assertFalse(gen.is_public_repo(None))
        self.assertFalse(gen.is_public_repo({}))
        self.assertTrue(gen.is_public_repo({"name": "repo"}))
        self.assertFalse(gen.is_public_repo({"name": "repo", "private": True}))
        self.assertFalse(gen.is_public_repo({"name": "repo", "archived": True}))
        self.assertFalse(gen.is_public_repo({"name": "repo", "fork": True}))

    def test_fetch_top_languages_sums_sizes(self) -> None:
        payload = {
            "data": {
                "user": {
                    "repositories": {
                        "nodes": [
                            {
                                "languages": {
                                    "edges": [
                                        {"size": 100, "node": {"name": "Go"}},
                                        {"size": 50, "node": {"name": "C#"}},
                                    ]
                                }
                            },
                            {
                                "languages": {
                                    "edges": [{"size": 25, "node": {"name": "Go"}}]
                                }
                            },
                        ]
                    }
                }
            }
        }
        with mock.patch.object(
            gen, "request_json", return_value=payload
        ) as request:
            counts = gen.fetch_top_languages("dacrab", "token")

        self.assertEqual(counts["Go"], 125)
        self.assertEqual(counts["C#"], 50)
        args = request.call_args
        self.assertEqual(args.args[0], gen.GRAPHQL_API)
        self.assertEqual(args.args[2]["variables"], {"login": "dacrab"})

    def test_fetch_top_languages_handles_graphql_errors(self) -> None:
        with mock.patch.object(
            gen, "request_json", return_value={"errors": [{"message": "nope"}]}
        ), redirect_stderr(StringIO()):
            counts = gen.fetch_top_languages("dacrab", "token")
        self.assertEqual(counts, Counter())

    def test_fetch_active_repos_dedupes_and_skips(self) -> None:
        def fake_fetch(path: str, token: str):
            if path == "/repos/u/clubOS":
                return {
                    "name": "clubOS",
                    "html_url": "https://github.com/u/clubOS",
                    "language": "TypeScript",
                }
            if path == "/users/u/events?per_page=50":
                return [
                    {"type": "PushEvent", "repo": {"name": "u/clubOS"}},
                    {"type": "WatchEvent", "repo": {"name": "u/ignored"}},
                    {"type": "PushEvent", "repo": {"name": "u/new"}},
                    {"type": "PushEvent", "repo": {"name": "u/new"}},
                ]
            if path == "/repos/u/new":
                return {
                    "name": "new",
                    "html_url": "https://github.com/u/new",
                    "language": "Go",
                }
            return None

        with mock.patch.object(gen, "FEATURED", ["clubOS", "missing"]), \
                mock.patch.object(gen, "fetch", side_effect=fake_fetch) as fetch:
            repos = gen.fetch_active_repos("u", "token")

        self.assertEqual([repo["name"] for repo in repos], ["clubOS", "new"])
        self.assertEqual(fetch.call_count, 4)

    def test_fetch_active_repos_stops_at_limit(self) -> None:
        def fake_fetch(path: str, token: str):
            if path == "/repos/u/clubOS":
                return {
                    "name": "clubOS",
                    "html_url": "https://github.com/u/clubOS",
                }
            return None

        with mock.patch.object(gen, "FEATURED", ["clubOS", "never-fetched"]), \
                mock.patch.object(gen, "fetch", side_effect=fake_fetch) as fetch:
            repos = gen.fetch_active_repos("u", "token", limit=1)

        self.assertEqual([repo["name"] for repo in repos], ["clubOS"])
        self.assertEqual(fetch.call_count, 1)

    def test_fetch_latest_repos_filters_and_limits(self) -> None:
        repos = [
            {"name": "a", "language": "Go", "fork": False},
            {"name": "fork", "language": "Go", "fork": True},
            {"name": "private", "language": "Go", "private": True},
            {"name": "archived", "language": "Go", "archived": True},
            {"name": "no-language"},
            {"name": "featured", "language": "Go"},
            {"name": "b", "language": "Rust"},
            {"name": "c", "language": "C"},
            {"name": "d", "language": "C++"},
        ]
        with mock.patch.object(gen, "FEATURED", ["featured"]), \
                mock.patch.object(gen, "fetch", return_value=repos):
            result = gen.fetch_latest_repos("u", "token")

        self.assertEqual([repo["name"] for repo in result], ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
