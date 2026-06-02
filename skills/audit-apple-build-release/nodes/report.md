# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` with build-release-specific tier mapping (**Immediate Action** above P0 for Critical findings — these are App-Store-upload-blockers or unattributable-crash chains).

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`, `codex_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Apple-build-release sprint mapping override

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | **Immediate Action — fix before next archive** |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

"Immediate Action" here means: do not archive a Release build for TestFlight / App Store with this finding outstanding. Common Critical examples: a Release config with `SWIFT_OPTIMIZATION_LEVEL=-Onone`, a missing dSYM destination, capability missing from Release entitlements.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Category** — one of the 12 build-release categories
- **Location** — `path/to/file:line` or `Xcode setting <NAME> at <target>:<configuration>` (never just "the project")
- **Anchor** — required (`BuildSetting:...`, `File:project.pbxproj`, `Apple:DistributionGuide`, etc.)
- **Platform** — `iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`, `visionOS`, or `Multi`
- **Issue** — clear description
- **Remediation** — concrete, specific (e.g. `Set SWIFT_OPTIMIZATION_LEVEL = -O for the Release configuration in MyApp.xcconfig:42, override in target settings, regenerate xcconfig`)
- **Verification** — for build-release this should usually be a *clean archive*: `xcodebuild archive -workspace ... -scheme ... -configuration Release -archivePath /tmp/Test.xcarchive`. For signing-specific findings, verify with `codesign --display --entitlements -` against the built `.app`. For dSYM, verify with `dwarfdump --uuid` against the produced `.xcarchive/dSYMs/`.

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — apple-build-release — <scope>, <date>`
- Task description: scope covered, 12 categories reviewed, tooling that ran, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Apple Build & Release Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, tooling summary, total findings by severity, top
3 issues, reminder of audit's inherent limitations — build-release
findings often require a real `xcodebuild archive` + `codesign` /
App-Store-Connect upload to confirm; the audit catches the misconfig
but only the upload confirms the fix.>

<If Critical findings exist:>
> ⚠️ **Critical findings present.** Apple-build-release Critical = do
> not archive a Release build for TestFlight or App Store until the
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
- $AUDIT_DIR/tooling-raw/ (build settings, xcconfigs, entitlements, lockfiles, schemes, plists)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/codex.md           <or "MISSING — single-agent run" if codex_status=failed>
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### Immediate Action — fix before next archive

<one block per Critical finding>

**Task: S### — <Category> — <Title>**
- Location: `path/to/file:line` or `Xcode setting <NAME> at <target>:<config>`
- Anchor: <anchor>
- Platform: <platform>
- Verification: <code | runtime>
- Issue: <description>
- Remediation: <specific fix>
- Verification step: <`xcodebuild archive ...` / `codesign --display --entitlements -` / `dwarfdump --uuid` / etc.>
- Operational note: <e.g. "blocks App Store upload" / "blocks symbolicated crash reports">

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
- [ ] If any task involved entitlement changes: re-verified via `codesign --display --entitlements -` against a built+signed `.app`
- [ ] If any task involved Archive config: verified by running `xcodebuild archive` and inspecting the resulting `.xcarchive`
- [ ] If any task involved dSYM config: verified that `.xcarchive/dSYMs/*.dSYM` exists and `dwarfdump --uuid` matches the binary's UUID
- [ ] If any task involved CI signing: verified with a clean CI run (cleared DerivedData, fresh checkout)
- [ ] If any task involved deployment target bumps: built against the minimum-supported OS in the simulator

## Sensitive-content warning

This report may reference internal team IDs (`DEVELOPMENT_TEAM`),
bundle identifiers, provisioning profile UUIDs, and CI secret variable
names. Treat as confidential. The exported `.xcarchive` and any
ExportOptions.plist may contain sensitive distribution metadata; review
before sharing externally.

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
