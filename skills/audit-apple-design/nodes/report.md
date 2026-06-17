# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md`. **Default baseline sprint mapping** — design audits do not use an "Immediate Action" tier; Critical design findings land in P0.

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Apple-design sprint mapping (baseline)

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

Design remediations frequently depend on shared tokens, design-system components, or asset-catalog updates — note the task ordering in the hand-off. Animation, gesture, and material findings benefit from a Simulator review before signing off.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Category** — one of the 10 Apple design categories
- **Location** — `path/to/file.swift:line` (never just a function name)
- **HIG anchor** — required (e.g. `HIG:Navigation`, `HIG:Modality`)
- **Platform** — `iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`, `visionOS`, or `Multi`
- **Verification** — `code` (inspectable) or `runtime` (requires Simulator / device review)
- **Issue** — clear description anchored to the HIG principle
- **Remediation** — concrete, specific (never "fix the issue"); reference the stock SwiftUI / UIKit / AppKit control or modifier
- **Verification step** — code review for inspectable; Simulator screenshot / motion check / dark-mode toggle / Mac sidebar inspection for runtime

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — apple-design — <scope>, <date>`
- Task description: scope covered, 10 categories reviewed, date, reviewer agents
- Do not produce an empty sprint

## Output template

Write the per-run audit deliverable to `$AUDIT_DIR/REPORT.md`:

```markdown
# Apple Design Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, total findings by severity, top 3 issues,
reminder of audit's inherent limitations — LLM review against HIG
cannot validate visual rendering, animation timing, gesture feel, or
how a layout reads in motion. Findings marked `runtime` require
Simulator / on-device review.>

<If a project design system was detected:>
> **Project design system detected.** Design-system deviations dominate
> over generic HIG findings. Verify shared tokens / components are
> updated before per-screen fixes.

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
- $AUDIT_DIR/tooling-raw/STATUS.md (no Phase 1 tooling for this audit)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### P0 — Must Ship

<one block per Critical and High finding>

**Task: S### — <Category> — <Title>**
- Location: `path/to/file.swift:line`
- HIG: <anchor>
- Platform: <platform>
- Verification: <code | runtime>
- Issue: <description>
- Remediation: <specific fix referencing the stock control or modifier>
- Verification step: <code review for `code`; Simulator screenshot / motion check / dark-mode toggle for `runtime`>

### P1 — Ship If Capacity Allows

<one block per Medium finding, same format>

### Deferred

<one-line per Low finding>

## Compound Findings

<reproduce from synthesis.md if any>

## Definition of Done

- [ ] All P0 tasks completed and verified
- [ ] Each task's verification step executed
- [ ] If any task involved animation or motion changes: re-verified in Simulator with `accessibilityReduceMotion` ON and OFF
- [ ] If any task involved dark-mode fixes: re-verified by toggling appearance in Simulator
- [ ] If any task involved Mac / iPad sidebar or split view: re-verified across the target platforms
- [ ] If a project design system is in use: shared tokens / components updated before per-screen tasks landed

## Sensitive-content warning

This deliverable may reference internal file paths, identifiers, or
fragments of vendored dependencies. Treat as confidential before sharing.

## Dependencies

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

- Synthesis has zero findings → produce the single-task no-findings deliverable; still transition to `verify`.
- Critical finding without a concrete remediation → write what's known and flag `**REMEDIATION INCOMPLETE**` in the task body; verify will still pass on artifact existence, but the user sees the gap.
