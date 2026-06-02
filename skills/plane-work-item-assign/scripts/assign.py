#!/usr/bin/env python3
"""Assign work items to Cycle/Module/Epic/Milestone groupings."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude" / "lib"))
from plane_schema import (
    Cycle,
    Epic,
    Milestone,
    Module,
    WorkItem,
    project_work_item_path,
    resolve_org_repo,
    slugify,
)


VALID_UNSET = {"cycle", "module", "epic", "milestone"}


def stub_named_entity(cls, *, org: str, repo: str, slug: str) -> None:
    if cls.load(org, repo, slug) is not None:
        return
    cls(id=slug, name=slug.replace("-", " ").title(),
        project=repo, workspace=org,
        description=f"Auto-stubbed by plane-work-item-assign. "
                    f"Edit name/description as needed.\n").save()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scope", default=".", help="Project root.")
    ap.add_argument("--id", action="append", default=[], dest="ids",
                    required=True, help="Work item ID. Repeatable.")
    ap.add_argument("--cycle", help="Cycle id (must exist).")
    ap.add_argument("--module", help="Module slug (auto-stub if absent).")
    ap.add_argument("--epic", help="Epic slug (auto-stub if absent).")
    ap.add_argument("--milestone", help="Milestone slug (auto-stub if absent).")
    ap.add_argument("--unset", action="append", default=[],
                    help="Clear a field: cycle | module | epic | milestone. Repeatable.")
    args = ap.parse_args()

    project_cwd = Path(args.scope).resolve()
    org, repo = resolve_org_repo(project_cwd)

    # Validate --unset values.
    for u in args.unset:
        if u not in VALID_UNSET:
            print(f"error: --unset must be one of {sorted(VALID_UNSET)}; got {u!r}",
                  file=sys.stderr)
            return 2

    # Validate Cycle exists (hard requirement).
    if args.cycle:
        if Cycle.load(org, repo, args.cycle) is None:
            print(f"error: cycle {args.cycle!r} does not exist", file=sys.stderr)
            print(f"       run /plane-cycle-new first.", file=sys.stderr)
            return 3

    # Auto-stub Module/Epic/Milestone if missing.
    if args.module:
        stub_named_entity(Module, org=org, repo=repo, slug=args.module)
    if args.epic:
        stub_named_entity(Epic, org=org, repo=repo, slug=args.epic)
    if args.milestone:
        stub_named_entity(Milestone, org=org, repo=repo, slug=args.milestone)

    # Apply per work item.
    fields_set = []
    if args.cycle:     fields_set.append(f"cycle={args.cycle}")
    if args.module:    fields_set.append(f"module={args.module}")
    if args.epic:      fields_set.append(f"epic={args.epic}")
    if args.milestone: fields_set.append(f"milestone={args.milestone}")
    for u in args.unset:
        fields_set.append(f"{u}=(unset)")

    if not fields_set:
        print("error: nothing to assign — pass at least one of "
              "--cycle / --module / --epic / --milestone / --unset",
              file=sys.stderr)
        return 4

    summary = ", ".join(fields_set)
    errors = 0
    for wi_id in args.ids:
        p = project_work_item_path(org, repo, wi_id)
        if not p.exists():
            print(f"  {wi_id:<10} ERROR: not found at {p}", file=sys.stderr)
            errors += 1
            continue
        wi = WorkItem.load(p)
        if args.cycle:     wi.cycle = args.cycle
        if args.module:    wi.module = args.module
        if args.epic:      wi.epic = args.epic
        if args.milestone: wi.milestone = args.milestone
        for u in args.unset:
            setattr(wi, u, None)
        wi.append_activity(f"Assigned: {summary}")
        wi.save(p)
        print(f"  {wi_id:<10} ok ({summary})")

    if errors:
        print(f"---\n{errors} error(s); {len(args.ids) - errors} updated", file=sys.stderr)
        return 5
    print(f"---\n{len(args.ids)} item(s) updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
