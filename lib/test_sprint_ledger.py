"""Tests for sprint_ledger.get_reports_base().

The function is load-bearing across many skills (sprint-*, review-*, audit
subagents) since it determines where ~/Reports/<org>/<repo>/ resolves to.
The upstream-over-origin preference is the load-bearing rule, since `origin`
points at the personal fork under this user's GitHub workflow.

Run from the lib/ directory:

    python3 -m unittest test_sprint_ledger
"""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sprint_ledger


def _ok(stdout: str) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout, stderr="")


class GetReportsBaseTest(unittest.TestCase):
    """Verify get_reports_base() resolves the right ~/Reports/<org>/<repo>/."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="sprint-ledger-test-")
        self.home_patcher = patch.object(Path, "home", return_value=Path(self.tmpdir))
        self.home_patcher.start()

    def tearDown(self):
        self.home_patcher.stop()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _mock_git(self, remotes: dict):
        """remotes maps remote name -> stdout string. Missing keys raise CalledProcessError."""

        def fake_run(cmd, **kwargs):
            name = cmd[3]
            if name not in remotes:
                raise subprocess.CalledProcessError(returncode=128, cmd=cmd)
            return _ok(remotes[name] + "\n")

        return patch("sprint_ledger.subprocess.run", side_effect=fake_run)

    def test_prefers_upstream_over_origin(self):
        with self._mock_git({
            "upstream": "git@github.com:upstream-org/the-repo.git",
            "origin": "git@github.com:my-fork/the-repo.git",
        }):
            result = sprint_ledger.get_reports_base()
        self.assertEqual(result, Path(self.tmpdir) / "Reports" / "upstream-org" / "the-repo")

    def test_falls_back_to_origin_when_no_upstream(self):
        with self._mock_git({
            "origin": "git@github.com:coreydaley/sandbox.git",
        }):
            result = sprint_ledger.get_reports_base()
        self.assertEqual(result, Path(self.tmpdir) / "Reports" / "coreydaley" / "sandbox")

    def test_no_remotes_falls_back_to_no_repo(self):
        with self._mock_git({}):
            result = sprint_ledger.get_reports_base()
        self.assertEqual(result, Path(self.tmpdir) / "Reports" / "_no-repo")

    def test_non_github_upstream_falls_through_to_origin(self):
        with self._mock_git({
            "upstream": "https://gitlab.com/foo/bar.git",
            "origin": "git@github.com:my-org/my-repo.git",
        }):
            result = sprint_ledger.get_reports_base()
        self.assertEqual(result, Path(self.tmpdir) / "Reports" / "my-org" / "my-repo")

    def test_https_url_form(self):
        with self._mock_git({
            "upstream": "https://github.com/driftlessaf/go-driftlessaf.git",
        }):
            result = sprint_ledger.get_reports_base()
        self.assertEqual(result, Path(self.tmpdir) / "Reports" / "driftlessaf" / "go-driftlessaf")

    def test_url_without_git_suffix(self):
        with self._mock_git({
            "upstream": "git@github.com:upstream-org/the-repo",
        }):
            result = sprint_ledger.get_reports_base()
        self.assertEqual(result, Path(self.tmpdir) / "Reports" / "upstream-org" / "the-repo")

    def test_non_github_url_falls_back_to_no_repo(self):
        with self._mock_git({
            "upstream": "https://gitlab.com/foo/bar.git",
        }):
            result = sprint_ledger.get_reports_base()
        self.assertEqual(result, Path(self.tmpdir) / "Reports" / "_no-repo")

    def test_creates_directory(self):
        with self._mock_git({
            "upstream": "git@github.com:upstream-org/the-repo.git",
        }):
            result = sprint_ledger.get_reports_base()
        self.assertTrue(result.is_dir())


if __name__ == "__main__":
    unittest.main()
