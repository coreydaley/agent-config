---
name: plane-cycle-new
description: >-
  Create a new Cycle directory + CYCLE.md under
  ~/Reports/<org>/<repo>/cycles/<DATE>--cycle-NNN/. Cycle ID is
  auto-derived from today's date plus the next sequential index.
  Doesn't assign work items — pair with plane-work-item-assign for
  that.
argument-hint: "[--name DISPLAY] [--goal TEXT] [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--exit CRITERION]..."
disable-model-invocation: true
---

# plane-cycle-new — create a new Cycle

Cycle = time-boxed batch of work items. ID format is
`<YYYY-MM-DD>--cycle-NNN` for filesystem sortability + Plane-import
compatibility.

## Help mode

If `--help` / `-h` in args, print the blurb verbatim and stop:

```
/plane-cycle-new — create a new Cycle

When to use it
  Starting a time-boxed batch of work. Typically you create a
  Cycle, then run /plane-work-item-assign to put items in it,
  then /plane-cycle-render to publish a TRACKING.md view.

What it does
  1. Scans existing cycles/ to find next sequential NNN.
  2. Builds id = <today's date>--cycle-NNN.
  3. Writes cycles/<id>/CYCLE.md with the metadata you pass.
  4. Prints the new id + path.

Usage
  /plane-cycle-new [--name DISPLAY] [--goal TEXT]
                   [--start YYYY-MM-DD] [--end YYYY-MM-DD]
                   [--exit CRITERION]... [--state STATE]
                   [--scope PATH]

  --name      Display name (defaults to "Cycle NNN").
  --goal      One-line goal text.
  --start     ISO date. Defaults to today.
  --end       ISO date. No default.
  --exit      Repeatable. Each occurrence is one exit criterion line.
  --state     planned | active | completed | cancelled (default: planned).
  --scope     Project root path. Defaults to cwd.
  --help, -h  Print this help.
```

## What to do

1. Parse args. If `--help` / `-h`, print blurb and stop.

2. Run the script:

   ```bash
   python3 scripts/new.py [args]
   ```

3. Echo the script's output. Stop. Do NOT auto-assign work items —
   `/plane-work-item-assign` is the next step.

## Don'ts

- **Don't** create a Cycle in a project where `PROJECT.md` doesn't
  exist. The script checks and aborts with a message to run
  `/plane-init` first.
- **Don't** assign work items here. Cycle creation and work-item
  assignment are deliberately separate.

## ARGUMENTS

$ARGUMENTS
