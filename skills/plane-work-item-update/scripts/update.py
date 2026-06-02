#!/usr/bin/env python3
"""Update a work item: state, landed_in, deferral, comment, points."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude" / "lib"))
from plane_schema import (
    WorkItem,
    project_work_item_path,
    resolve_org_repo,
    validate_transition,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scope", default=".", help="Project root.")
    ap.add_argument("--id", required=True, help="Work item ID.")
    ap.add_argument("--state",
                    choices=["backlog", "unstarted", "started", "completed",
                             "cancelled", "deferred"],
                    help="New state.")
    ap.add_argument("--landed-in", dest="landed_in",
                    help="Commit SHA. Implies --state completed.")
    ap.add_argument("--defer-to", dest="defer_to",
                    help="Defer-target slug. Implies --state deferred.")
    ap.add_argument("--defer-reason", dest="defer_reason",
                    help="Defer rationale text.")
    ap.add_argument("--comment", help="Free-text activity-log entry.")
    ap.add_argument("--points", type=int, help="Estimate (integer).")
    args = ap.parse_args()

    project_cwd = Path(args.scope).resolve()
    org, repo = resolve_org_repo(project_cwd)
    p = project_work_item_path(org, repo, args.id)
    if not p.exists():
        print(f"error: work item not found: {p}", file=sys.stderr)
        return 1

    wi = WorkItem.load(p)
    prior_state = wi.state

    # Implied-state derivations.
    new_state = args.state
    if args.landed_in and new_state is None:
        new_state = "completed"
    if args.defer_to and new_state is None:
        new_state = "deferred"

    # State transition (validated). Special case: --landed-in from
    # backlog/unstarted bridges through started → completed in one op, so
    # callers don't have to two-step "mark started, then mark completed"
    # just to log a commit SHA after the fact.
    bridged = False
    if (args.landed_in
            and new_state == "completed"
            and prior_state in ("backlog", "unstarted")):
        # Walk: prior → started → completed (both transitions are valid).
        wi.state = "started"
        wi.state = "completed"
        bridged = True
    elif new_state and new_state != prior_state:
        err = validate_transition(prior_state, new_state)
        if err:
            print(f"error: {err}", file=sys.stderr)
            return 2
        wi.state = new_state

    # Field updates.
    activity_bits = []
    if bridged:
        activity_bits.append(f"state {prior_state} → started → completed (bridged by --landed-in)")
    elif new_state and new_state != prior_state:
        activity_bits.append(f"state {prior_state} → {new_state}")
    if args.landed_in:
        wi.landed_in = args.landed_in
        activity_bits.append(f"landed_in={args.landed_in}")
    if args.defer_to:
        wi.deferral_target = args.defer_to
        activity_bits.append(f"defer_to={args.defer_to}")
    if args.defer_reason:
        wi.deferral_reason = args.defer_reason
        activity_bits.append("defer_reason set")
    if args.points is not None:
        wi.estimate_points = args.points
        activity_bits.append(f"points={args.points}")

    if not activity_bits and not args.comment:
        print("error: nothing to update — pass --state, --landed-in, "
              "--defer-to, --defer-reason, --comment, or --points",
              file=sys.stderr)
        return 3

    log = "; ".join(activity_bits)
    if args.comment:
        log = f"{log} — {args.comment}" if log else args.comment
    wi.append_activity(log)
    wi.save(p)

    print(f"  {wi.id}: state={wi.state} priority={wi.priority}"
          + (f" landed_in={wi.landed_in}" if wi.landed_in else "")
          + (f" defer_to={wi.deferral_target}" if wi.deferral_target else ""))
    print(f"  activity: {log}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
