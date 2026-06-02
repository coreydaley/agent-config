# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` with Apple-privacy-specific tier mapping (**Immediate Action** above P0 for Critical / Submission Blocker findings).

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`, `codex_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Apple-privacy sprint mapping override

| Finding Severity | Sprint Priority |
|---|---|
| **Critical (Submission Blocker)** | **Immediate Action — fix before next App Store submission** |
| High (Submission Risk) | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

For Apple apps, "Immediate Action" here means: do not submit to App Review until the blocker is resolved. Note this in the report's overview.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Concern** — one of: `PrivacyManifest`, `PurposeStrings`, `ATT`, `RequiredReason`, `SDKPrivacy`, `DataMinimization`, `Tracking`, `Permissions`
- **Submission Impact** — `Submission Blocker`, `Submission Risk`, `Compliance`, or `Best Practice`
- **Location** — `path/to/file.swift:line` or `path/to/PrivacyInfo.xcprivacy` (never just a function name)
- **Verification mode** — `code` or `runtime`
- **Issue** — clear description
- **Remediation** — concrete, specific (never "fix the issue")
- **Verification step** — App Store Connect Privacy Manifest validation report; on-device App Privacy Report; or a code-level inspection for `code`-mode findings

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — apple-privacy — <scope>, <date>`
- Task description: scope covered, 8 concerns reviewed, tooling that ran, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Apple Privacy Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, tooling summary, total findings by severity, top 3
issues, reminder of audit's inherent limitations — privacy is partly mechanical
(manifest present, purpose strings present) and partly about runtime behavior
matching declarations; static review catches the mechanical parts only.>

<If Critical / Submission Blocker findings exist:>
> ⚠️ **Submission Blocker(s) present.** Do NOT submit to App Review
> until the Immediate Action items below are resolved. App Review will
> reject deterministically on the conditions flagged.

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
- $AUDIT_DIR/tooling-raw/ (privacy-manifests, info-plist-privacy, third-party-sdks, idfa-att, required-reason-candidates)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/codex.md           <or "MISSING — single-agent run" if codex_status=failed>
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### Immediate Action — fix before next App Store submission

<one block per Critical / Submission Blocker finding>

**Task: S### — <Concern> — <Title>**
- Location: `path/to/file.swift:line` or `path/to/PrivacyInfo.xcprivacy`
- Concern: <PrivacyManifest | PurposeStrings | ATT | RequiredReason | SDKPrivacy | DataMinimization | Tracking | Permissions>
- Submission Impact: Submission Blocker
- Verification: <code | runtime>
- Issue: <description>
- Remediation: <specific fix>
- Verification step: <App Store Connect Privacy Manifest validation report after TestFlight build / on-device App Privacy Report / code inspection>
- Operational note: do NOT submit to App Review until resolved.

### P0 — Must Ship

<one block per High / Submission Risk finding, same format>

### P1 — Ship If Capacity Allows

<one block per Medium finding>

### Deferred

<one-line per Low finding>

## Compound Findings

<reproduce from synthesis.md if any>

## Definition of Done

- [ ] All Immediate Action and P0 tasks completed and verified
- [ ] Each task's verification step executed
- [ ] PrivacyInfo.xcprivacy validates clean in App Store Connect after TestFlight build
- [ ] App Privacy Report on a TestFlight build matches the manifest's declared data types and tracking domains
- [ ] Every required-reason API has its Apple-assigned reason code declared in NSPrivacyAccessedAPITypes
- [ ] All third-party SDKs on Apple's required list bundle their PrivacyInfo.xcprivacy AND signature
- [ ] If IDFA accessed: ATT prompt verified on-device; IDFA reads gated by authorization status
- [ ] No new findings introduced by the remediations

## Sensitive-content warning

This report may reference internal file paths, identifiers, declared data
practices, and tracking domains. Treat as confidential. App Privacy Report
exports may contain unredacted strings — flag before sharing externally.

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
- Submission Blocker without a concrete remediation → write what's known and flag `**REMEDIATION INCOMPLETE**` in the task body; verify will still pass on artifact existence, but the user sees the gap.
