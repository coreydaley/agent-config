import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import paths  # noqa: E402


def _repo(remotes: dict[str, str]) -> Path:
    d = Path(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q", str(d)], check=True)
    for name, url in remotes.items():
        subprocess.run(["git", "-C", str(d), "remote", "add", name, url], check=True)
    return d


class OrgRepoTest(unittest.TestCase):
    def test_upstream_wins_over_origin(self):
        d = _repo({
            "origin": "https://github.com/fork-owner/widget.git",
            "upstream": "https://github.com/acme/widget.git",
        })
        self.assertEqual(paths.org_repo(d), "acme/widget")

    def test_origin_when_no_upstream(self):
        d = _repo({"origin": "https://github.com/acme/widget.git"})
        self.assertEqual(paths.org_repo(d), "acme/widget")

    def test_scp_and_ssh_forms(self):
        for url in ("git@github.com:acme/widget.git", "ssh://git@host:2222/acme/widget"):
            with self.subTest(url=url):
                self.assertEqual(paths.org_repo(_repo({"origin": url})), "acme/widget")

    def test_no_remote_falls_back_to_local(self):
        d = _repo({})
        self.assertEqual(paths.org_repo(d), f"local/{d.resolve().name}")

    def test_not_a_repo_falls_back_to_local(self):
        d = Path(tempfile.mkdtemp())
        self.assertEqual(paths.org_repo(d), f"local/{d.resolve().name}")


class ReportsBaseTest(unittest.TestCase):
    def test_creates_under_reports_root(self):
        root = Path(tempfile.mkdtemp())
        d = _repo({"origin": "https://github.com/acme/widget.git"})
        with mock.patch.object(paths, "REPORTS_ROOT", root):
            base = paths.reports_base(d)
        self.assertEqual(base, root / "acme" / "widget")
        self.assertTrue(base.is_dir())


class CliTest(unittest.TestCase):
    def test_missing_dir_exits_nonzero(self):
        result = subprocess.run(
            [sys.executable, str(Path(paths.__file__)), "org-repo", "-C", "/nonexistent/x"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
