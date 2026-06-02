# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` with notifications-specific tier mapping (**Immediate Action** above P0 for Critical findings — most Criticals are user-facing breakage and some block App Review).

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`, `codex_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Apple-notifications sprint mapping override

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | **Immediate Action — fix before next archive** |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

"Immediate Action" here means: do not archive a Release build for TestFlight / App Store with this finding outstanding. Common Critical examples: `aps-environment=development` in Release.entitlements (silent push failure on every Release device), `.criticalAlert` requested without the corresponding Apple-issued entitlement (App Review rejects), `UNUserNotificationCenter` delegate wired after first push delivery (first push lost on cold launch).

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Category** — one of the 12 notifications categories
- **Location** — `path/to/file:line` or `Entitlement <KEY> at <target>:<configuration>` (never just "the project")
- **Anchor** — required (`Apple:UNUserNotificationCenter`, `Entitlement:aps-environment`, `APNs:apns-push-type`, `Apple:INSendMessageIntent`, `Info.plist:UIBackgroundModes`, etc.)
- **Platform** — `iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`, `visionOS`, or `Multi`
- **Issue** — clear description
- **Remediation** — concrete, specific (e.g. `Set aps-environment = production in MyApp/Release.entitlements; re-archive; verify with codesign --display --entitlements - against the built .app`)
- **Verification** — for notifications this is usually a *sandbox APNs push* against the built app: `apns` CLI or `Knuff` against the device token, with `Console.app` filtered on `subsystem: com.apple.usernotifications`. For entitlement findings: `codesign --display --entitlements - <path/to/built.app>`. For authorization-flow findings: launch on a clean simulator and observe the OS prompt; for delegate-lifecycle findings: kill the app, schedule a local notification, cold-launch from the notification tap and confirm `didReceive` fires.

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — apple-notifications — <scope>, <date>`
- Task description: scope covered, 12 categories reviewed, tooling that ran, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Apple Notifications Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, tooling summary, total findings by severity, top
3 issues, reminder of audit's inherent limitations — notifications
correctness is best confirmed with a real sandbox APNs push to a real
device with Console.app capturing the usernotifications subsystem; the
audit catches the misconfig but the live push confirms the fix.>

<If Critical findings exist:>
> ⚠️ **Critical findings present.** Apple-notifications Critical = do
> not archive a Release build for TestFlight or App Store until the
> Immediate Action tasks are resolved. Several Criticals here block
> App Review on resubmission (criticalAlert without entitlement,
> aps-environment mismatch); others silently break push on every
> Release device. See section below.

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
- $AUDIT_DIR/tooling-raw/ (aps-environments, background-modes, un-center-calls, categories-and-actions, intents-donation, nse-targets, delegate-wiring, payload-strings)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/codex.md           <or "MISSING — single-agent run" if codex_status=failed>
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### Immediate Action — fix before next archive

<one block per Critical finding>

**Task: S### — <Category> — <Title>**
- Location: `path/to/file:line` or `Entitlement <KEY> at <target>:<config>`
- Anchor: <anchor>
- Platform: <platform>
- Verification: <code | runtime>
- Issue: <description>
- Remediation: <specific fix>
- Verification step: <sandbox APNs push via `apns` CLI / `codesign --display --entitlements - <app>` / cold-launch from notification tap / etc.>
- Operational note: <e.g. "blocks App Review on resubmission" / "silent push failure on every Release user">

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
- [ ] If any task involved entitlement changes: re-verified via `codesign --display --entitlements -` against a built+signed `.app` (host AND any NSE/NCE target)
- [ ] If any task involved authorization-flow changes: re-tested on a clean simulator / device (delete app + reinstall to clear cached authorization state)
- [ ] If any task involved server-side payload hygiene: live sandbox push via `apns` CLI confirms `apns-push-type`, `apns-priority`, `apns-topic`, and `apns-expiration` are accepted; payload body confirmed under 4KB
- [ ] If any task involved delegate-lifecycle changes: cold-launch-from-notification-tap test passes (kill app, schedule notification, tap from lock screen, confirm `didReceive` handler runs)
- [ ] If any task involved Communication Notifications: confirmed avatar renders on lock screen with `INSendMessageIntent` donated (vs the generic fallback)
- [ ] If `interruptionLevel: .timeSensitive` or `.critical` is used: the corresponding entitlement is present in Release.entitlements and signed in

## Sensitive-content warning

This report may reference APNs auth-key identifiers, push topics
(`apns-topic` matches the bundle id and is sensitive), team IDs, and
NSE / NCE entitlement contents. Treat as confidential. Push tokens,
APNs keys (`.p8`), and server-side push credentials must never appear
in the report — if they do, redact before sharing.

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

- Synthesis has zero findings → produce the single-task no-findings deliverable; still transition to `verify`.
- Critical finding without a concrete remediation → write what's known and flag `**REMEDIATION INCOMPLETE**` in the task body; verify will still pass on artifact existence, but the user sees the gap.
