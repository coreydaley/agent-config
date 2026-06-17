# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` using the baseline P0/P1/Deferred mapping.

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Web-accessibility sprint mapping (baseline)

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

Web-a11y has no "Immediate Action" tier — there's no analog to pulling a TestFlight build. Critical findings still fold into P0; the hand-off message calls out that some findings require runtime AT verification, so plan accordingly when scheduling those tasks.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **WCAG** — required (success criterion number like `1.4.3`, or `Best Practice`)
- **Level** — `A`, `AA`, `AAA`, or `BP`
- **Location** — `path/to/file.tsx:line` or `path/to/template.html:line` (never just a component name)
- **Verification mode** — `code` (inspectable from source) or `runtime` (requires browser + AT)
- **Issue** — clear description of the violation
- **Remediation** — concrete, specific (never "fix the issue"). Cite the ARIA/HTML pattern or WCAG technique where applicable.
- **Verification step** — for `code` items: a static check (lint rule, jest-axe test, source diff). For `runtime` items: an explicit AT script (e.g. "VoiceOver on macOS: Cmd+F5, navigate via VO+Right, confirm the modal title is announced before any form controls").

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — web-accessibility — <scope>, <date>`
- Task description: scope covered, 10 WCAG-anchored categories reviewed, tooling that ran, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Web Accessibility Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, tooling summary (axe/pa11y/lighthouse if they
ran, or "no TARGET_URL — source-level audit only"), total findings by
severity, top 3 issues, reminder of audit's inherent limitations:
static code review cannot fully validate dynamic behavior, screen
reader output, or focus management without runtime AT testing; not a
WCAG conformance certification.>

## Audit Summary

| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Total | N |

| WCAG Level | Count |
|---|---|
| A | N |
| AA | N |
| AAA | N |
| BP | N |

| Category | Count |
|---|---|
<non-zero categories only — Semantic structure, Images, Color/contrast,
Keyboard, Focus, ARIA, Forms, Live regions, Motion, Cognitive>

Intermediate audit artifacts:
- $AUDIT_DIR/tooling-raw/ (axe, pa11y, lighthouse, frontend-inventory)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### P0 — Must Ship

<one block per Critical and High finding>

**Task: S### — WCAG <criterion> (Level <A|AA|AAA|BP>) — <Title>**
- Location: `path/to/file.tsx:line`
- WCAG: <e.g. 1.4.3>
- Level: <A|AA|AAA|BP>
- Verification: <code | runtime>
- Issue: <description>
- Remediation: <specific fix; cite ARIA/HTML pattern or WCAG technique>
- Verification step: <static check for `code`; explicit AT script for `runtime`>

### P1 — Ship If Capacity Allows

<one block per Medium finding, same format>

### Deferred

<one-line per Low finding>

## Compound Findings

<reproduce from synthesis.md if any>

## Definition of Done

- [ ] All P0 tasks completed and verified
- [ ] Each `code`-verification task confirmed via source diff or
      automated a11y test (jest-axe, cypress-axe, axe-playwright)
- [ ] Each `runtime`-verification task confirmed via the specified AT
      script on at least one screen reader (VoiceOver / NVDA / JAWS /
      TalkBack)
- [ ] No new Critical/High findings introduced by the remediations
- [ ] If automated a11y tooling is in CI, the previously-failing rules
      are now passing
- [ ] Keyboard-only walkthrough of the affected flows completed end-to-end

## Sensitive-content warning

This report may reference internal file paths, identifiers, or fragments
of vendored dependencies. Treat as confidential. Some remediation
suggestions may quote user-visible copy; check for PII before sharing
externally.

## Dependencies

- Tooling output: `$AUDIT_DIR/tooling-raw/`
- Intermediate files: `$AUDIT_DIR/{claude,synthesis,devils-advocate}.md`

## Hand-off note

Findings marked `runtime` require browser and assistive-technology
testing to confirm the fix. Include AT testing time in the sprint that
tackles those tasks; do not mark them done from source inspection alone.
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
