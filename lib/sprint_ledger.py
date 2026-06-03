"""Sprint reports-tree helpers + terminal display helpers.

Small shared module for the sprint-* skills and the `commit` skill. This used
to be the TSV sprint *ledger*, but that's retired: a sprint is now a Forgejo
milestone (see `forgejo_sprints.py`), so the `SprintEntry`/`SprintLedger` model
and the on-disk `ledger.tsv` are gone. What remains is the still-shared
plumbing nothing else owns:

- `discover_reports_roots()` — find the `~/Reports/<...>/` roots that hold
  sprints (used by `forgejo_sprints.py` to decide which repos to query).
- `get_reports_base()` — resolve `~/Reports/<org>/<repo>/` from the cwd's git
  remote (the canonical rule the skills' bash replicas follow).
- terminal color helpers (`_C`, `_use_color`, `_colorize`) — used by `commit.py`.

(The filename is kept for import stability; it no longer implements a ledger.)
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional


# --- Terminal color helpers (used by commit.py) ----------------------

class _C:
    GREEN = "\033[32m"
    CYAN = "\033[36m"
    BLUE = "\033[34m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def _use_color() -> bool:
    """Auto-detect color support: NO_COLOR env var disables; otherwise require TTY."""
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def _colorize(text: str, color: str) -> str:
    return f"{color}{text}{_C.RESET}" if _use_color() else text


# --- Reports-tree resolution -----------------------------------------

def get_reports_base(override: Optional[Path] = None) -> Path:
    """Resolve the reports base directory.

    Resolution order:
    1. `override` argument (used by callers that already know the root, e.g.
       /sprint-work passing a root derived from the sprint's session_dir).
    2. SPRINT_REPORTS_ROOT env var.
    3. ~/Reports/<org>/<repo>/ from the cwd's upstream/origin remote.
    4. ~/Reports/no-repo/ fallback when cwd isn't a git repo or has no
       usable remote.

    Prefers `upstream` over `origin` because `origin` typically points at a
    personal fork under our GitHub workflow, which would land reports under
    the fork's path rather than the source repo's."""
    if override is not None:
        base = Path(override).expanduser()
        base.mkdir(parents=True, exist_ok=True)
        return base
    env_override = os.environ.get("SPRINT_REPORTS_ROOT")
    if env_override:
        base = Path(env_override).expanduser()
        base.mkdir(parents=True, exist_ok=True)
        return base
    org_repo = "no-repo"
    for remote_name in ("upstream", "origin"):
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", remote_name],
                capture_output=True, text=True, check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
        remote = result.stdout.strip()
        # Strip leading host (handles both ssh and https forms) and trailing .git
        match = re.search(r"github\.com[:/](.+?)(?:\.git)?$", remote)
        if match:
            org_repo = match.group(1)
            break
    base = Path.home() / "Reports" / org_repo
    base.mkdir(parents=True, exist_ok=True)
    return base


def discover_reports_roots() -> list[Path]:
    """Find every sprint-bearing root under ~/Reports/.

    A root is a directory that contains a `sprints/` subdirectory — that's
    where per-sprint folders live (`<root>/sprints/<TS>/`). This is the marker
    the sprint tracker (`forgejo_sprints.py`) uses to decide which repos to
    query milestones in. Supports two layouts:
    - `<root>/sprints/` for the bare-name roots (seeds/, forgejo/, no-repo/)
    - `<org>/<repo>/sprints/` for standard repo-scoped roots

    (Historically this keyed on the presence of a `ledger.tsv` file; the TSV
    ledger is retired, so discovery keys on the `sprints/` directory the roots
    actually contain. No `ledger.tsv` is required or read.)

    Returns absolute paths to the sprint-bearing directories. Empty list if
    ~/Reports/ doesn't exist yet.
    """
    base = Path.home() / "Reports"
    if not base.is_dir():
        return []
    roots: list[Path] = []
    for level1 in sorted(base.iterdir()):
        if not level1.is_dir():
            continue
        if (level1 / "sprints").is_dir():
            roots.append(level1)
            continue
        # Two-level <org>/<repo>/sprints/
        for level2 in sorted(level1.iterdir()):
            if level2.is_dir() and (level2 / "sprints").is_dir():
                roots.append(level2)
    return roots
