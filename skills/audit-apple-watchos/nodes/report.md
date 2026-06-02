# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` with watchOS-specific tier mapping (**Immediate Action** above P0 for Critical findings — watch reliability is a known sore spot, and Critical findings here represent crash-on-launch, workout-data-loss, or sync-death scenarios that compound badly with each release).

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`, `codex_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## watchOS sprint mapping override

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | **Immediate Action — fix before next watch app release** |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

"Immediate Action" here means: do not ship a watch app update with this finding outstanding. Common Critical examples on watchOS: a cold-launch OOM crash, a `WCSession` activation gap that breaks sync end-to-end, an `HKWorkoutSession` state-machine misuse that loses workout data mid-session. These all compound badly — a single bad release breaks the watch app for users who then uninstall.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Category** — one of the 12 watchOS categories
- **Location** — `path/to/file.swift:line` (the most specific available) or `<TargetName> Info.plist <key>` for plist findings
- **Anchor** — required (`Apple:WCSession`, `Apple:WidgetKit.accessoryCircular`, `Apple:HKLiveWorkoutBuilder`, `Apple:isLuminanceReduced`, `Apple:CLKComplicationDataSource`, `Apple:WKApplicationRefreshBackgroundTask`, etc.)
- **Platform** — usually `watchOS`; `Multi` when a paired iOS-side counterpart is involved
- **Issue** — clear description
- **Remediation** — concrete, specific (e.g. `Replace CLKComplicationDataSource with WidgetKit StaticConfiguration supporting accessoryCircular + accessoryRectangular; remove ComplicationController.swift and add WatchComplication.swift as a Widget target.`)
- **Verification** — for watchOS this should almost always be **on real hardware**: a real watch on the wrist, paired to a real iPhone, in the relevant scenario (locked phone, wrist-down for always-on, mid-workout for HealthKit). The simulator lies about memory pressure, always-on rendering, and paired reachability.

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — apple-watchos — <scope>, <date>`
- Task description: scope covered, 12 categories reviewed, tooling that ran, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Apple watchOS Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, tooling summary, total findings by severity, top
3 issues, reminder of audit's inherent limitations — many watchOS
findings require real-hardware verification because the simulator lies
about memory pressure, always-on rendering, and paired-iPhone
reachability. Cold-launch crashes only reproduce reliably on a real
watch under battery pressure.>

<If Critical findings exist:>
> **Critical findings present.** Apple-watchos Critical = do not ship
> a watch app update until the Immediate Action tasks are resolved.
> Watch app reliability compounds: a single bad release where the app
> crashes on cold launch or loses workout data leads to uninstalls
> that don't come back. See section below.

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
- $AUDIT_DIR/tooling-raw/ (watch-targets, complication-impl, wcsession-usage, healthkit-workout-usage, watch-info-plists, watchos-deployment)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/codex.md           <or "MISSING — single-agent run" if codex_status=failed>
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### Immediate Action — fix before next watch app release

<one block per Critical finding>

**Task: S### — <Category> — <Title>**
- Location: `path/to/file.swift:line` or `<TargetName> Info.plist <key>`
- Anchor: <anchor>
- Platform: <watchOS | Multi>
- Verification: <code | runtime>
- Issue: <description>
- Remediation: <specific fix>
- Verification step: <real-hardware scenario to reproduce + the fix to confirm — e.g. "On a Series 6+ paired to iPhone, lock the iPhone, leave on charger; verify the watch app cold-launch succeeds 5/5 trials.">
- Operational note: <e.g. "blocks next App Store release of the watch app" / "high crash-free-session impact">

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
- [ ] Each task's verification step executed on a real watch (not simulator)
- [ ] No new Critical/High findings introduced by the remediations
- [ ] If any task involved WCSession changes: verified end-to-end on both iPhone and Watch, with reachability toggled (phone locked, phone out of range, watch on Wi-Fi only)
- [ ] If any task involved complication changes: verified on at least three complication families (`.accessoryCircular`, `.accessoryRectangular`, `.accessoryInline`) on a real face
- [ ] If any task involved HKWorkoutSession changes: verified by completing a full workout (start → mid-workout-app-background → end → save) without data loss
- [ ] If any task involved always-on rendering: verified with the watch wrist-down for >5s observing `.privacySensitive()` redaction and `isLuminanceReduced` adaptation
- [ ] If any task involved background refresh: verified that scheduling stays under the per-day budget and `setTaskCompletedWithSnapshot(_:)` is called in every handler

## Sensitive-content warning

This report may reference paired-device identifiers, complication
push tokens, HealthKit-protected data categories, and watch app
bundle identifiers. Treat as confidential.

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
