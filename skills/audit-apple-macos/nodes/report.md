# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` with macOS-specific tier mapping (**Immediate Action** above P0 for Critical findings — these block Mac App Store submission or fail Notarization).

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`, `codex_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Apple-macos sprint mapping override

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | **Immediate Action — fix before next Mac submission / Notarization** |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

"Immediate Action" here means: do not submit a build to App Store Connect (Mac App Store) or run `xcrun notarytool submit` against a Developer ID build with this finding outstanding. Common Critical examples: a Mac App Store target without `com.apple.security.app-sandbox`; a Developer ID build with an unjustified `disable-library-validation` exception that Notarization will reject; a Sparkle 1 update channel with no EdDSA signature.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Category** — one of the 12 macOS categories
- **Location** — `path/to/file:line` or `<TargetName>.entitlements:<key>` or `ExportOptions.plist:method` (never just "the project")
- **Anchor** — required (`Entitlement:com.apple.security.app-sandbox`, `Entitlement:com.apple.security.cs.disable-library-validation`, `InfoPlist:LSUIElement`, `Apple:Notarization`, `Sparkle:SUPublicEDKey`, etc.)
- **Platform** — `macOS` or `MacCatalyst` (or `Multi` when the finding also affects iPad-on-Mac)
- **Issue** — clear description
- **Remediation** — concrete, specific (e.g. `Add <key>com.apple.security.app-sandbox</key><true/> to MyMacApp.entitlements; ensure the Mac App Store scheme's CODE_SIGN_ENTITLEMENTS build setting points at it; re-archive and re-upload`)
- **Verification step** — for macos this is usually `codesign --display --entitlements - <app>`, `spctl --assess --type execute --verbose <app>`, `xcrun notarytool log <submission-id>`, or a live launch test on a clean Mac (no developer cert in Keychain) for Gatekeeper confirmation. For Sparkle, an end-to-end test against a staging appcast.

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — apple-macos — <scope>, <date>`
- Task description: scope covered, 12 categories reviewed, tooling that ran, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Apple macOS Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, tooling summary, total findings by severity,
top 3 issues, reminder of audit's inherent limitations — macOS
findings often require a real `xcodebuild archive` + `codesign
--display` + `xcrun notarytool submit` cycle to confirm. The audit
catches the misconfig but only the Notarization round-trip or App
Store Connect upload confirms the fix.>

<If Critical findings exist:>
> **Critical findings present.** Apple-macos Critical = do not submit
> to Mac App Store or run Notarization against this build until the
> Immediate Action tasks are resolved. See section below.

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
- $AUDIT_DIR/tooling-raw/ (build settings, entitlements, info-plists, export-options, codesign, sparkle-detection)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/codex.md           <or "MISSING — single-agent run" if codex_status=failed>
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### Immediate Action — fix before next Mac submission / Notarization

<one block per Critical finding>

**Task: S### — <Category> — <Title>**
- Location: `path/to/file:line` or `<entitlements>:<key>` or `ExportOptions.plist:method`
- Anchor: <anchor>
- Platform: <macOS | MacCatalyst | Multi>
- Verification: <code | runtime>
- Issue: <description>
- Remediation: <specific fix>
- Verification step: <`codesign --display --entitlements - <app>` / `spctl --assess --type execute --verbose <app>` / `xcrun notarytool submit` round-trip / Sparkle staging-appcast test>
- Operational note: <e.g. "blocks Mac App Store submission" / "Notarization will return Invalid" / "Gatekeeper will block launch on clean Macs">

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
- [ ] If any task involved entitlement changes: re-verified via `codesign --display --entitlements - <app>` against a freshly archived+signed `.app`
- [ ] If any task involved Notarization: re-verified by a full `xcrun notarytool submit --wait` + `xcrun stapler staple` cycle against the produced `.app` or `.dmg`
- [ ] If any task involved Gatekeeper: re-verified with `spctl --assess --type execute --verbose=4` on a clean Mac (no developer cert in Keychain) — local dev Macs trust their own certs and mask the issue
- [ ] If any task involved Sparkle: re-verified end-to-end against a staging appcast with `SUPublicEDKey` configured and the binary signed with the matching EdDSA key
- [ ] If any task involved Mac Catalyst pointer / keyboard: re-verified on a real Mac with mouse + hardware keyboard, not the simulator

## Sensitive-content warning

This report may reference internal team IDs (`DEVELOPMENT_TEAM`),
bundle identifiers, provisioning profile UUIDs, EdDSA public keys, and
appcast URLs. Treat as confidential. The exported `.xcarchive`, any
`ExportOptions.plist`, and Notarization submission logs may contain
sensitive distribution metadata; review before sharing externally.

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
