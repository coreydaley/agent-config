# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` using the baseline P0/P1/Deferred sprint mapping. Architecture has no "Immediate Action" tier — there is no out-of-band patch story for design issues.

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (no-tooling marker)
- Walker state: `audit_dir`, `da_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Architecture sprint mapping (baseline)

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | **P0 — Must Ship** |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

**Migration Cost nuance**: P0 tasks with `Migration Cost=High` get a "Requires team alignment and design discussion before execution" note — architecture changes touching shared boundaries shouldn't ship without team validation.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Pattern/Principle** — the named architectural rule or trade-off (required)
- **Location** — `path/to/file:line` or directory boundary (never just a name)
- **Migration Cost** — `Low` | `Medium` | `High`
- **Issue** — clear description with the principle in tension
- **Alternative** — the concrete target design
- **Remediation** — specific steps to move from current to alternative (never "refactor this")
- **Verification** — how the team confirms the principle is now honored (often a code review checklist item, an import graph check, or a re-read of the affected module after the change)

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — architecture — <scope>, <date>`
- Task description: scope covered, 7 categories reviewed, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Architecture Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, total findings by severity, top 3 issues,
reminder of audit's inherent limitations — architectural "correctness"
is context-dependent; every finding is a hypothesis requiring team
validation before execution.>

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
- $AUDIT_DIR/tooling-raw/STATUS.md (no automated tooling — pure-LLM audit)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### P0 — Must Ship

<one block per Critical and High finding>

**Task: S### — <Title>**
- Location: `path/to/file:line`
- Pattern/Principle: <e.g. SOLID:SRP, Low Coupling>
- Migration Cost: <Low | Medium | High>
- Issue: <description>
- Alternative: <concrete target design>
- Remediation: <specific steps>
- Verification: <how to confirm the principle is now honored>
<if Migration Cost=High:>
- **Note: Requires team alignment and design discussion before execution.**

### P1 — Ship If Capacity Allows

<one block per Medium finding, same format>

### Deferred

<one-line per Low finding>

## Compound Findings

<reproduce from synthesis.md if any>

## Definition of Done

- [ ] All P0 tasks completed and verified
- [ ] Each task's verification step executed
- [ ] No new High/Critical findings introduced by the remediations
- [ ] P0 tasks with Migration Cost=High had team design review before execution
- [ ] Every shipped task cites the Pattern/Principle in its commit message or PR description

## Sensitive-content warning

This report may reference internal file paths and module names. Treat as
confidential before sharing externally.

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

- Synthesis has zero findings → produce the single-task no-findings report; still transition to `verify`.
- Critical/High finding without a concrete `Alternative` → evidence discipline violated; the synthesis should have dropped it. If it slipped through, flag `**ALTERNATIVE MISSING — INVALID FINDING**` in the task body; verify will still pass on artifact existence, but the user sees the gap.
