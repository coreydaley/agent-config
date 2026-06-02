#!/usr/bin/env python3
"""Promote audit-scoped work items into the project pool.

Default mode is dry-run: prints plan and writes PROMOTE-PREVIEW.md
without touching the project pool. Pass --apply to execute.

Matching: existing work items are identified by (audit_type, audit_id).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude" / "lib"))
from plane_schema import (
    SEVERITY_TO_PRIORITY,
    WorkItem,
    find_existing_work_item,
    now_iso,
    project_work_item_path,
)


# --- Dispositions ------------------------------------------------------

CREATE = "create"
REOPEN = "re-open"
UPDATE = "update"
KEEP_DEFERRED = "keep-deferred"
SKIP_CANCELLED = "skip-cancelled"


@dataclass
class Plan:
    audit_wi: WorkItem
    existing: WorkItem | None
    disposition: str
    notes: str = ""

    @property
    def id(self) -> str:
        return self.audit_wi.id


# --- Planner -----------------------------------------------------------

def decide(audit_wi: WorkItem, existing: WorkItem | None) -> Plan:
    if existing is None:
        return Plan(audit_wi, None, CREATE,
                    "no existing work item with matching (audit_type, audit_id)")
    if existing.state == "cancelled":
        return Plan(audit_wi, existing, SKIP_CANCELLED,
                    "existing is cancelled — sticky; leaving alone")
    if existing.state == "completed":
        return Plan(audit_wi, existing, REOPEN,
                    f"existing was completed — re-opening (state → started)")
    if existing.state == "deferred":
        return Plan(audit_wi, existing, KEEP_DEFERRED,
                    f"existing is deferred (target={existing.deferral_target}) — keeping state, refreshing fields")
    return Plan(audit_wi, existing, UPDATE,
                f"existing in state={existing.state} — refreshing fields")


# --- Field-merge -------------------------------------------------------

def merge_audit_fields_into_existing(
    existing: WorkItem, audit_wi: WorkItem, *, audit_type: str, audit_ts: str,
    reopen: bool,
) -> WorkItem:
    """Refresh audit-derived fields on existing. Preserve project-side fields.
    Mutates and returns existing for clarity."""
    existing.title = audit_wi.title
    existing.description = audit_wi.description
    existing.acceptance = audit_wi.acceptance
    existing.audit_severity = audit_wi.audit_severity
    existing.audit_type = audit_wi.audit_type
    existing.audit_id = audit_wi.audit_id
    existing.priority = SEVERITY_TO_PRIORITY.get(audit_wi.audit_severity or "", existing.priority)
    existing.location_hint = audit_wi.location_hint
    existing.source_ref = audit_wi.source_ref

    # Labels: preserve non-audit labels, refresh audit-* labels.
    non_audit_labels = [l for l in existing.labels
                        if not (l == "audit" or l.startswith("audit:") or l.startswith("category:"))]
    audit_labels = [l for l in audit_wi.labels
                    if l == "audit" or l.startswith("audit:") or l.startswith("category:")]
    existing.labels = sorted(set(non_audit_labels + audit_labels))

    if reopen:
        existing.state = "started"
        # Re-opening clears the landed_in pointer because it's no longer "landed".
        existing.landed_in = None
        existing.append_activity(
            f"Re-audited by {audit_type} @ {audit_ts} — re-opened "
            f"(severity {audit_wi.audit_severity})"
        )
    else:
        existing.append_activity(
            f"Re-audited by {audit_type} @ {audit_ts} — refreshed fields "
            f"(severity {audit_wi.audit_severity}, state unchanged)"
        )
    return existing


# --- Manifest renderers -----------------------------------------------

def render_manifest(
    *, audit_type: str, audit_ts: str, audit_dir: Path,
    project: str, workspace: str, plans: list[Plan], applied: bool,
) -> str:
    tallies: dict[str, int] = {}
    for p in plans:
        tallies[p.disposition] = tallies.get(p.disposition, 0) + 1

    title = "Promote manifest" if applied else "Promote PREVIEW (dry-run)"
    lines = [
        f"# {title} — {audit_type} @ {audit_ts}",
        "",
        f"- Workspace: `{workspace}`",
        f"- Project: `{project}`",
        f"- Audit dir: `{audit_dir}`",
        f"- {'Applied' if applied else 'Planned'} at: {now_iso()}",
        f"- Items in plan: {len(plans)}",
        "",
        "## Disposition tally",
        "",
        "| Disposition | Count |",
        "|---|---:|",
    ]
    for disp in (CREATE, REOPEN, UPDATE, KEEP_DEFERRED, SKIP_CANCELLED):
        n = tallies.get(disp, 0)
        if n:
            lines.append(f"| {disp} | {n} |")
    lines += [
        "",
        "## Per-item dispositions",
        "",
        "| ID | Audit ID | Disposition | Existing state | New severity | Notes |",
        "|---|---|---|---|---|---|",
    ]
    for p in plans:
        ex_state = p.existing.state if p.existing else "(none)"
        sev = p.audit_wi.audit_severity or ""
        lines.append(
            f"| {p.id} | {p.audit_wi.audit_id} | {p.disposition} | {ex_state} | "
            f"{sev} | {p.notes} |"
        )
    if not applied:
        lines += [
            "",
            "## Next step",
            "",
            "Re-run with `--apply` to execute the plan:",
            "",
            f"```",
            f"python3 scripts/promote.py {audit_dir} --apply",
            f"```",
        ]
    lines.append("")
    return "\n".join(lines)


# --- main --------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("audit_dir", type=Path,
                    help="Audit directory containing INGEST.md.")
    ap.add_argument("--apply", action="store_true",
                    help="Execute the plan. Default is dry-run.")
    args = ap.parse_args()

    audit_dir = args.audit_dir.resolve()
    ingest_path = audit_dir / "INGEST.md"
    manifest_path = audit_dir / "MANIFEST.json"
    audit_wi_dir = audit_dir / "work-items"

    for p in (ingest_path, manifest_path, audit_wi_dir):
        if not p.exists():
            print(f"error: missing {p}", file=sys.stderr)
            print(f"       run /plane-audit-ingest first.", file=sys.stderr)
            return 1

    manifest = json.loads(manifest_path.read_text())
    audit_type = manifest["audit_name"]
    audit_ts = manifest["report_ts"]
    org_repo = manifest["org_repo"]
    org, repo = org_repo.split("/", 1)

    audit_wi_files = sorted(audit_wi_dir.glob("*.md"))
    if not audit_wi_files:
        print(f"warning: no audit-scoped work items under {audit_wi_dir}", file=sys.stderr)

    # Load each audit work item, find existing, decide.
    plans: list[Plan] = []
    for p in audit_wi_files:
        try:
            audit_wi = WorkItem.load(p)
        except Exception as e:
            print(f"error: failed to load {p}: {e}", file=sys.stderr)
            return 2
        existing = find_existing_work_item(
            org, repo, audit_wi.audit_type or "", audit_wi.audit_id or "")
        plans.append(decide(audit_wi, existing))

    # Print plan summary to stdout.
    for plan in plans:
        ex_state = plan.existing.state if plan.existing else "(none)"
        print(f"  {plan.id:<10}  {plan.disposition:<16}  "
              f"existing={ex_state:<10}  {plan.notes}")

    tally = {}
    for p in plans:
        tally[p.disposition] = tally.get(p.disposition, 0) + 1
    print("---")
    print(f"plan: {len(plans)} items — " + ", ".join(
        f"{d}={tally.get(d, 0)}" for d in (CREATE, REOPEN, UPDATE, KEEP_DEFERRED, SKIP_CANCELLED)
        if tally.get(d, 0)))

    if not args.apply:
        preview = render_manifest(
            audit_type=audit_type, audit_ts=audit_ts, audit_dir=audit_dir,
            project=repo, workspace=org, plans=plans, applied=False,
        )
        out = audit_dir / "PROMOTE-PREVIEW.md"
        out.write_text(preview)
        print(f"preview:  {out}")
        print("DRY-RUN — re-run with --apply to execute")
        return 0

    # Apply mode — execute the plan.
    for plan in plans:
        target = project_work_item_path(org, repo, plan.id)
        if plan.disposition == CREATE:
            # Save the audit-scoped work item into the project pool.
            # Note: we deliberately save a COPY so editing project-pool item
            # later doesn't reach back into the audit-scoped one.
            plan.audit_wi.save(target)
        elif plan.disposition == SKIP_CANCELLED:
            continue
        elif plan.disposition == REOPEN:
            merged = merge_audit_fields_into_existing(
                plan.existing, plan.audit_wi,
                audit_type=audit_type, audit_ts=audit_ts, reopen=True,
            )
            merged.save(target)
        elif plan.disposition in (UPDATE, KEEP_DEFERRED):
            merged = merge_audit_fields_into_existing(
                plan.existing, plan.audit_wi,
                audit_type=audit_type, audit_ts=audit_ts, reopen=False,
            )
            merged.save(target)
        else:
            print(f"error: unknown disposition {plan.disposition!r} for {plan.id}",
                  file=sys.stderr)
            return 3

    promote_out = audit_dir / "PROMOTE.md"
    promote_out.write_text(render_manifest(
        audit_type=audit_type, audit_ts=audit_ts, audit_dir=audit_dir,
        project=repo, workspace=org, plans=plans, applied=True,
    ))
    print(f"applied: {len(plans)} items")
    print(f"manifest: {promote_out}")
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
