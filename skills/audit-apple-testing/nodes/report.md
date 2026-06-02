# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` with the baseline tier mapping (Critical → P0 / Must Ship). Apple-testing findings rarely warrant out-of-band patches the way security Criticals do — Criticals here mean "a primary path has no regression coverage," not "ship a hotfix tonight."

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`, `codex_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Sprint mapping (baseline)

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

No "Immediate Action" tier for testing audits — these gaps require new tests, not hotfixes. The exception is a tautological-test Critical that's hiding an active production bug; flag that separately in the overview.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **TestLayer** — one of `Unit`, `Integration`, `UI`, `Preview`, `Snapshot`, `Performance`, `Fixture`
- **Framework** — `XCTest`, `Swift Testing`, `SwiftUI Preview`, `XCUITest`, `Snapshot library`, or `Other`
- **Location** — `path/to/file.swift:line` (production file lacking coverage, plus the proposed test file path)
- **Verification mode** — `code` or `runtime`
- **Issue** — clear description
- **Remediation** — concrete (write test for X covering Y assertion)
- **Verification** — **mutation check**: temporarily break the production code (or remove the assertion), confirm the test fails. "Test added" without this is insufficient. Plus: the test runs in CI on every PR, not just locally.

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — apple-testing — <scope>, <date>`
- Task description: scope covered, 10 categories reviewed, tooling that ran, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Apple Testing Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, tooling summary, total findings by severity, top 3
gaps, reminder of audit's inherent limitations — test quality is partly
objective (mutation check) and partly judgment.>

<If Critical findings include a tautological test on a production path:>
> ⚠️ **Tautological-test Critical present.** A test currently passes
> regardless of code behavior on a production path. Treat this like a
> latent bug — the production code may already be broken.

## Audit Summary

| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Total | N |

| TestLayer | Count |
|---|---|
<non-zero layers only>

Intermediate audit artifacts:
- $AUDIT_DIR/tooling-raw/ (test-inventory.txt, optional swift-test.log, optional COVERAGE-SOURCE.md)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/codex.md           <or "MISSING — single-agent run" if codex_status=failed>
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### P0 — Must Ship

<one block per Critical and High finding>

**Task: S### — <TestLayer> — <Title>**
- Location: `path/to/file.swift:line` (production) → `Tests/.../...Tests.swift` (proposed)
- TestLayer: <Unit | Integration | UI | Preview | Snapshot | Performance | Fixture>
- Framework: <XCTest | Swift Testing | XCUITest | SwiftUI Preview | Snapshot library | Other>
- Verification mode: <code | runtime>
- Issue: <description>
- Remediation: <write test for X covering Y assertion>
- Verification: <mutation check: break production, confirm test fails; AND test runs in CI on every PR>

### P1 — Ship If Capacity Allows

<one block per Medium finding, same format>

### Deferred

<one-line per Low finding>

## Compound Findings

<reproduce from synthesis.md if any>

## Definition of Done

- [ ] All P0 tasks have tests added AND mutation-checked (production temporarily broken, test fails as expected)
- [ ] All new tests run in CI on every PR (not just locally)
- [ ] No new tautological tests introduced (every assertion would fail if the production logic changed)
- [ ] If any task involved Swift Testing migration: both XCTest and Swift Testing pass in the same test bundle
- [ ] If any task involved XCUITest: tests use accessibility identifiers, not localized text matching
- [ ] If any task involved snapshot testing: light + dark + AX text size variants present
- [ ] Test plan / scheme configurations cover the new tests in CI

## Dependencies

- Tooling output: `$AUDIT_DIR/tooling-raw/`
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
