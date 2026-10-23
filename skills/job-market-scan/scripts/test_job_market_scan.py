#!/usr/bin/env python3
"""Unit tests for fetch_postings.py and compare_runs.py (no network)."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import fetch_postings as fp  # noqa: E402


class ToText(unittest.TestCase):
    def test_strips_tags_and_keeps_list_items(self):
        html = "&lt;h3&gt;Requirements&lt;/h3&gt;&lt;ul&gt;&lt;li&gt;Go&lt;/li&gt;&lt;li&gt;Kubernetes&lt;/li&gt;&lt;/ul&gt;"
        self.assertEqual(fp.to_text(html), "Requirements\n- Go\n- Kubernetes")

    def test_empty(self):
        self.assertEqual(fp.to_text(None), "")


class RequirementsPart(unittest.TestCase):
    def test_starts_at_requirements_heading(self):
        text = "About us\nWe build things.\nWhat you'll bring\n- Go\n- Rust"
        self.assertEqual(fp.requirements_part(text), "What you'll bring\n- Go\n- Rust")

    def test_ignores_long_lines_that_mention_skills(self):
        long_line = "We value skills " + "x" * 100
        text = f"{long_line}\nYou have\n- Go"
        self.assertEqual(fp.requirements_part(text), "You have\n- Go")

    def test_falls_back_to_capped_text(self):
        text = "a" * (fp.MAX_CHARS + 50)
        self.assertEqual(len(fp.requirements_part(text)), fp.MAX_CHARS)


class Matches(unittest.TestCase):
    cfg = {"title_keywords": ["platform"], "exclude_title_keywords": ["marketing"],
           "location_keywords": []}

    def test_keyword_match_is_case_insensitive(self):
        self.assertTrue(fp.matches("Senior Platform Engineer", "Remote", self.cfg))

    def test_exclude_wins(self):
        self.assertFalse(fp.matches("Platform Marketing Lead", "Remote", self.cfg))

    def test_no_title_keyword(self):
        self.assertFalse(fp.matches("Data Scientist", "Remote", self.cfg))

    def test_location_filter(self):
        cfg = dict(self.cfg, location_keywords=["remote"])
        self.assertTrue(fp.matches("Platform Engineer", "Remote - US", cfg))
        self.assertFalse(fp.matches("Platform Engineer", "London", cfg))


class CompareRuns(unittest.TestCase):
    def write_run(self, root: Path, name: str, postings: int, counts: dict) -> Path:
        run = root / name
        run.mkdir()
        (run / "requirements.json").write_text(json.dumps({
            "run_date": name, "postings": postings,
            "requirements": [{"name": n, "count": c, "examples": []} for n, c in counts.items()]}))
        return run

    def run_compare(self, current: Path) -> dict:
        out = subprocess.run([sys.executable, str(HERE / "compare_runs.py"), "--current", str(current)],
                             capture_output=True, text=True, check=True)
        return json.loads(out.stdout)

    def test_first_run(self):
        with tempfile.TemporaryDirectory() as d:
            cur = self.write_run(Path(d), "2026-10-01", 10, {"Go": 5})
            self.assertIsNone(self.run_compare(cur)["previous"])

    def test_previous_run_orders_numeric_suffixes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name in ["2026-10-23", "2026-10-23-2", "2026-10-23-10"]:
                self.write_run(root, name, 10, {"Go": 1})
            cur = self.write_run(root, "2026-10-23-11", 10, {"Go": 1})
            self.assertEqual(self.run_compare(cur)["previous"], "2026-10-23-10")

    def test_new_gone_rising_falling_use_shares(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.write_run(root, "2026-07-01", 10, {"Go": 2, "Java": 6, "Perl": 1, "Kubernetes": 5})
            cur = self.write_run(root, "2026-10-01", 20, {"Go": 10, "Java": 6, "Kubernetes": 10, "AI coding tools": 8})
            r = self.run_compare(cur)
            self.assertEqual(r["previous"], "2026-07-01")
            self.assertEqual(r["new"], ["AI coding tools"])
            self.assertEqual(r["gone"], ["Perl"])
            self.assertEqual(r["rising"], [{"name": "Go", "from_pct": 20, "to_pct": 50}])
            self.assertEqual(r["falling"], [{"name": "Java", "from_pct": 60, "to_pct": 30}])
            # Kubernetes is 50% in both runs despite double the count: not rising.
            self.assertNotIn("Kubernetes", [x["name"] for x in r["rising"]])


if __name__ == "__main__":
    unittest.main()
