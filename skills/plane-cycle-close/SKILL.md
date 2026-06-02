---
name: plane-cycle-close
description: >-
  Close out a Cycle. Generates a RETRO.md report (per-item state, what
  landed vs slipped vs deferred), sets cycle.state = completed. Slipped
  items keep their cycle: field pointing at the now-completed Cycle —
  the user explicitly moves them with /plane-work-item-assign if they
  want them in a future Cycle.
argument-hint: "[--cycle ID] [--notes TEXT] [--scope PATH]"
disable-model-invocation: true
---

# plane-cycle-close — close out a Cycle

Final step in a Cycle's lifecycle. Generates a retro report and flips
the Cycle's state to `completed`. Designed to be called by a human
deciding "this Cycle is done."

## Help mode

If `--help` / `-h`, print this verbatim and stop:

```
/plane-cycle-close — close out a Cycle

When to use it
  When a Cycle is done — either because the end_date arrived,
  the exit criteria are met, or you're cutting it short and
  moving slipped items to the next Cycle.

What it does
  1. Resolves the target Cycle (--cycle, or active, or latest).
  2. Walks all work items with cycle: matching the target.
  3. Generates RETRO.md classifying each: landed (completed),
     slipped (still in {backlog, unstarted, started}),
     deferred (state=deferred), cancelled.
  4. Sets cycle.state = completed (only valid from planned/active).
  5. Prints summary + path to RETRO.md.

  Slipped items KEEP their cycle: field pointing at this Cycle
  (audit trail). To move them, run
  /plane-work-item-assign --cycle <next-cycle> for each.

Usage
  /plane-cycle-close [--cycle ID] [--notes TEXT] [--scope PATH]

  --cycle    Cycle id (defaults to active/latest).
  --notes    Free-text retro notes appended to RETRO.md. Multi-line
             OK if your shell handles it.
  --scope    Project root. Defaults to cwd.
  --help, -h Print this help.
```

## What to do

1. Parse args. If `--help` / `-h`, print and stop.

2. Run a dry-run summary FIRST (no state change). The script when
   called without `--apply` shows what would happen:

   ```bash
   python3 scripts/close.py [args]
   ```

3. **Show the user the summary** (landed / slipped / deferred / cancelled
   counts plus the RETRO.md preview path) and ask via
   `AskUserQuestion`:

   > "Close the Cycle? Slipped items will keep their cycle: field
   > pointing here. RETRO.md will be regenerated as the final version."

   - **Close** — runs `close.py --apply`
   - **Cancel** — leaves RETRO-PREVIEW.md in place, no state change

4. On approval, run `close.py --apply`. Echo the output.

## Don'ts

- **Don't** auto-move slipped items to another Cycle. That's a
  scheduling call. Surface them clearly in RETRO.md and let the user
  drive the next-Cycle assignment with `/plane-work-item-assign`.
- **Don't** modify work item states here. Only `cycle.state` changes.
- **Don't** close a Cycle that's already `completed` or `cancelled`.
  The script will refuse.

## ARGUMENTS

$ARGUMENTS
