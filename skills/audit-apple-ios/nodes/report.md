# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` with iOS-specific tier mapping (**Immediate Action** above P0 for Critical findings — these are App-Store-review flags, multitasking breakage, or silently-non-executing background tasks).

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`, `codex_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Apple-iOS sprint mapping override

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | **Immediate Action — fix before next iOS release** |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

"Immediate Action" here means: do not ship the next iOS release with this finding outstanding. Common Critical examples: `UIRequiresFullScreen=YES` on a non-game productivity app (App Review flag + Stage Manager users locked out), `BGTaskScheduler.register` called after `applicationDidFinishLaunching` (tasks silently never run), Live Activity Dynamic Island compact-state crash on a real iPhone 14 Pro+.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Category** — one of the 12 iOS categories
- **Location** — `path/to/file.swift:line` or `Info.plist:<key>` or `entitlements:<key>` (never just "the project")
- **Anchor** — required (`Plist:UIRequiresFullScreen`, `Apple:UIWindowSceneDelegate`, `Apple:BGTaskScheduler`, `Apple:DynamicIsland`, `Apple:AppShortcut`, etc.)
- **Platform** — `iOS`, `iPadOS`, or `Multi`
- **Verification** — `code` (inspectable from Info.plist key / source line) or `runtime` (requires on-device test — Stage Manager, Dynamic Island, Action Button, BGTask `_simulateLaunchForTaskWithIdentifier`)
- **Issue** — clear description
- **Remediation** — concrete, specific (e.g. `Set UIRequiresFullScreen = NO in <Target>/Info.plist; verify iPad multitasking by rotating + splitting + Stage Manager`)
- **Verification step** — for iOS, the verification depends on the finding type:
  - `Plist:UIRequiresFullScreen` change → rebuild + run on iPad simulator + verify Stage Manager works + verify Split View / Slide Over
  - `Apple:BGTaskScheduler` finding → rebuild + use lldb `e -l objc -- (void)[[BGTaskScheduler sharedScheduler] _simulateLaunchForTaskWithIdentifier:@"<id>"]` to verify the task is registered and runs
  - `Apple:DynamicIsland` finding → rebuild on a real iPhone 14 Pro+ (simulator does NOT render the Island)
  - `Apple:AppShortcut` finding → assign the app to the Action Button in Settings on a real iPhone 15 Pro+, then trigger the Action Button
  - `Apple:FocusFilterIntent` finding → enable a Focus that includes the app filter; verify content adapts
  - `Apple:UIWindowSceneDelegate` finding → verify cold-launch deep link with `xcrun simctl openurl booted <url>` against a freshly-killed app

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — apple-ios — <scope>, <date>`
- Task description: scope covered, 12 iOS categories reviewed, deployment target, device family, tooling that ran, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Apple iOS Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, deployment target, device family, tooling summary,
total findings by severity, top 3 issues, reminder of audit's inherent
limitations — many iOS findings (Dynamic Island rendering, Stage Manager
behavior, Action Button assignment, BGTask launch) require real
iPhone 14 Pro+ / iPhone 15 Pro+ / iPad-with-Magic-Keyboard hardware to
confirm; the simulator lies about these surfaces.>

<If Critical findings exist:>
> **Critical findings present.** Apple-iOS Critical = do not ship the
> next iOS release until the Immediate Action tasks are resolved. See
> section below.

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
- $AUDIT_DIR/tooling-raw/ (ios-deployment, ios-info-plists, scene-lifecycle, bg-task-scheduler, ui-background-modes, ipad-input, hardware-buttons, live-activity, live-text, focus)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/codex.md           <or "MISSING — single-agent run" if codex_status=failed>
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### Immediate Action — fix before next iOS release

<one block per Critical finding>

**Task: S### — <Category> — <Title>**
- Location: `path/to/file.swift:line` or `Info.plist:<key>`
- Anchor: <anchor>
- Platform: <platform>
- Verification: <code | runtime>
- Issue: <description>
- Remediation: <specific fix>
- Verification step: <iPad multitasking / Dynamic Island / Action Button / BGTask lldb / Focus filter / cold-launch URL — chosen per category as listed above>
- Operational note: <e.g. "blocks Stage Manager on iPad" / "user reports app never refreshes" / "App Review flags non-game app">

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
- [ ] If any task involved `UIRequiresFullScreen` / `UIApplicationSceneManifest` / `UISupportedInterfaceOrientations`: verified on iPad simulator with Stage Manager + Split View + Slide Over + rotation
- [ ] If any task involved `BGTaskScheduler`: verified via lldb `_simulateLaunchForTaskWithIdentifier` AND a real overnight scheduler run on a device left charging
- [ ] If any task involved Live Activity / Dynamic Island: verified on a real iPhone 14 Pro+ (simulator does not render the Island)
- [ ] If any task involved Lock Screen widgets: verified on the Lock Screen + StandBy mode (iOS 17+) on real hardware
- [ ] If any task involved Action Button: verified by assigning the app via Settings on a real iPhone 15 Pro+ and triggering the button
- [ ] If any task involved `FocusFilterIntent`: verified by adding the app filter to a Focus and toggling the Focus
- [ ] If any task involved scene lifecycle: verified cold-launch deep link from killed state via `xcrun simctl openurl booted <url>` AND notification-tap-from-killed-state on real hardware
- [ ] If any task involved iPad pointer / Pencil: verified with a real Magic Keyboard / Apple Pencil paired to the iPad

## Sensitive-content warning

This report may reference internal team IDs, bundle identifiers,
notification topics, BGTask identifiers, Live Activity push tokens,
and Focus filter intent payloads. Treat as confidential before
sharing.

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
- Critical finding without a concrete remediation → write what's known and flag `**REMEDIATION INCOMPLETE**` in the task body.
