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
        self.assertEqual(result, Path(self.tmpdir) / "Reports" / "no-repo")

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
        self.assertEqual(result, Path(self.tmpdir) / "Reports" / "no-repo")

    def test_creates_directory(self):
        with self._mock_git({
            "upstream": "git@github.com:upstream-org/the-repo.git",
        }):
            result = sprint_ledger.get_reports_base()
        self.assertTrue(result.is_dir())

    def test_explicit_override_wins_over_remotes(self):
        """An explicit override (used by /sprint-work to point at the sprint's
        actual session root) bypasses cwd-remote detection so cross-cutting
        sprints under ~/Reports/seeds/ aren't misrouted to a cwd-derived path."""
        explicit = Path(self.tmpdir) / "Reports" / "seeds"
        with self._mock_git({
            "upstream": "git@github.com:upstream-org/the-repo.git",
        }):
            result = sprint_ledger.get_reports_base(explicit)
        self.assertEqual(result, explicit)
        self.assertTrue(result.is_dir())

    def test_env_var_override_when_no_explicit(self):
        """SPRINT_REPORTS_ROOT env var is the fallback override layer."""
        env_path = str(Path(self.tmpdir) / "Reports" / "linear")
        with self._mock_git({
            "upstream": "git@github.com:upstream-org/the-repo.git",
        }), patch.dict(sprint_ledger.os.environ, {"SPRINT_REPORTS_ROOT": env_path}):
            result = sprint_ledger.get_reports_base()
        self.assertEqual(result, Path(env_path))

    def test_explicit_override_beats_env_var(self):
        """When both are set, the explicit argument wins (callers know more)."""
        explicit = Path(self.tmpdir) / "Reports" / "explicit"
        env_path = str(Path(self.tmpdir) / "Reports" / "from-env")
        with patch.dict(sprint_ledger.os.environ, {"SPRINT_REPORTS_ROOT": env_path}):
            result = sprint_ledger.get_reports_base(explicit)
        self.assertEqual(result, explicit)


class UpdateStatusTest(unittest.TestCase):
    """Verify update_status preserves started_at on idempotent --start.

    Re-running /sprints --start on an already-in-progress sprint (resume,
    re-invocation) must not reset the timer or duration/velocity stats
    are corrupted."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="sprint-update-status-test-")
        self.ledger_path = Path(self.tmpdir) / "ledger.tsv"
        self.ledger = sprint_ledger.SprintLedger(self.ledger_path)
        self.ledger.entries["2026-05-08T14-30-00"] = sprint_ledger.SprintEntry(
            session="2026-05-08T14-30-00",
            title="Test sprint",
            status="planned",
            created_at="2026-05-08T14:30:00Z",
            updated_at="2026-05-08T14:30:00Z",
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_first_start_stamps_started_at(self):
        entry = self.ledger.update_status("2026-05-08T14-30-00", "in_progress")
        self.assertTrue(entry.started_at)
        first_stamp = entry.started_at

        # Re-start: started_at must NOT change
        import time
        time.sleep(1.1)  # ensure _now() would differ at second precision
        entry = self.ledger.update_status("2026-05-08T14-30-00", "in_progress")
        self.assertEqual(entry.started_at, first_stamp)

    def test_complete_then_restart_does_stamp(self):
        """If a sprint was completed and is being restarted (legit reuse),
        started_at SHOULD reset — it's a fresh run."""
        self.ledger.update_status("2026-05-08T14-30-00", "in_progress")
        first_stamp = self.ledger.entries["2026-05-08T14-30-00"].started_at
        self.ledger.update_status("2026-05-08T14-30-00", "completed")

        import time
        time.sleep(1.1)  # ensure _now() differs at second precision
        entry = self.ledger.update_status("2026-05-08T14-30-00", "in_progress")
        self.assertNotEqual(entry.started_at, first_stamp)


class DiscoverReportsRootsTest(unittest.TestCase):
    """Verify multi-root discovery handles both bare-name and <org>/<repo> layouts.

    /sprints uses this when no explicit --root is passed, so cross-cutting
    sprints under seeds/ are resolvable without the caller knowing the root."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="sprint-discover-test-")
        self.home_patcher = patch.object(Path, "home", return_value=Path(self.tmpdir))
        self.home_patcher.start()
        self.reports = Path(self.tmpdir) / "Reports"
        self.reports.mkdir()

    def tearDown(self):
        self.home_patcher.stop()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_root(self, *path_parts: str) -> Path:
        """Create a ledger-bearing root at ~/Reports/<path_parts>/."""
        root = self.reports.joinpath(*path_parts)
        root.mkdir(parents=True)
        (root / "ledger.tsv").write_text("session\ttitle\tstatus\n")
        return root

    def test_no_reports_dir_returns_empty(self):
        shutil.rmtree(self.reports)
        self.assertEqual(sprint_ledger.discover_reports_roots(), [])

    def test_finds_bare_name_root(self):
        seeds = self._make_root("seeds")
        roots = sprint_ledger.discover_reports_roots()
        self.assertIn(seeds, roots)

    def test_finds_org_repo_root(self):
        repo = self._make_root("upstream-org", "the-repo")
        roots = sprint_ledger.discover_reports_roots()
        self.assertIn(repo, roots)

    def test_mixed_layouts(self):
        """The four real-world roots should all be discovered together."""
        seeds = self._make_root("seeds")
        linear = self._make_root("linear")
        no_repo = self._make_root("no-repo")
        repo_a = self._make_root("upstream-org", "the-repo")
        repo_b = self._make_root("another-org", "another-repo")
        roots = sprint_ledger.discover_reports_roots()
        for r in (seeds, linear, no_repo, repo_a, repo_b):
            self.assertIn(r, roots)

    def test_skips_non_ledger_dirs(self):
        """A subdir without ledger.tsv shouldn't be returned (e.g., a stray
        directory, or a sandbox under <org>/<repo>/ that has no ledger yet)."""
        self._make_root("seeds")
        (self.reports / "stray-dir").mkdir()
        (self.reports / "another" / "no-ledger-here").mkdir(parents=True)
        roots = sprint_ledger.discover_reports_roots()
        self.assertEqual(len(roots), 1)


if __name__ == "__main__":
    unittest.main()
