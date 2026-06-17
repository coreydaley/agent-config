# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` with the baseline P0/P1/Deferred mapping. Every task's verification step must specify an Instruments configuration and require before/after measurement.

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Sprint mapping

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | **Immediate Action — fix before next release** |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

For Apple performance, Critical = a measured (or near-certain) hang / crash / launch-time regression / widget kill. These are user-visible regressions; treat with the same urgency as a Critical security finding even though no out-of-band patch is required.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Category** — one of the 10 Apple performance categories
- **Location** — `path/to/file.swift:line` (never just a function name)
- **Instrument** — required (`TimeProfiler`, `Allocations`, `Leaks`, `Hangs`, `MetricKit`, `SwiftUI Profiler`, `EnergyLog`, `Network`, or `static`)
- **Platform** — `iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`, `visionOS`, `WidgetExtension`, or `Multi`
- **Verification mode** — `code` (inspectable) or `runtime` (Instruments profiling required)
- **Issue** — clear description
- **Remediation** — concrete, specific (never "fix the issue")
- **Verification step** — Instruments configuration to use AND a before/after measurement protocol. "Looks faster" is not verification.
- **Baseline / Target** — the measurement before the fix and the target after (e.g. "cold launch 3.2s → <1.5s"; "scroll FPS 42 → 60"; "widget peak memory 38 MB → <25 MB")

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — apple-performance — <scope>, <date>`
- Task description: scope covered, 10 categories reviewed, tooling that ran, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Apple Performance Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, tooling summary, total findings by severity, top 3
issues, reminder of audit's inherent limitations — performance is a
runtime property; static review identifies likely issues but Instruments
profiling is required to confirm magnitude. Many tasks will be runtime
verification.>

<If Critical findings exist:>
> ⚠️ **Critical findings present.** User-visible regressions (hangs,
> launch-time blowouts, widget kills, OOM). Fix before next release.

## Audit Summary

| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Total | N |

| Category | Count |
|---|---|
<non-zero categories only>

Intermediate audit artifacts:
- $AUDIT_DIR/tooling-raw/ (semgrep, grep-patterns, instruments-traces)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### Immediate Action — fix before next release

<one block per Critical finding>

**Task: S### — <Category> — <Title>**
- Location: `path/to/file.swift:line`
- Instrument: <TimeProfiler | Allocations | Leaks | Hangs | MetricKit | SwiftUI Profiler | EnergyLog | Network | static>
- Platform: <platform>
- Verification mode: <code | runtime>
- Issue: <description>
- Remediation: <specific fix>
- Verification step: <Instruments configuration: which template, which scheme, what to measure>
- Baseline / Target: <before/after measurement protocol>

### P0 — Must Ship

<one block per High finding, same format>

### P1 — Ship If Capacity Allows

<one block per Medium finding>

### Deferred

<one-line per Low finding>

## Compound Findings

<reproduce from synthesis.md if any>

## Definition of Done

- [ ] All Immediate Action and P0 tasks completed and verified
- [ ] Each task's verification step executed with the named Instruments instrument
- [ ] Before/after measurements recorded for each runtime-verified task
- [ ] No new Critical/High findings introduced by the remediations
- [ ] If any task touched cold launch: re-measured with Time Profiler from clean install
- [ ] If any task touched widget memory: re-measured against the family budget (~30 MB)
- [ ] If any task touched a retain cycle: confirmed deallocation via Leaks / Allocations Generations

## Sensitive-content warning

This report may reference internal file paths, identifiers, or fragments
of vendored dependencies. Treat as confidential. Instruments traces
(.trace bundles) may contain unredacted file paths, process names, and
stack frames — flag before sharing externally.

## Dependencies

- Tooling output: `$AUDIT_DIR/tooling-raw/`
- Intermediate files: `$AUDIT_DIR/{claude,synthesis,devils-advocate}.md`
```

## Outputs

- `$AUDIT_DIR/REPORT.md` exists, non-empty, contains the Implementation Plan with appropriate tiers populated

## Outgoing edges

- → `verify` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from report --to verify
```

## Failure modes

- Synthesis has zero findings → produce the single-task no-findings report; still transition to `verify`.
- Critical finding without a concrete remediation → write what's known and flag `**REMEDIATION INCOMPLETE**` in the task body; verify will still pass on artifact existence, but the user sees the gap.
