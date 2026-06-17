# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` with deep-links-specific tier mapping (**Immediate Action** above P0 for Critical findings — these are either user-visible breakage of every marketing link, or RCE-class deep-link exploit chains, both unacceptable on a live build).

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Apple-deeplinks-continuity sprint mapping override

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | **Immediate Action — fix before relying on the deep-link surface** |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

"Immediate Action" here means: do not run marketing-link campaigns, do not advertise Universal Link support on the website, and (for RCE-class findings) do not ship the build at all until the Immediate Action tasks are resolved. Common Critical examples: deep-link handler that passes user-controlled URL to `evaluateJavaScript`, URL scheme that triggers a state change without re-auth, AASA missing on the production domain, Associated Domains entitlement that doesn't match production hostname.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Category** — one of the 12 deep-links categories
- **Location** — `path/to/file.swift:line`, `Entitlement:<file>:<line>`, or `Info.plist:<key>` (never just "the project")
- **Anchor** — required (`Entitlement:com.apple.developer.associated-domains`, `Apple:NSUserActivity`, `Apple:CSSearchableIndex`, `Plist:CFBundleURLTypes`, etc.)
- **Platform** — `iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`, `visionOS`, or `Multi`
- **Issue** — clear description
- **Remediation** — concrete, specific (e.g. `Remove '?mode=developer' suffix from applinks:foo.com in MyApp.entitlements:14; re-archive Release; verify with swcutil dl -d foo.com on a TestFlight device`)
- **Verification** — for deep-links this is usually a runtime check: `swcutil dl -d <domain>` on an iOS device with Developer mode enabled, `curl -I https://<domain>/.well-known/apple-app-site-association` for AASA reachability, `xcrun simctl openurl booted <url>` for scheme testing, tap-a-link-in-Notes for Universal Link cold-launch, manual Settings → Siri & Search inspection for Spotlight items.

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — apple-deeplinks-continuity — <scope>, <date>`
- Task description: scope covered, 12 categories reviewed, tooling that ran, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Apple Deep Links & Continuity Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, tooling summary, total findings by severity,
top 3 issues, reminder of audit's inherent limitations — deep-link
findings frequently require a real `swcutil dl -d <domain>` on-device
or a tap-from-Notes test to confirm; the audit catches the
misconfiguration but only the on-device check confirms the fix.>

<If Critical findings exist:>
> **Critical findings present.** Apple-deep-link Critical = do not
> rely on the deep-link surface for marketing campaigns, and for
> RCE-class deep-link handlers, do not ship the build at all until
> the Immediate Action tasks are resolved. See section below.

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
- $AUDIT_DIR/tooling-raw/ (associated-domains, url-types, queries-schemes, user-activity-types, continue-useractivity, url-scheme-handlers, spotlight-refs, app-intents-refs, aasa-references)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### Immediate Action — fix before relying on the deep-link surface

<one block per Critical finding>

**Task: S### — <Category> — <Title>**
- Location: `path/to/file.swift:line` or `Entitlement:<file>:<key>` or `Info.plist:<key>`
- Anchor: <anchor>
- Platform: <platform>
- Verification: <code | runtime>
- Issue: <description>
- Remediation: <specific fix>
- Verification step: <`swcutil dl -d <domain>` / `curl -I https://<domain>/.well-known/apple-app-site-association` / `xcrun simctl openurl booted <url>` / tap-from-Notes / etc.>
- Operational note: <e.g. "blocks marketing-link campaigns" / "RCE — block release" / "AutoFill silently broken">

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
- [ ] If any task involved the Associated Domains entitlement: re-verified via `swcutil dl -d <domain>` on a Developer-mode-enabled iOS device against a TestFlight build
- [ ] If any task involved AASA serving: re-verified via `curl -I https://<domain>/.well-known/apple-app-site-association` (no redirect, 200, Content-Type application/json)
- [ ] If any task involved a custom URL scheme handler: re-verified via `xcrun simctl openurl booted <url>` AND a state-changing scenario was tested for the re-auth / confirmation requirement
- [ ] If any task involved Universal Link routing: re-verified by tapping a link in Notes from cold launch, warm launch, and locked screen
- [ ] If any task involved Spotlight indexing of private content: re-verified that `isEligibleForPublicIndexing = false` was set and tested via Settings → Siri & Search on a freshly-signed-in device
- [ ] If any task involved `webcredentials:`: re-verified that AutoFill suggests credentials on the matching domain

## Sensitive-content warning

This report references the project's Associated Domains entitlement
content, AASA-style URLs, custom URL schemes, and potentially internal
domain names. Treat as confidential — these are exactly the URLs an
attacker probes when targeting a custom URL scheme or staging an AASA
spoof. Do not share externally without redaction.

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
