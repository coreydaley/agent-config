# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` using the **default baseline sprint mapping** — no Immediate Action tier for web-responsive (Critical findings still get P0 priority; pulling a build is not the response model for a web frontend).

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`, `codex_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Sprint mapping (default baseline)

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

Web-responsive does not use the "Immediate Action" tier — there's no out-of-band patch model equivalent to pulling a TestFlight build. Critical responsive issues still belong in the next deploy.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Category** — one of the 10 web-responsive categories
- **Location** — `path/to/file.css:line` or `path/to/Component.tsx:line` (never just a class or component name)
- **Breakpoint** — affected viewport range(s), framework-specific names where applicable
- **Issue** — clear description
- **Remediation** — concrete, specific (never "make it responsive")
- **Verification** — for responsive design, this should be a **specific DevTools emulation target or physical device**. At minimum: Chrome DevTools at 375 px (iPhone), 768 px (iPad portrait), 1024 px (iPad landscape / small laptop). Physical device testing preferred where the finding is `Verification: runtime`.

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — web-responsive — <scope>, <date>`
- Task description: scope covered, 10 categories reviewed, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Web Responsive Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, total findings by severity, top 3 issues,
reminder that static code review cannot validate visual rendering —
Verification: runtime findings require Chrome DevTools device emulation
at 375 px, 768 px, 1024 px at minimum; physical device testing preferred.>

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
- $AUDIT_DIR/tooling-raw/STATUS.md
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/codex.md           <or "MISSING — single-agent run" if codex_status=failed>
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### P0 — Must Ship

<one block per Critical and High finding>

**Task: S### — <Category> — <Title>**
- Location: `path/to/file.css:line`
- Breakpoint: <e.g. xs,sm or md and below>
- Verification: <code | runtime>
- Issue: <description>
- Remediation: <specific fix>
- Verification step: <DevTools emulation target(s) or physical device(s)>

### P1 — Ship If Capacity Allows

<one block per Medium finding, same format>

### Deferred

<one-line per Low finding>

## Compound Findings

<reproduce from synthesis.md if any>

## Definition of Done

- [ ] All P0 tasks completed and verified
- [ ] Each task's verification step executed at minimum 375 px, 768 px, 1024 px
- [ ] Runtime-verification findings re-tested on at least one physical mobile device and one physical tablet
- [ ] No new responsive regressions introduced by the remediations
- [ ] If the project has Percy/Chromatic/visual-regression coverage: baselines updated

## Sensitive-content warning

This report may reference internal file paths, component names, and
class names. Treat as confidential before sharing externally.

## Dependencies

- Tooling output: `$AUDIT_DIR/tooling-raw/STATUS.md`
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
