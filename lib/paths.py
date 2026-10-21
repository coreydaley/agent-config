#!/usr/bin/env python3
"""Path resolver for skill bash blocks.

    REPORTS_BASE=$(python3 "$HOME/.claude/lib/paths.py" reports-base) || exit 1

Prints ~/Reports/<org>/<repo> for the cwd's checkout, with <org>/<repo> taken
from the `upstream` remote, falling back to `origin`, falling back to
local/<basename of cwd>. Same resolution as lib/audit-runner.sh. Creates the
directory. Prints one value on stdout; errors go to stderr.

The `|| exit 1` matters: skill bash runs under `set +u`, so an unset variable
expands to empty and relocates "$BASE/prs/<key>" to the filesystem root.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPORTS_ROOT = Path.home() / "Reports"


def _git(cwd: Path, *cmd: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), *cmd],
            capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return result.stdout.strip() or None


def org_repo(cwd: Path) -> str:
    for remote in ("upstream", "origin"):
        url = _git(cwd, "remote", "get-url", remote)
        if not url:
            continue
        parts = [p for p in re.split(r"[:/]", re.sub(r"\.git$", "", url)) if p]
        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1]}"
    return f"local/{cwd.resolve().name}"


def reports_base(cwd: Path) -> Path:
    base = REPORTS_ROOT / org_repo(cwd)
    base.mkdir(parents=True, exist_ok=True)
    return base


def main() -> int:
    parser = argparse.ArgumentParser(prog="paths.py", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("reports-base", "~/Reports/<org>/<repo>, created if missing"),
        ("org-repo", "<org>/<repo> of the checkout"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("-C", dest="cwd", default=".", help="checkout to resolve (default: cwd)")
    args = parser.parse_args()

    cwd = Path(args.cwd).expanduser()
    if not cwd.is_dir():
        print(f"paths.py: not a directory: {cwd}", file=sys.stderr)
        return 1
    if args.command == "reports-base":
        print(reports_base(cwd))
    else:
        print(org_repo(cwd))
    return 0


if __name__ == "__main__":
    sys.exit(main())
