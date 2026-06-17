# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` with Apple-security-specific tier mapping (**Immediate Action** above P0 for Critical findings).

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Apple-security sprint mapping override

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | **Immediate Action — fix before next release / out-of-band patch** |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

For Apple apps, "Immediate Action" frequently means: pull the build from TestFlight, hotfix, re-submit. Note this in the report's overview.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Category** — one of the 12 Apple security categories
- **Location** — `path/to/file.swift:line` (never just a function name)
- **CWE/Apple anchor** — required (`CWE-522 / Apple:Keychain`)
- **Platform** — `iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`, `visionOS`, or `Multi`
- **Issue** — clear description
- **Remediation** — concrete, specific (never "fix the issue")
- **Verification** — for security, this should be a *negative test* (try the exploit, confirm it fails). For Apple-specific runtime verification: `codesign --display --entitlements -`, Console.app for `os_log`, Xcode Static Analyzer

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — apple-security — <scope>, <date>`
- Task description: scope covered, 12 categories reviewed, tooling that ran, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Apple Security Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, tooling summary, total findings by severity, top 3
issues, reminder of audit's inherent limitations — Apple SAST is thinner
than the web ecosystem; many findings require runtime verification.>

<If Critical findings exist:>
> ⚠️ **Critical findings present.** Apple-security Critical = pull the
> TestFlight build / out-of-band patch. See Immediate Action section
> below.

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
- $AUDIT_DIR/tooling-raw/ (gitleaks, semgrep, xcodebuild-analyze, entitlements)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### Immediate Action — fix before next release / out-of-band patch

<one block per Critical finding>

**Task: S### — <Category> — <Title>**
- Location: `path/to/file.swift:line`
- CWE/Apple: <anchor>
- Platform: <platform>
- Verification: <code | runtime>
- Issue: <description>
- Remediation: <specific fix>
- Verification step: <negative test or runtime check>
- Operational note: <e.g. "pull TestFlight build before re-submit">

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
- [ ] Each task's verification step executed
- [ ] No new Critical/High findings introduced by the remediations
- [ ] If any task involved Keychain changes: verified via runtime read on a built+signed app
- [ ] If any task involved entitlement changes: re-verified via `codesign --display --entitlements -`
- [ ] If any task involved `os_log` privacy changes: re-verified via Console.app
- [ ] (If applicable) TestFlight build pulled and hotfix re-submitted

## Sensitive-content warning

This report may reference internal file paths, identifiers, or fragments
of vendored dependencies. Treat as confidential. Apple-specific:
crash-report sysdiagnose bundles may contain unredacted strings — flag
before sharing externally.

## Dependencies

- Tooling output: `$AUDIT_DIR/tooling-raw/`
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
- Critical finding without a concrete remediation → write what's known and flag `**REMEDIATION INCOMPLETE**` in the task body; verify will still pass on artifact existence, but the user sees the gap.
