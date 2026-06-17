# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` using the baseline P0/P1/Deferred mapping.

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary — design has none)
- Walker state: `audit_dir`, `da_status`, `apple_project`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Design sprint mapping (baseline)

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

Design audits do not produce an "Immediate Action / out-of-band patch" tier — there is no analogue to a live-credential leak. Critical findings still ship next, just inside P0.

**Sprint ordering note** for the hand-off: some design remediations depend on shared tokens, components, or design-system updates. Review the task ordering before executing — applying a token change after a component refactor is wasted work.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Category** — one of the 7 design categories
- **Location** — `path/to/file.{html,css,tsx,swift,...}:line` (never just a component name)
- **Heuristic anchor** — required (project design system / cross-pattern consistency / Nielsen N#X / Apple HIG / Material Design)
- **Issue** — clear description distinguishing aesthetic opinion from user-impact evidence
- **Remediation** — concrete, specific (never "make it more consistent")
- **Verification** — design verification typically requires a built UI + visual comparison; note when token / component-library changes need design-system propagation

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — design — <scope>, <date>`
- Task description: scope covered, 7 categories reviewed, heuristic priority applied, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Design Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, total findings by severity, top 3 issues,
heuristic priority order used (note whether Apple HIG was promoted),
reminder of audit's inherent limitations — LLM review cannot validate
visual rendering, user perception, or dynamic interaction without
browser/device testing.>

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
- $AUDIT_DIR/tooling-raw/STATUS.md (design is pure-LLM; no tool output)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### P0 — Must Ship

<one block per Critical or High finding>

**Task: S### — <Category> — <Title>**
- Location: `path/to/file:line`
- Heuristic: <project design system / cross-pattern / Nielsen N#X / Apple HIG / Material Design>
- Issue: <description — distinguish aesthetic opinion from user-impact evidence>
- Remediation: <specific fix; reference design-system tokens / components if applicable>
- Verification step: <visual diff, design-system parity check, runtime check>

### P1 — Ship If Capacity Allows

<one block per Medium finding, same format>

### Deferred

<one-line per Low finding>

## Compound Findings

<reproduce from synthesis.md if any>

## Definition of Done

- [ ] All P0 tasks completed and verified
- [ ] Each task's verification step executed (visual diff or design-system parity check)
- [ ] No new design-system deviations introduced by the remediations
- [ ] If any task involved token / component-library changes: shared deps propagated and verified across affected surfaces
- [ ] If any task involved accessibility findings (contrast, touch targets, screen-reader behavior): re-verified with appropriate tooling (axe, VoiceOver, Accessibility Inspector)
- [ ] When auditing an Apple project: HIG-anchored findings dominate over Nielsen-anchored ones in the heuristic column

## Sensitive-content warning

This report may reference internal file paths and identifiers. Treat as
confidential before sharing externally.

## Dependencies

- Intermediate files: $AUDIT_DIR/{claude,synthesis,devils-advocate}.md
- Sprint ordering: design tasks that touch shared tokens or components
  should be ordered before tasks that depend on them.
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
- Critical/High finding without a concrete remediation → write what's known and flag `**REMEDIATION INCOMPLETE**` in the task body; verify will still pass on artifact existence, but the user sees the gap.
