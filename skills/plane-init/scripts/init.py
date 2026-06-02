#!/usr/bin/env python3
"""Bootstrap a Plane-shaped markdown workspace + project.

Idempotent. Never overwrites existing WORKSPACE.md / PROJECT.md.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude" / "lib"))
from plane_schema import (
    Project,
    Workspace,
    project_dir,
    resolve_org_repo,
    workspace_dir,
)


def titlecase(slug: str) -> str:
    return " ".join(w.capitalize() for w in re.split(r"[-_]+", slug) if w)


def repo_url(project_cwd: Path) -> str:
    for remote in ("upstream", "origin"):
        try:
            url = subprocess.check_output(
                ["git", "-C", str(project_cwd), "remote", "get-url", remote],
                stderr=subprocess.DEVNULL, text=True).strip()
            if url:
                return url
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    return ""


def ensure_subdirs(pdir: Path) -> list[str]:
    """Create the standard subdirs, return list of created (new) ones."""
    created = []
    for name in ("work-items", "cycles", "modules", "epics", "milestones", "pages"):
        sub = pdir / name
        if not sub.exists():
            sub.mkdir(parents=True)
            created.append(name)
    return created


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("scope", nargs="?", default=".",
                    help="Project root (defaults to cwd).")
    args = ap.parse_args()

    project_cwd = Path(args.scope).resolve()
    if not project_cwd.is_dir():
        print(f"error: scope is not a directory: {project_cwd}", file=sys.stderr)
        return 1

    org, repo = resolve_org_repo(project_cwd)
    wdir = workspace_dir(org)
    pdir = project_dir(org, repo)
    pdir.mkdir(parents=True, exist_ok=True)

    print(f"resolved: org={org} repo={repo}")
    print(f"workspace: {wdir}")
    print(f"project:   {pdir}")

    # WORKSPACE.md
    ws = Workspace.load(org)
    if ws is None:
        ws = Workspace(
            id=org, name=titlecase(org),
            description=(
                f"Plane-shaped markdown workspace for the `{org}` GitHub org. "
                f"One project directory per repo lives at the same level as "
                f"this file.\n"
            ),
        )
        ws.save()
        print(f"created: {wdir / 'WORKSPACE.md'}")
    else:
        print(f"exists:  {wdir / 'WORKSPACE.md'}")

    # PROJECT.md
    pr = Project.load(org, repo)
    if pr is None:
        url = repo_url(project_cwd)
        pr = Project(
            id=repo, name=titlecase(repo), workspace=org,
            repo_url=url,
            description=(
                f"Project markdown store for `{org}/{repo}`. Work items, "
                f"cycles, modules, epics, and milestones for this project "
                f"live in sibling directories. Audit input under `audits/` "
                f"is owned by the audit-* skills.\n"
            ),
        )
        pr.save()
        print(f"created: {pdir / 'PROJECT.md'}")
    else:
        print(f"exists:  {pdir / 'PROJECT.md'}")

    # Subdirs
    created = ensure_subdirs(pdir)
    if created:
        print(f"created subdirs: {', '.join(created)}")
    else:
        print("subdirs: all present")

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
