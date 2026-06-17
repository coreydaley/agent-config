# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` with App-Store-Review-specific tier mapping (**Submission Blocker** above P0 for Critical / Will Reject findings).

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## App-Store-Review sprint mapping override

Critical findings (Will Reject) tier into a **Submission Blocker** section above P0. These prevent App Store submission:

| Finding Severity | Sprint Priority |
|---|---|
| **Critical (Will Reject)** | **Submission Blocker — fix before next App Store submission** |
| High (Likely Reject) | P0 — Must Ship |
| Medium (Risk) | P1 — Ship If Capacity Allows |
| Low (Best Practice) | Deferred |

For Apple apps, "Submission Blocker" means: the build will be rejected by App Review if submitted as-is. Hold the submission until these are cleared. Note this in the report's overview.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Guideline** — the most-specific Review Guideline subsection (e.g. `2.1`, `3.1.2`, `4.8`, `5.1.1`)
- **Section** — `1. Safety` | `2. Performance` | `3. Business` | `4. Design` | `5. Legal`
- **Rejection Likelihood** — `Will Reject` | `Likely Reject` | `Risk` | `Best Practice`
- **Location** — `path/to/file.swift:line`, `Info.plist:<key>`, `fastlane/metadata/...`, or `App Store Connect: <field>` (never just a function name)
- **Verification** — `code` (inspectable) or `runtime` (App Store Connect / TestFlight / device review)
- **Issue** — clear description, citing the Guideline language where helpful
- **Remediation** — concrete, specific (never "fix the issue")
- **Verification step** — for App Store Review, this often means a runtime check on a built+signed app, a TestFlight build, or an App Store Connect metadata review

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — apple-app-store-review — <scope>, <date>`
- Task description: scope covered, 5 sections reviewed, tooling that ran, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Apple App Store Review Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, tooling summary, total findings by severity, top 3
issues, reminder of audit's inherent limitations — App Review enforcement
varies in practice; reviewers exercise judgment; the Guidelines update
frequently. Treat findings as "high likelihood of rejection" rather than
"Apple will definitely reject".>

<If Submission Blocker findings exist:>
> ⚠️ **Submission Blocker findings present.** Do not submit the current
> build to App Review. See Submission Blocker section below.

## Audit Summary

| Severity | Rejection Likelihood | Count |
|---|---|---|
| Critical | Will Reject | N |
| High | Likely Reject | N |
| Medium | Risk | N |
| Low | Best Practice | N |
| Total | | N |

| Section | Count |
|---|---|
<non-zero sections only>

Intermediate audit artifacts:
- $AUDIT_DIR/tooling-raw/ (Info.plist, Privacy Manifest, StoreKit usage, auth/push, placeholder content)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### Submission Blocker — fix before next App Store submission

<one block per Critical / Will Reject finding>

**Task: S### — Guideline <X.Y.Z> — <Title>**
- Guideline: <X.Y.Z>
- Section: <1. Safety | 2. Performance | 3. Business | 4. Design | 5. Legal>
- Rejection Likelihood: Will Reject
- Location: `path/to/file.swift:line` or `Info.plist:<key>` or `App Store Connect: <field>`
- Verification: <code | runtime>
- Issue: <description, citing Guideline language>
- Remediation: <specific fix>
- Verification step: <runtime check on built app, TestFlight, App Store Connect metadata review>
- Operational note: <e.g. "do not submit until cleared; if already submitted, withdraw">

### P0 — Must Ship

<one block per High / Likely Reject finding, same format>

### P1 — Ship If Capacity Allows

<one block per Medium / Risk finding>

### Deferred

<one-line per Low / Best Practice finding>

## Compound Findings

<reproduce from synthesis.md if any>

## Definition of Done

- [ ] All Submission Blocker and P0 tasks completed and verified
- [ ] Each task's verification step executed
- [ ] No new Will Reject / Likely Reject findings introduced by the remediations
- [ ] If any task involved IAP / subscription changes: verified via StoreKit Configuration in Xcode and on TestFlight
- [ ] If any task involved metadata changes: verified in App Store Connect against the shipping build
- [ ] If any task involved Sign in with Apple: button ordering verified per HIG; flow tested end-to-end
- [ ] If any task involved push notifications: payload reviewed for promotional content; opt-in confirmed
- [ ] If category-specific (Kids, Health, HealthKit, Location): applicable Section 5 sub-rules re-verified
- [ ] If `audit-apple-privacy` has been run, its Section 5.1.1 findings cross-referenced

## Sensitive-content warning

This report may reference internal file paths, identifiers, and App Store Connect metadata fragments. Treat as confidential before sharing externally.

## Dependencies

- Tooling output: `$AUDIT_DIR/tooling-raw/`
- Intermediate files: `$AUDIT_DIR/{claude,synthesis,devils-advocate}.md`
- App Store Review Guidelines (current): https://developer.apple.com/app-store/review/guidelines/
```

## Outputs

- `$AUDIT_DIR/REPORT.md` exists, non-empty, contains the Implementation Plan with appropriate tiers populated (Submission Blocker / P0 / P1 / Deferred)

## Outgoing edges

- → `verify` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from report --to verify
```

## Failure modes

- Synthesis has zero findings → produce the single-task no-findings report; still transition to `verify`.
- Critical finding without a concrete remediation → write what's known and flag `**REMEDIATION INCOMPLETE**` in the task body; verify will still pass on artifact existence, but the user sees the gap.
