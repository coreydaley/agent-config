# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` using the baseline P0/P1/Deferred tier mapping. **Migration Cost nuance**: P0 tasks with `Migration Cost=High` get a "Requires team alignment and design discussion before execution" note — module restructuring, state-ownership rewrites, and navigation overhauls shouldn't ship without team validation.

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling note)
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

Architecture findings are hypothesis-generating — there is no out-of-band patch story. Critical architectural debt still needs team validation before remediation.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Pattern** — the named pattern anchor
- **Location** — `path/to/file.swift:line` (never just a function name)
- **Platform** — `iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`, `visionOS`, or `Multi`
- **Alternative** — concrete alternative pattern to move toward
- **Migration Cost** — `Low`, `Medium`, or `High`
- **Issue** — clear description of the current pattern and why it's wrong here
- **Remediation** — concrete, specific (never "refactor this")
- **Verification** — how to confirm the migration landed (compile-time enforcement, test coverage, manual review of the pattern boundary)
- **Team alignment note** — required on P0 tasks with `Migration Cost=High`

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — apple-architecture — <scope>, <date>`
- Task description: scope covered, 10 categories reviewed, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Apple Architecture Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, total findings by severity, top 3 patterns surfaced,
reminder of audit's inherent limitations — architecture findings are
hypothesis-generating; each finding requires team validation before
execution, especially for High migration-cost items.>

## Audit Summary

| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Total | N |

| Pattern | Count |
|---|---|
<non-zero patterns only>

Intermediate audit artifacts:
- $AUDIT_DIR/tooling-raw/STATUS.md (no Phase 1 tooling for this audit)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/codex.md           <or "MISSING — single-agent run" if codex_status=failed>
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### P0 — Must Ship

<one block per Critical or High finding>

**Task: S### — <Pattern> — <Title>**
- Location: `path/to/file.swift:line`
- Pattern: <pattern anchor>
- Platform: <platform>
- Alternative: <concrete alternative pattern>
- Migration Cost: <Low | Medium | High>
- Issue: <description>
- Remediation: <specific migration steps>
- Verification: <how to confirm the migration landed>
- <If Migration Cost=High:> **Team alignment**: Requires team alignment and design discussion before execution.

### P1 — Ship If Capacity Allows

<one block per Medium finding, same format>

### Deferred

<one-line per Low finding>

## Compound Findings

<reproduce from synthesis.md if any>

## Definition of Done

- [ ] All P0 tasks completed and verified
- [ ] Each P0 task with Migration Cost=High had a team design discussion before execution
- [ ] Each task's verification step executed
- [ ] No regressions introduced (existing test suite green; pattern boundaries unchanged)
- [ ] Updated `Pattern` boundaries documented (e.g. new module README; updated `Package.swift` notes)

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
- P0 task without a concrete `Alternative` → write what's known and flag `**ALTERNATIVE INCOMPLETE**` in the task body; verify will still pass on artifact existence, but the user sees the gap.
