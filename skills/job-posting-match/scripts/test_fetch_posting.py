#!/usr/bin/env python3
"""Unit tests for fetch_posting.py URL parsing and text cleanup (no network)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import fetch_posting as fp  # noqa: E402


class Parse(unittest.TestCase):
    def test_greenhouse_job_boards(self):
        self.assertEqual(fp.parse("https://job-boards.greenhouse.io/acme/jobs/123"), ("greenhouse", "acme", "123"))

    def test_greenhouse_classic_boards(self):
        self.assertEqual(fp.parse("https://boards.greenhouse.io/acme/jobs/123?t=x"), ("greenhouse", "acme", "123"))

    def test_careers_page_with_gh_jid_needs_slug(self):
        url = "https://www.acme.com/careers/123?gh_jid=123"
        self.assertIsNone(fp.parse(url))
        self.assertEqual(fp.parse(url, "acme"), ("greenhouse", "acme", "123"))

    def test_lever(self):
        self.assertEqual(fp.parse("https://jobs.lever.co/acme/abc-123/apply"), ("lever", "acme", "abc-123"))

    def test_ashby(self):
        self.assertEqual(fp.parse("https://jobs.ashbyhq.com/acme/uuid-1"), ("ashby", "acme", "uuid-1"))

    def test_unsupported(self):
        self.assertIsNone(fp.parse("https://example.com/jobs/1"))
        self.assertIsNone(fp.parse("https://jobs.lever.co/acme"))


class ToText(unittest.TestCase):
    def test_double_escaped_greenhouse_content(self):
        self.assertEqual(fp.to_text("&lt;p&gt;Go &amp;amp; Rust&lt;/p&gt;"), "Go & Rust")

    def test_nbsp(self):
        self.assertEqual(fp.to_text("a&nbsp;b"), "a b")


class PayAndWorkplace(unittest.TestCase):
    def test_pay_ranges_from_text(self):
        text = "Benefits\nUSA base pay range (CA, WA) per year: $195,000 - $255,000\nOther states: $173,000 to $233,000"
        pay = fp.pay_from_text(text)
        self.assertEqual(len(pay), 2)
        self.assertTrue(pay[0].startswith("$195,000 - $255,000"))
        self.assertTrue(pay[1].startswith("$173,000 to $233,000"))

    def test_ignores_money_outside_pay_lines(self):
        self.assertEqual(fp.pay_from_text("We raised $10 - $20 million last year"), [])

    def test_workplace(self):
        self.assertEqual(fp.workplace_from("Remote US", "", ""), "remote")
        self.assertEqual(fp.workplace_from("New York", "... #LI-Hybrid", ""), "hybrid")
        self.assertEqual(fp.workplace_from("New York", "", ""), "")
        self.assertEqual(fp.workplace_from("Remote", "", "hybrid"), "hybrid")


if __name__ == "__main__":
    unittest.main()
