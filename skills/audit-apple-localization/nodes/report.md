# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able output artifact with the baseline framework tier mapping (no Apple-localization-specific override — Critical is rare and does not warrant out-of-band patching).

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`, `codex_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Apple-localization sprint mapping (framework baseline)

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship (top of P0) |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

There is no "Immediate Action" tier for localization — even a market-launch-blocking gap is "fix before the locale-launch release," not "out-of-band patch tonight."

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Surface** — one of the 10 Apple-localization surfaces
- **Location** — `path/to/file.swift:line` or `Localizable.xcstrings#<key>`
- **Verification mode** — `code` (inspectable) or `runtime` (Scheme → Run → Options → Application Language / Application Region)
- **Languages to test** — for `runtime` tasks, list specific languages (e.g. `ar-SA` for RTL, `pl` for plural categories, `de` for long-string overflow, `ja` for non-Latin script)
- **Issue** — clear description with the specific user-visible symptom
- **Remediation** — concrete (e.g. "move key to `Localizable.xcstrings`, add `%lld item(s)` with plural variations for zero/one/few/many/other")
- **Verification** — the test step that proves the fix (Simulator language toggle + screenshot diff is the canonical localization verification)

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — apple-localization — <scope>, <date>`
- Task description: scope covered, 10 surfaces reviewed, tooling that ran, declared target languages, date, reviewer agents
- Do not produce an empty sprint

## Output artifact template

The orchestrator writes the artifact at `$AUDIT_DIR/REPORT.md`. Structure:

```
# Apple Localization Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, declared target languages, tooling summary, total
findings by severity, top 3 issues, reminder of audit's inherent limitations
— static review cannot judge translation quality; `runtime` findings need
Simulator language testing.>

## Audit Summary

| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Total | N |

| Surface | Count |
|---|---|
<non-zero surfaces only>

Declared target languages (from `CFBundleLocalizations`): <list>

Intermediate audit artifacts:
- $AUDIT_DIR/tooling-raw/ (string-catalogs, legacy-strings, stringsdict, supported-languages, lproj-dirs, grep-candidates)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/codex.md           <or "MISSING — single-agent run" if codex_status=failed>
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### P0 — Must Ship

<one block per Critical/High finding; Critical findings appear first within P0>

**Task: S### — <Surface> — <Title>**
- Location: `path/to/file.swift:line` (or `Localizable.xcstrings#<key>`)
- Surface: <surface>
- Verification mode: <code | runtime>
- Languages to test (runtime only): <e.g. `ar-SA, he-IL, pl, de, ja`>
- Issue: <description with user-visible symptom>
- Remediation: <specific fix>
- Verification step: <Simulator language toggle + screenshot diff, or static re-check>

### P1 — Ship If Capacity Allows

<one block per Medium finding, same format>

### Deferred

<one-line per Low finding>

## Compound Findings

<reproduce from synthesis.md if any>

## Definition of Done

- [ ] All P0 tasks completed and verified
- [ ] Each `runtime` task verified in Simulator across the listed languages
- [ ] No new localization regressions introduced by remediations
- [ ] If String Catalog migration occurred: all keys re-flowed and "needs review" flags cleared
- [ ] If RTL findings remediated: visual smoke test in `ar-SA` on the affected screens
- [ ] `CFBundleLocalizations` matches the languages actually shipped in `*.lproj` / `*.xcstrings`

## Sensitive-content warning

This artifact may reference internal file paths and identifiers. Treat as
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

- Synthesis has zero findings → produce the single-task no-findings artifact; still transition to `verify`.
- Critical finding without a concrete remediation → write what is known and flag `**REMEDIATION INCOMPLETE**` in the task body; verify will still pass on artifact existence, but the user sees the gap.
