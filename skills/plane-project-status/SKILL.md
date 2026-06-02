---
name: plane-project-status
description: >-
  High-level overview of a project: counts by state × priority × module
  × milestone, active Cycle, audit-source coverage, and key dates.
  Writes <project>/STATUS.md by default (or --stdout). Cheap to run;
  safe to call frequently.
argument-hint: "[--stdout] [--scope PATH]"
disable-model-invocation: true
---

# plane-project-status — project overview

Top-down read of a project. Pure aggregation — no side effects on
work items. Useful as a daily check-in or a "where are we right now"
snapshot.

## Help mode

If `--help` / `-h`, print this verbatim and stop:

```
/plane-project-status — project overview

When to use it
  Daily / weekly health check. Before a Cycle close. Before a
  milestone gate review. Any time you want a one-screen read on
  where things are.

What it does
  Aggregates the project's work items, Cycles, Modules, Epics,
  Milestones into a single markdown report:
    - Project header (name, state, ship_target)
    - Counts by state, priority, severity
    - Per-module breakdown
    - Per-milestone breakdown
    - Active + recent Cycles
    - Audit-source coverage (which audit_type the items came from)
    - Recent commits (work items with landed_in set)

Usage
  /plane-project-status [--stdout] [--scope PATH]

  --stdout   Print to stdout instead of writing STATUS.md.
  --scope    Project root. Defaults to cwd.
  --help, -h Print this help.
```

## What to do

1. Parse args. If `--help` / `-h`, print and stop.

2. Run the script:

   ```bash
   python3 scripts/status.py [args]
   ```

3. Echo the script's output (counts summary + path to STATUS.md).
   Stop.

## Don'ts

- **Don't** modify any work items. This is a read-only report.
- **Don't** assume `<project>/STATUS.md` is hand-editable — it's
  regenerated on every invocation.

## ARGUMENTS

$ARGUMENTS
