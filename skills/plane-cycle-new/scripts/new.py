#!/usr/bin/env python3
"""Create a new Cycle under <project>/cycles/<DATE>--cycle-NNN/."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude" / "lib"))
from plane_schema import (
    Cycle,
    Project,
    project_dir,
    resolve_org_repo,
)


CYCLE_ID_RE = re.compile(r"^(?P<date>\d{4}-\d{2}-\d{2})--cycle-(?P<n>\d{3,})$")


def next_index(org: str, repo: str) -> int:
    """Find next sequential cycle index by scanning existing dirs."""
    cdir = project_dir(org, repo) / "cycles"
    if not cdir.exists():
        return 1
    max_n = 0
    for d in cdir.iterdir():
        if not d.is_dir():
            continue
        m = CYCLE_ID_RE.match(d.name)
        if m:
            max_n = max(max_n, int(m.group("n")))
    return max_n + 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scope", default=".", help="Project root (defaults to cwd).")
    ap.add_argument("--name", help="Display name. Defaults to 'Cycle NNN'.")
    ap.add_argument("--goal", default="", help="One-line goal text.")
    ap.add_argument("--start", default=date.today().isoformat(),
                    help="Start date YYYY-MM-DD. Defaults to today.")
    ap.add_argument("--end", default="", help="End date YYYY-MM-DD. No default.")
    ap.add_argument("--exit", action="append", default=[], dest="exit_criteria",
                    help="Exit criterion. Repeatable.")
    ap.add_argument("--state", default="planned",
                    choices=["planned", "active", "completed", "cancelled"],
                    help="Cycle state. Default: planned.")
    ap.add_argument("--description", default="", help="Free-text description.")
    args = ap.parse_args()

    project_cwd = Path(args.scope).resolve()
    org, repo = resolve_org_repo(project_cwd)

    project = Project.load(org, repo)
    if project is None:
        print(f"error: PROJECT.md missing for {org}/{repo}", file=sys.stderr)
        print(f"       run /plane-init in this project first.", file=sys.stderr)
        return 1

    idx = next_index(org, repo)
    cycle_id = f"{date.today().isoformat()}--cycle-{idx:03d}"
    name = args.name or f"Cycle {idx:03d}"

    c = Cycle(
        id=cycle_id, name=name, project=repo, workspace=org,
        goal=args.goal, state=args.state,
        start_date=args.start, end_date=args.end,
        exit_criteria=args.exit_criteria,
        description=args.description,
    )
    p = c.save()
    print(f"cycle:    {cycle_id}")
    print(f"name:     {name}")
    print(f"path:     {p}")
    print(f"state:    {args.state}")
    if args.exit_criteria:
        print(f"exit:     {len(args.exit_criteria)} criterion(a)")
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
