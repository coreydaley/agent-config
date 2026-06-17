# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` with visionOS-specific tier mapping. **Critical findings land in "Immediate Action" — visionOS apps are scrutinized in App Review, and the Critical anchors here are runtime crashes, App Store rejections, or user-trapped-in-immersion outcomes.**

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Apple-visionos sprint mapping override

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | **Immediate Action — fix before next TestFlight build / App Review submission** |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

"Immediate Action" here means: do not submit a Vision Pro build to TestFlight or App Review with this finding outstanding. visionOS apps are scrutinized — the Critical anchors (hand-tracking without entitlement, trapped immersion, USDZ-induced OOM, missing PrivacyInfo required-reason) are documented rejection reasons.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Category** — one of the 12 visionOS categories
- **Location** — `path/to/file.swift:line` or `target/Info.plist` / `target/<Target>.entitlements` (never just "the immersive view")
- **Anchor** — required (`Apple:ImmersiveSpace`, `Apple:RealityView`, `Entitlement:com.apple.developer.arkit.hand-tracking`, `Apple:HoverEffect`, `File:Info.plist:NSHandsTrackingUsageDescription`, etc.)
- **Platform** — almost always `visionOS`; `Multi` only when a shared scene-type usage affects more than one platform
- **Issue** — clear description anchored to the visionOS API or entitlement
- **Remediation** — concrete, specific (e.g. `Add com.apple.developer.arkit.hand-tracking to MyApp.entitlements; add NSHandsTrackingUsageDescription to Info.plist with user-facing copy; verify in entitlements report after archive`)
- **Verification** — for visionOS this depends on the finding: `code` for entitlement / plist / file-size findings, `runtime` for gaze targeting, ImmersionStyle transitions, hand-tracking behavior, spatial audio rendering. Runtime findings require a real Vision Pro device — simulator does not reproduce eye / hand tracking.

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — apple-visionos — <scope>, <date>`
- Task description: scope covered, 12 categories reviewed, tooling that ran, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Apple visionOS Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, visionOS targets detected, total findings by
severity, top 3 issues, reminder of the audit's inherent limitations —
visionOS findings often require a real Vision Pro device to confirm;
the simulator approximates but does not reproduce eye / hand tracking,
ImmersionStyle transitions, or spatial audio rendering. The audit
catches the misconfig; only on-device review confirms the experience.>

<If Critical findings exist:>
> **Critical findings present.** visionOS apps are scrutinized at App
> Review; the Critical anchors here (hand-tracking without entitlement,
> trapped immersion, USDZ-induced OOM, missing PrivacyInfo
> required-reason) are documented rejection reasons. Do not submit a
> Vision Pro build to TestFlight or App Review until the Immediate
> Action tasks are resolved.

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
- $AUDIT_DIR/tooling-raw/ (visionos-targets, scene-types, arkit-providers, entitlements, info-plists, usdz-assets)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### Immediate Action — fix before next TestFlight build / App Review submission

<one block per Critical finding>

**Task: S### — <Category> — <Title>**
- Location: `path/to/file.swift:line` or `target/Info.plist` / `target/<Target>.entitlements`
- Anchor: <anchor>
- Platform: visionOS
- Verification: <code | runtime>
- Issue: <description>
- Remediation: <specific fix>
- Verification step: <code: inspect entitlements report after archive / runtime: enter the flow on Vision Pro device, confirm no crash / no trapped immersion / no OOM>
- Operational note: <e.g. "blocks App Review submission" / "crashes on entry to hand-tracking flow" / "user can't escape immersion">

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
- [ ] If any task involved entitlement changes: verified in the post-archive entitlements report (`codesign --display --entitlements -` against the built `.app`)
- [ ] If any task involved Info.plist purpose strings: verified the string is user-facing and accurate
- [ ] If any task involved PrivacyInfo.xcprivacy: re-generated the App Privacy Report from a real Vision Pro device and confirmed the required-reason entry appears
- [ ] If any task involved `ImmersiveSpace` lifecycle: verified entering and exiting the space on a real Vision Pro (simulator's immersion approximation is insufficient)
- [ ] If any task involved gaze targeting / hover effects: verified the gaze acquires the target with feedback on a real Vision Pro
- [ ] If any task involved USDZ loading: profiled the load with Instruments (Spatial Compute / RealityKit) — no main-thread freeze, no OOM termination
- [ ] If any task involved spatial audio: verified positional audio behavior on a real Vision Pro (simulator audio is non-spatial)

## Sensitive-content warning

This report may reference internal bundle identifiers, entitlement
strings, and purpose-string copy. Treat as confidential. The exported
`.xcarchive` and PrivacyInfo.xcprivacy may contain sensitive disclosure
metadata; review before sharing externally.

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
- Critical finding without a concrete remediation → write what's known and flag `**REMEDIATION INCOMPLETE**` in the task body.
