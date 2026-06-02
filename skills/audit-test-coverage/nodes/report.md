# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md`. Test-coverage uses the **default baseline sprint mapping** (no Immediate Action tier — coverage gaps don't warrant out-of-band patches; Critical findings still land at P0).

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

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Category** — one of `Gap`, `Pyramid`, `Quality`, `Missing-Layer`
- **Location** — `path/to/file.ext:line` (never just a function name)
- **Recommended layer** — `unit` / `integration` / `e2e`. **Required.** Adding tests at the wrong layer can be worse than no test.
- **Issue** — clear description
- **Remediation** — concrete, specific (never "add tests")
- **Verification** — must demand a *measurable outcome*: a specific coverage number, a named test scenario that would now pass, or a **mutation check** (temporarily break the covered code and confirm the new test fails). "Tests added" is insufficient.

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — test-coverage — <scope>, <date>`
- Task description: scope covered, 4 categories reviewed (Gap, Pyramid, Quality, Missing-Layer), tooling that ran, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Test Coverage Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, languages detected, coverage tools that ran with
overall %, total findings by severity, top 3 issues, reminder of audit's
inherent limitation — line/branch coverage measures execution, not
correctness.>

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
| Gap | N |
| Pyramid | N |
| Quality | N |
| Missing-Layer | N |

Intermediate audit artifacts:
- $AUDIT_DIR/tooling-raw/ (coverage logs per language)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/codex.md           <or "MISSING — single-agent run" if codex_status=failed>
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### P0 — Must Ship

<one block per Critical and High finding>

**Task: S### — <Category> — <Title>**
- Location: `path/to/file.ext:line`
- Recommended layer: <unit | integration | e2e>
- Issue: <description>
- Remediation: <specific fix>
- Verification step: <measurable outcome — coverage number, named scenario, OR mutation check>

### P1 — Ship If Capacity Allows

<one block per Medium finding, same format>

### Deferred

<one-line per Low finding>

## Compound Findings

<reproduce from synthesis.md if any>

## Definition of Done

- [ ] All P0 tasks completed and verified
- [ ] Each task's verification step executed and produced a measurable outcome
- [ ] No coverage regressions vs. baseline reported in tooling-raw/
- [ ] (If applicable) CI integrated to fail on coverage regression
- [ ] (If Missing-Layer fixes shipped) New layer (integration / e2e / contract) wired into CI

## Sensitive-content warning

This report references internal file paths and identifiers. Treat as
confidential before sharing externally.

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
- A task missing a Recommended layer or measurable Verification → flag `**LAYER UNSPECIFIED**` or `**VERIFICATION INCOMPLETE**` in the task body; verify still passes on artifact existence, but the user sees the gap.
