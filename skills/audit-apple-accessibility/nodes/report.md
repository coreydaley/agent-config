# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` using the baseline sprint-tier mapping. The old subagent's hand-off note specifies: many Apple accessibility findings require runtime verification (VoiceOver / Accessibility Inspector / Switch Control / Voice Control / Full Keyboard Access) — include this in task execution for items marked `runtime`.

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (records the no-tooling status)
- Walker state: `audit_dir`, `da_status`, `codex_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Sprint mapping

Baseline mapping (no audit-specific override):

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Title** — short, action-oriented
- **Location** — `path/to/file.swift:line` (never just a function name)
- **API/Standard** — the Apple API or HIG principle (e.g. `SwiftUI:.accessibilityLabel`, `HIG:TouchTarget`)
- **Platform** — `iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`, `visionOS`, or `Multi`
- **Verification mode** — `code` (inspectable in source) or `runtime` (requires Accessibility Inspector / VoiceOver / Switch Control / Voice Control / FKA on a built app)
- **Issue** — clear description
- **Remediation** — concrete, specific (never "fix the issue")
- **Verification step** — for `runtime` items, name the assistive technology and platform combo (e.g. "VoiceOver on iOS 17 device, AX5 Dynamic Type setting"); for `code` items, the diff to inspect

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — apple-accessibility — <scope>, <date>`
- Task description: scope covered, 10 categories reviewed, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Apple Accessibility Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, total findings by severity, top 3 issues,
reminder of audit's inherent limitations — static review cannot
validate VoiceOver output, focus behavior, gesture recognition, or
visual-settings interactions without runtime testing in Xcode's
Accessibility Inspector and on-device with VoiceOver / Switch Control
/ Voice Control / Full Keyboard Access. Findings marked `runtime`
require these tools to confirm.>

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
- $AUDIT_DIR/codex.md           <or "MISSING — single-agent run" if codex_status=failed>
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### P0 — Must Ship

<one block per Critical and High finding>

**Task: S### — <Title>**
- Location: `path/to/file.swift:line`
- API/Standard: <anchor>
- Platform: <platform>
- Verification: <code | runtime>
- Issue: <description>
- Remediation: <specific fix>
- Verification step: <runtime AT + platform combo, or code diff to inspect>

### P1 — Ship If Capacity Allows

<one block per Medium finding, same format>

### Deferred

<one-line per Low finding>

## Compound Findings

<reproduce from synthesis.md if any>

## Definition of Done

- [ ] All P0 tasks completed and verified
- [ ] Each task's verification step executed
- [ ] No new Critical/High findings introduced by the remediations
- [ ] Runtime-verification items confirmed on-device with the named
      assistive technology (VoiceOver / Switch Control / Voice Control
      / Full Keyboard Access / Accessibility Inspector)
- [ ] When platform list includes macOS: Mac-specific patterns (Full
      Keyboard Access, custom NSView accessibility, AppKit
      accessibility APIs) reviewed
- [ ] Dynamic Type spot-checks at AX5 for any task touching typography

## Sensitive-content warning

This report references internal file paths and identifiers. Treat as
confidential before sharing externally.

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
- Critical/High finding without a concrete remediation → write what's known and flag `**REMEDIATION INCOMPLETE**` in the task body; verify will still pass on artifact existence, but the user sees the gap.
