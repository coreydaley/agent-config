---
name: plane-work-item-update
description: >-
  Update a work item's state, set landed_in (commit SHA), set
  deferral metadata, set estimate_points, or append a comment.
  Enforces the state-transition contract (e.g. cancelled is terminal;
  completed → backlog requires going through started first). Appends
  one activity-log entry per invocation.
argument-hint: "--id ID [--state STATE] [--landed-in SHA] [--defer-to TARGET --defer-reason REASON] [--comment TEXT] [--points N]"
disable-model-invocation: true
---

# plane-work-item-update — update a work item

State changes, commit-SHA links, deferral metadata, estimate, free-text
comments. One work item per invocation. Activity log auto-appended.

## Help mode

If `--help` / `-h` in args, print this verbatim and stop:

```
/plane-work-item-update — update a work item

When to use it
  - After a commit lands work: --state completed --landed-in <sha>
  - Starting work: --state started
  - Marking deferred: --state deferred --defer-to v0.2
                      --defer-reason "<text>"
  - Adding a free-text note: --comment "..."
  - Setting an estimate: --points N

What it does
  Loads the work item from the project pool, applies field changes
  with state-transition validation, appends an activity-log entry,
  writes the file back.

Allowed state transitions:
  backlog   → unstarted, started, cancelled, deferred
  unstarted → started, backlog, cancelled, deferred
  started   → completed, unstarted, cancelled, deferred
  completed → started (re-open only)
  cancelled → (terminal — no outgoing transitions)
  deferred  → backlog, unstarted, started, cancelled

Usage
  /plane-work-item-update --id ID
                          [--state STATE]
                          [--landed-in SHA]
                          [--defer-to TARGET] [--defer-reason REASON]
                          [--comment TEXT]
                          [--points N]
                          [--scope PATH]

  --id           Work item ID. Required.
  --state        New state (validated).
  --landed-in    Commit SHA. Implies --state completed unless
                 --state given explicitly.
  --defer-to     Target version slug (e.g. v0.2, v0.1.1). Implies
                 --state deferred unless --state given explicitly.
  --defer-reason Defer rationale text. Strongly recommended with
                 --defer-to.
  --comment      Free-text activity-log entry.
  --points       Estimate (integer).
  --scope        Project root. Defaults to cwd.
  --help, -h     Print this help.
```

## What to do

1. Parse args. If `--help` / `-h`, print and stop.

2. Run the script:

   ```bash
   python3 scripts/update.py [args]
   ```

3. Echo the script's output. If the script exited non-zero (typically
   from an invalid state transition), surface the error message and
   stop. Don't retry.

## Don'ts

- **Don't** bypass the state-transition rules. If you need to force a
  transition the rules don't allow, that's a sign the rules need
  updating in `lib/plane_schema.py` — discuss before changing.
- **Don't** modify audit-derived fields (`title`, `description`,
  `audit_severity`, `priority`) here. Those are owned by
  audit-ingest/promote. Use `--comment` to record context instead.
- **Don't** clear `landed_in` here. The promote skill clears it on
  re-open; nothing else should.

## ARGUMENTS

$ARGUMENTS
