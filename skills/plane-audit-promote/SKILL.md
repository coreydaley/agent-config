---
name: plane-audit-promote
description: >-
  Promote audit-scoped work items into the project work-items pool.
  Matches existing work items by (audit_type, audit_id). Re-opens
  completed items, leaves cancelled items alone, updates everything
  else. Runs in dry-run mode by default so the user can review the
  proposed plan before applying. Idempotent in apply mode — running
  twice on the same INGEST.md is a no-op the second time.
argument-hint: "[audit-dir] [--apply] [--help]"
disable-model-invocation: true
---

# plane-audit-promote — audit work items → project pool

Lifts findings from one audit's `work-items/` into the project's
canonical `work-items/` pool under `~/Reports/<org>/<repo>/`. Per the
matching contract, the same finding surfacing in a re-audit re-opens
the existing work item rather than creating a duplicate.

## Help mode

If `--help` / `-h` is in arguments, print this verbatim and stop:

```
/plane-audit-promote — audit work items → project pool

When to use it
  After /plane-audit-ingest has written audit-scoped work items
  and INGEST.md. Promotion lifts those into the project's
  canonical work-items/ pool so cycles, modules, and milestones
  can reference them.

What it does
  Default: dry-run — prints proposed dispositions, writes
  <audit-dir>/PROMOTE-PREVIEW.md.

  With --apply: executes the plan — creates new work items,
  re-opens completed ones, updates fields on existing items
  that aren't cancelled. Writes <audit-dir>/PROMOTE.md manifest.

  Matching rule: existing project work item is identified by
  matching (audit_type, audit_id). Title or description changes
  in the new audit do NOT cause duplicates.

Disposition matrix:
  - no match              → create new work item in project pool
  - match, completed      → re-open: state→started, fields refreshed
  - match, cancelled      → skip: no changes (cancelled is sticky)
  - match, deferred       → keep state, refresh fields, log re-audit
  - match, started/etc.   → refresh fields, log re-audit

Usage
  /plane-audit-promote [<audit-dir>] [--apply] [--help]

  <audit-dir>  Audit directory (the one containing INGEST.md).
               If omitted, uses the most recent audit dir with an
               INGEST.md present under the current project.
  --apply      Execute the plan (default is dry-run).
```

## What to do

1. **Parse args.** If `--help` / `-h` present, print the help blurb
   above and stop.

2. **Resolve the audit dir.** If a path argument is present, use it.
   Otherwise find the most recent audit dir under the current project
   that has an `INGEST.md` (the marker that ingest already ran).

3. **Verify INGEST.md exists.** If it doesn't, instruct the user to
   run `/plane-audit-ingest` first and stop.

4. **Run the promote script in dry-run mode FIRST** (always):

   ```bash
   python3 scripts/promote.py <audit-dir>
   ```

   The script prints a per-item disposition plan to stdout and writes
   `<audit-dir>/PROMOTE-PREVIEW.md`. No project-pool files are touched
   in this mode.

5. **Present the dispositions to the user.** Summarize the plan:
   - N new (create)
   - N re-open (completed → started)
   - N update (refresh fields)
   - N skip (cancelled)
   - N keep-deferred (refresh fields, state unchanged)

   Ask via `AskUserQuestion`:
   > "Apply the promotion plan to the project work-items pool?"
   - **Apply** — runs `promote.py <audit-dir> --apply`
   - **Cancel** — leaves PROMOTE-PREVIEW.md in place, exits

6. **On Apply, run with `--apply`:**

   ```bash
   python3 scripts/promote.py <audit-dir> --apply
   ```

   The script:
   - Creates new project-pool work items where no match.
   - Re-opens completed matches (state → started; appends activity
     log; refreshes audit_severity/labels/description).
   - Updates non-cancelled matches (refreshes fields; appends
     activity log).
   - Skips cancelled matches (no changes).
   - Writes `<audit-dir>/PROMOTE.md` manifest with final
     dispositions.

7. **Report.** Echo the apply-mode output and the path to PROMOTE.md.
   Stop. Do NOT proceed to schedule into a Cycle — that's a separate
   skill (`/plane-cycle-plan`, Phase 2).

## Field preservation policy

When updating an existing project-pool work item, the script:

**Preserves (does NOT touch) these fields** — they're project-side planning data:
- `state` (unless re-opening completed: completed → started)
- `cycle`, `module`, `epic`, `milestone`
- `assignee`, `estimate_points`
- `deferral_reason`, `deferral_target`
- `landed_in`
- `created` (original creation timestamp)
- Existing `activity_log` entries (new entry is appended)

**Refreshes from the new audit** — these are audit-derived:
- `title`, `description`, `acceptance`
- `audit_severity`
- `priority` (re-derived from severity)
- `audit-*` labels (non-audit labels preserved)
- `location_hint`
- `source_ref`
- `updated` timestamp

## Don'ts

- **Don't** apply without showing the dry-run plan first. The user
  must explicitly approve.
- **Don't** modify `cancelled` work items. Cancelled is sticky —
  the user decided this finding isn't real or isn't going to be
  worked.
- **Don't** create duplicate work items when the matching key
  matches an existing one. The point of the (audit_type, audit_id)
  match is exactly this.
- **Don't** touch any audit-scoped work items under
  `<audit-dir>/work-items/`. Promotion is read-only on the audit
  side; it writes only to the project pool.
- **Don't** schedule into a Cycle here. Cycle scheduling is the next
  skill's job.

## ARGUMENTS

Optional audit dir path. Optional `--apply` flag. `--help` / `-h`
prints help.

The literal arguments passed by the user follow:

$ARGUMENTS
