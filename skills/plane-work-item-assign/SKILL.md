---
name: plane-work-item-assign
description: >-
  Assign one or more project-pool work items to a Cycle / Module / Epic
  / Milestone. Multi-target — pass multiple --id flags to bulk-assign.
  Auto-creates stub Module/Epic/Milestone files if you reference a slug
  that doesn't exist yet (so you don't have to bootstrap them
  separately).
argument-hint: "--id ID [--id ID]... [--cycle SLUG] [--module SLUG] [--epic SLUG] [--milestone SLUG]"
disable-model-invocation: true
---

# plane-work-item-assign — group work items

Sets the `cycle:` / `module:` / `epic:` / `milestone:` fields on one or
more work items in the project pool. Repeated `--id` flags bulk-assign.

## Help mode

If `--help` / `-h` in args, print this verbatim and stop:

```
/plane-work-item-assign — assign work items to Cycle/Module/Epic/Milestone

When to use it
  After /plane-cycle-new (to populate the new Cycle), or any time
  you re-organize work — moving items between Cycles, grouping
  by category Module, attaching to an Epic.

What it does
  - Loads each work item in --id list from the project pool.
  - Sets cycle/module/epic/milestone fields (whichever flags
    you passed; others left untouched).
  - Validates referenced Cycle exists. (Auto-stubs Module / Epic
    / Milestone if missing — they're flat files with no required
    pre-existence contract.)
  - Appends activity-log entry on each work item.
  - Prints a per-item summary.

Usage
  /plane-work-item-assign --id ID [--id ID]...
                          [--cycle SLUG] [--module SLUG]
                          [--epic SLUG] [--milestone SLUG]
                          [--unset FIELD]... [--scope PATH]

  --id        Work item ID (e.g. SEC-001). Repeatable.
  --cycle     Cycle id (must exist).
  --module    Module slug. Auto-stub-created if absent.
  --epic      Epic slug. Auto-stub-created if absent.
  --milestone Milestone slug. Auto-stub-created if absent.
  --unset     Clear a field. Repeatable. One of: cycle | module | epic | milestone.
  --scope     Project root. Defaults to cwd.
  --help, -h  Print this help.
```

## What to do

1. Parse args. If `--help` / `-h`, print and stop.

2. Run the script:

   ```bash
   python3 scripts/assign.py [args]
   ```

3. Echo the script's output. Stop.

## Don'ts

- **Don't** silently create Cycles. If the referenced `--cycle` doesn't
  exist, abort and tell the user to run `/plane-cycle-new`. Cycles are
  meaningful enough to require explicit creation.
- **Don't** change work-item state here. Use `/plane-work-item-update`
  for state transitions and commit-SHA links.
- **Don't** touch the `priority` / `audit_severity` fields. Those are
  owned by audit ingest/promote.

## ARGUMENTS

$ARGUMENTS
