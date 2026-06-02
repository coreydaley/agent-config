---
name: plane-cycle-render
description: >-
  Render a human-readable TRACKING.md view of a Cycle by scanning all
  project-pool work items whose `cycle:` field matches. Groups by
  Module, shows state checkboxes + priority + title, includes summary
  tallies. Writes to <cycle-dir>/TRACKING.md by default (or stdout).
argument-hint: "[--cycle ID] [--stdout] [--scope PATH]"
disable-model-invocation: true
---

# plane-cycle-render — render a Cycle as TRACKING.md

Generates a human-readable markdown view of a Cycle. The source of
truth is each work item's `cycle:` field; this skill reads those and
aggregates. Re-running is safe — the output file is regenerated each
time.

## Help mode

If `--help` / `-h` in args, print this verbatim and stop:

```
/plane-cycle-render — render a Cycle as TRACKING.md

When to use it
  - After /plane-work-item-assign populates a Cycle, to publish a
    readable view.
  - Any time during the Cycle to refresh the TRACKING.md snapshot
    (e.g. after state changes).

What it does
  Scans <project>/work-items/*.md for items where cycle: matches
  the target Cycle id. Groups by Module, sorts by priority then
  ID. Renders to <cycle-dir>/TRACKING.md (or stdout with --stdout).

  Resolution order for --cycle:
    1. --cycle <id> argument
    2. If exactly one Cycle in state=active, uses that.
    3. Otherwise: most recent Cycle by id (filesystem sort).

Usage
  /plane-cycle-render [--cycle ID] [--stdout] [--scope PATH]

  --cycle    Specific Cycle id (e.g. 2026-05-22--cycle-001).
  --stdout   Print to stdout instead of writing to TRACKING.md.
  --scope    Project root. Defaults to cwd.
  --help, -h Print this help.
```

## What to do

1. Parse args. If `--help` / `-h`, print and stop.

2. Run the script:

   ```bash
   python3 scripts/render.py [args]
   ```

3. Echo the script's output (rendered TRACKING.md path + tallies).
   Stop.

## Don'ts

- **Don't** edit the rendered `TRACKING.md` by hand. It is regenerated
  each invocation — edits will be lost. The source of truth is each
  work-item file's frontmatter.
- **Don't** include audit-source noise in the rendered view. Show
  what's actionable; the audit_id is shown as supplemental context.

## ARGUMENTS

$ARGUMENTS
