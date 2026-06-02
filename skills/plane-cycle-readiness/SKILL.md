---
name: plane-cycle-readiness
description: >-
  Gap analysis for a Cycle. Lists project-pool work items whose
  audit_severity is critical or high but that aren't in any Cycle —
  the structural fix for the "must-ship items hidden outside the
  current wave" failure mode. Also reports what's IN the target Cycle,
  by state, plus what's been explicitly deferred.
argument-hint: "[--cycle ID] [--stdout] [--scope PATH]"
disable-model-invocation: true
---

# plane-cycle-readiness — gap analysis

Reports unassigned high-severity work items so they can't hide outside
the current Cycle. Writes a markdown report to `<cycle-dir>/READINESS.md`
unless `--stdout` is passed.

## Help mode

If `--help` / `-h`, print this verbatim and stop:

```
/plane-cycle-readiness — Cycle gap analysis

When to use it
  - Before promoting a Cycle from planned → active, to confirm
    nothing must-ship is hiding outside it.
  - Mid-cycle as a sanity check.
  - Before /plane-cycle-close, to see what didn't land.

What it does
  Walks <project>/work-items/ and bucketizes:
    1. UNASSIGNED MUST-SHIP — critical/high severity, no cycle.
       This is the alarm row.
    2. IN-CYCLE — items whose cycle = target.
    3. OTHER CYCLES — must-ship items in different Cycles (the
       spread-thin case).
    4. EXPLICITLY DEFERRED — items in state=deferred with reason.

  Writes <cycle-dir>/READINESS.md unless --stdout.

Usage
  /plane-cycle-readiness [--cycle ID] [--stdout] [--scope PATH]

  --cycle    Specific Cycle id (defaults to active/latest).
  --stdout   Print to stdout instead of writing to READINESS.md.
  --scope    Project root. Defaults to cwd.
  --help, -h Print this help.
```

## What to do

1. Parse args. If `--help` / `-h`, print and stop.

2. Run the script:

   ```bash
   python3 scripts/readiness.py [args]
   ```

3. Echo the script's output. If gaps exist, the script exits 0 but
   prints them prominently. Surface the count to the user.

## Don'ts

- **Don't** auto-assign gaps to the Cycle. That's a scheduling
  decision — use `/plane-work-item-assign` after reviewing.
- **Don't** filter on priority alone. The gap criterion is
  `audit_severity` (objective signal from the audit) plus state. A
  manually-set high-priority feature isn't a "must ship" in this
  sense.

## ARGUMENTS

$ARGUMENTS
