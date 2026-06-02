# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` with the baseline sprint-tier mapping. **Apple-persistence-specific override:** migration findings are sequencing-sensitive — shipped migrations can't be safely reverted, so the remediation must be forward-compatible.

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`, `codex_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Sprint mapping

Baseline framework mapping applies:

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | **Immediate Action — fix before next release** |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

For migration findings, "fix before next release" must be read as: **forward-compatible fix only**. A migration that has already shipped to users cannot be safely reverted; the next migration must accept the on-disk state from the shipped one and move forward.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Stack** — `SwiftData`, `CoreData`, `GRDB`, `SQLite`, `Realm`, `CloudKit-direct`, or `UserDefaults`
- **Concern** — one of: `Schema`, `Migration`, `Threading`, `Fetch`, `Predicate`, `Batch`, `Sync`, `Conflict`, `Storage`, `Backup`
- **Location** — `path/to/file.swift:line` (or `*.xcdatamodeld/.../contents:entity` for model-file findings; never just a function name)
- **Verification mode** — `code` (inspectable) or `runtime` (needs SQL debug logging, Instruments fetch profiling, or migration dry-run on a real-data snapshot)
- **Issue** — clear description
- **Remediation** — concrete, specific (never "fix the issue")
- **Verification step** — for persistence, this is often a runtime check: enable `-com.apple.CoreData.SQLDebug 1`, profile fetches in Instruments, run the migration against a snapshot of real user data, or check CloudKit schema state in the developer console
- **Forward-compatibility note** (Migration findings only) — what the next migration must accept from the already-shipped state
- **CloudKit environment note** (Sync findings only) — dev vs production schema-deploy state

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — apple-persistence — <scope>, <date>`
- Task description: scope covered, 10 categories reviewed, persistence stack(s) detected, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Apple Persistence Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, persistence stack(s) in use, total findings by
severity, top 3 issues, reminder of audit's inherent limitations —
schema design is partly subjective; performance findings need runtime
verification (SQL debug logging, Instruments) to confirm magnitude;
migration findings need a real-data snapshot to dry-run against.>

<If Critical findings include migrations:>
> Critical migration findings present. Shipped migrations cannot be
> reverted — remediation must be forward-compatible. See Immediate
> Action section below.

## Audit Summary

| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Total | N |

| Concern | Count |
|---|---|
<non-zero concerns only>

Intermediate audit artifacts:
- $AUDIT_DIR/tooling-raw/ (persistence-stack, coredata-models, fetch-patterns, threading-patterns, userdefaults-usage)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/codex.md           <or "MISSING — single-agent run" if codex_status=failed>
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### Immediate Action — fix before next release

<one block per Critical finding>

**Task: S### — <Stack> / <Concern> — <Title>**
- Location: `path/to/file.swift:line`
- Verification: <code | runtime>
- Issue: <description>
- Remediation: <specific fix>
- Verification step: <runtime check — e.g. enable -com.apple.CoreData.SQLDebug 1; dry-run migration against snapshot>
- Forward-compatibility note (Migration only): <what the next migration must accept>
- CloudKit environment note (Sync only): <dev vs production deploy state>

### P0 — Must Ship

<one block per High finding, same format>

### P1 — Ship If Capacity Allows

<one block per Medium finding>

### Deferred

<one-line per Low finding>

## Compound Findings

<reproduce from synthesis.md if any>

## Definition of Done

- [ ] All Immediate Action and P0 tasks completed and verified
- [ ] Each task's verification step executed (SQL debug log, Instruments
      trace, migration dry-run output, or CloudKit dashboard screenshot
      pinned to the task)
- [ ] Migration tasks: forward-compatibility verified against a snapshot
      of real (or representative) user data
- [ ] CloudKit tasks: schema state confirmed in the target environment
      (dev vs production) before the build ships
- [ ] No new Critical/High findings introduced by the remediations
- [ ] If any task involved Delete Account: verified local store AND
      CloudKit mirror are wiped on the same code path

## Sensitive-content warning

This report may reference internal file paths, identifiers, or fragments
of schema. Treat as confidential. Database snapshots used for migration
dry-runs may contain real user data — handle per the project's data-
handling policy.

## Dependencies

- Tooling output: `$AUDIT_DIR/tooling-raw/`
- Intermediate files: `$AUDIT_DIR/{claude,codex,synthesis,devils-advocate}.md`
```

## Outputs

- `$AUDIT_DIR/REPORT.md` exists, non-empty, contains the Implementation Plan with appropriate tiers populated

## Outgoing edges

- -> `verify` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from report --to verify
```

## Failure modes

- Synthesis has zero findings -> produce the single-task no-findings report; still transition to `verify`.
- Critical migration finding without a concrete forward-compatible remediation -> write what's known and flag `**REMEDIATION INCOMPLETE — forward-compatibility unresolved**` in the task body; verify will still pass on artifact existence, but the user sees the gap.
