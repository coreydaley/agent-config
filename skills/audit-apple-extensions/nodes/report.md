# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` with extensions-specific tier mapping (**Immediate Action** above P0 for Critical findings — these affect every TestFlight user the extension surface touches: every push routed through NSE, every widget refresh, every Siri invocation against an App Intent).

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`, `codex_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Apple-extensions sprint mapping override

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | **Immediate Action — fix before next TestFlight build** |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

"Immediate Action" here means: do not promote a build to TestFlight Internal / External or App Store with this finding outstanding. Common Critical examples: an NSE that exceeds 24MB on a push the server actively sends, a Widget `getTimeline()` that blocks main thread, an extension target missing the App Groups entitlement the host carries, a Share Extension catchall activation rule.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Category** — one of the 12 extension categories
- **Location** — `path/to/file.swift:line` or `<ExtensionTargetName>/Info.plist:<key>` (never just "the extension")
- **Anchor** — required (`ExtensionType:WidgetKit`, `Apple:NSExtension`, `File:NSE/NotificationService.swift`, etc.)
- **Platform** — `iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`, `visionOS`, or `Multi`
- **Verification** — `code` (inspectable in the snapshot) or `runtime` (requires Instruments / "Add to Home Screen" + Console.app / XCUITest via Siri / real APNs send)
- **Issue** — clear description
- **Remediation** — concrete, specific (e.g. `Stream the attachment download to a file URL on disk in NotificationService.didReceive(...) instead of buffering Data; pair with serviceExtensionTimeWillExpire that calls contentHandler(bestAttemptContent) at the 27s mark`)
- **Verification step** — for extensions this is usually a *runtime* check: Instruments (Allocations / Time Profiler) on the extension process for memory budgets, an end-to-end APNs send via Push Notifications Console (or `xcrun simctl push`) for NSE / content-extension findings, "Add to Home Screen" + Console.app for widget findings, XCUITest invocation via Siri for App Intent findings, an end-to-end credential-save flow for AutoFill findings

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — apple-extensions — <scope>, <date>`
- Task description: scope covered, 12 categories reviewed, extension targets discovered, tooling that ran, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write the per-run audit deliverable to `$AUDIT_DIR/REPORT.md`:

```markdown
# Apple Extensions Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, list of detected extension targets and their
NSExtensionPointIdentifier, total findings by severity, top 3 issues,
reminder of audit's inherent limitations — extension findings often
require Instruments / a real APNs send / "Add to Home Screen" to
confirm magnitude; the audit catches the misconfig but only the
runtime confirms severity.>

<If Critical findings exist:>
> ⚠️ **Critical findings present.** Apple-extensions Critical = do
> not promote a build to TestFlight or App Store with the Immediate
> Action tasks outstanding. Common consequences: NSE silently reverts
> push to unmodified for users, widget renders blank, App Intent fails
> on Siri invocation, IPC silently broken between host and extension.

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
- $AUDIT_DIR/tooling-raw/ (appex-targets, entitlements, app-groups, info-plists, budgets)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/codex.md           <or "MISSING — single-agent run" if codex_status=failed>
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### Immediate Action — fix before next TestFlight build

<one block per Critical finding>

**Task: S### — <Category> — <Title>**
- Location: `path/to/file.swift:line` or `<ExtensionTarget>/Info.plist:<key>`
- Anchor: <anchor>
- Platform: <platform>
- Verification: <code | runtime>
- Issue: <description>
- Remediation: <specific fix>
- Verification step: <`Instruments (Allocations) on <extension>.appex` / `xcrun simctl push <device> <bundle-id> payload.json` / "Add to Home Screen, observe Console.app" / `XCUITest via Siri 'do <phrase>'` / etc.>
- Operational note: <e.g. "blocks every push that needs content mutation" / "blocks every widget refresh on Smart Stack" / "silently corrupts the user's file mirror">

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
- [ ] If any task involved NSE memory: re-verified via Instruments
      (Allocations) on the NSE process under a representative payload
- [ ] If any task involved widget timeline: re-verified via "Add to
      Home Screen" + Console.app filtered by the extension's subsystem
- [ ] If any task involved App Intent: re-verified via Siri invocation
      and via Spotlight Shortcuts surface
- [ ] If any task involved entitlement changes: re-verified via
      `codesign --display --entitlements -` against both the built host
      `.app` and the extension's `.appex` bundle (entitlement drift is
      only visible after signing)
- [ ] If any task involved App Group IPC: re-verified by writing from
      one side and reading from the other on a real device

## Sensitive-content warning

This deliverable may reference bundle identifiers, App Group
identifiers, team identifiers, push topic identifiers, and APNs
payload shapes. Treat as confidential before sharing. Avoid attaching
real production push payloads unless the team and operations are also
internal-only.

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
