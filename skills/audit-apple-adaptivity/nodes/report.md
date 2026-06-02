# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` using the baseline framework sprint mapping. Most findings here require Simulator verification at multiple device sizes + orientations + AX Dynamic Type sizes.

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`, `codex_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Sprint mapping

Baseline framework mapping applies (no audit-specific override):

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

Hand-off note: most findings require Simulator verification at multiple device sizes + orientations + AX Dynamic Type sizes. Specify the verification configuration per task.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Surface** — one of `SizeClass`, `Orientation`, `Multitasking`, `DynamicType`, `Windowing`, `DeviceSize`
- **Location** — `path/to/file.swift:line` (never just a function name)
- **Platform** — `iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`, `visionOS`, or `Multi`
- **Verification** — `code` or `runtime`
- **Issue** — clear description
- **Remediation** — concrete, specific (never "fix the issue")
- **Verification matrix** — for `runtime` findings: which device sizes, orientations, and AX Dynamic Type sizes need to be re-tested. At minimum: iPhone SE, iPhone Pro Max, iPad mini, iPad Pro 12.9"; AX1 + AX5 Dynamic Type; portrait + landscape; Split View on iPad

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — apple-adaptivity — <scope>, <date>`
- Task description: scope covered, 10 categories reviewed, declared platforms, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Apple Adaptivity Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, declared platforms, total findings by severity,
top 3 issues, reminder that adaptivity findings typically require
runtime Simulator verification across device sizes / orientations / AX
Dynamic Type sizes — static review cannot validate visual reflow.>

## Audit Summary

| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Total | N |

| Surface | Count |
|---|---|
<non-zero surfaces only>

| Platform | Count |
|---|---|
<non-zero platforms only>

Intermediate audit artifacts:
- $AUDIT_DIR/tooling-raw/STATUS.md (no tools ran — pure-LLM audit)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/codex.md           <or "MISSING — single-agent run" if codex_status=failed>
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### P0 — Must Ship

<one block per Critical and High finding>

**Task: S### — <Surface> — <Title>**
- Location: `path/to/file.swift:line`
- Surface: <SizeClass|Orientation|Multitasking|DynamicType|Windowing|DeviceSize>
- Platform: <platform>
- Verification: <code | runtime>
- Issue: <description>
- Remediation: <specific fix>
- Verification matrix: <device sizes + orientations + AX sizes to re-test>

### P1 — Ship If Capacity Allows

<one block per Medium finding, same format>

### Deferred

<one-line per Low finding>

## Compound Findings

<reproduce from synthesis.md if any>

## Definition of Done

- [ ] All P0 tasks completed and verified
- [ ] Each task's verification matrix executed in Simulator
- [ ] No new layout regressions introduced at AX1 or AX5 Dynamic Type
- [ ] iPad findings re-verified in Split View and (where applicable) Stage Manager
- [ ] Mac Catalyst / macOS / visionOS findings re-verified only where those targets are declared
- [ ] (If applicable) Snapshot test matrix extended to cover the previously-failing configurations

## Sensitive-content warning

This report may reference internal file paths and identifiers from the
project. Treat as confidential before sharing externally.

## Dependencies

- Intermediate files: `$AUDIT_DIR/{claude,codex,synthesis,devils-advocate}.md`
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
