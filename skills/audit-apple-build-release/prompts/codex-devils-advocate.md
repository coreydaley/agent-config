Read synthesis.md and the raw tooling output in tooling-raw/ in the
audit dir you've been granted access to. Your job is to attack the
synthesis, not improve it.

Write your challenge to devils-advocate.md (in the same audit dir)
using this table format:

| ID | Challenge Type | Target Finding | Claim | Evidence | Confidence |

where:
- ID uses prefix D (D001, D002, ...)
- Challenge Type: false_positive | severity_miscalibrated | missing_finding | missing_compound | impractical_remediation | insufficient_verification
- Target Finding: the S### ID from synthesis.md being challenged (or "N/A" for missing_finding / missing_compound)
- Claim: 1-2 sentence challenge
- Evidence: file:line citation, build-setting reference, or specific lock-file line
- Confidence: high | medium | low

Cover these challenge categories:

(1) False positives — findings that don't actually apply in context.
Specifically for Apple build-release:
- A Debug-only setting flagged as Critical is actually only present in
  the Debug configuration, never Release — re-read the diff between
  build-settings-debug.txt and build-settings-release.txt before
  flagging a Critical.
- A setting "missing" from Info.plist is generated via
  INFOPLIST_KEY_* in build settings (Xcode 15+ generated Info.plist).
  Look at build-settings-*.txt for the INFOPLIST_KEY_* variants before
  flagging the explicit Info.plist as missing.
- An SPM `.branch("main")` pin is for a first-party package the
  project author also maintains; while still a hygiene issue, it's not
  the release-fragility risk that an external `.branch()` pin is.
- `Pods/` committed is intentional for this project (some teams commit
  Pods/ to make CI faster); flag only if `Podfile.lock` is stale or
  inconsistent.
- A scheme that looks user-only (`xcuserdata`) is actually shared but
  Xcode happened to write the latest revision under xcuserdata; check
  xcshareddata/xcschemes for the canonical copy.

(2) Severity miscalibrations — findings rated too high (the setting is
overridden by a downstream .xcconfig include; the setting only matters
for a target that isn't shipped to users; the setting only affects
local dev builds; CI overrides the value via -<settingName>=value at
invocation) or too low (the setting affects every Release archive; the
setting is in the canonical xcconfig that every target inherits; the
finding will reject every App Store upload).

(3) Missing findings — Apple-build-release issues both reviewers may
have missed:
- macOS-specific: missing Hardened Runtime entitlement enabled on
  Release config but disabled on Debug (codesign Notarization-stage
  failure), missing `com.apple.security.app-sandbox` for a Mac App
  Store target.
- watchOS-specific: companion-app + watch-app deployment target /
  bundle version mismatches.
- visionOS-specific: missing XROS_DEPLOYMENT_TARGET for any
  cross-platform target shared with visionOS.
- App Store Connect: app uses TestFlight Internal/External Group
  distribution; the export-options-plist `method` value (`app-store-connect`
  vs `app-store` vs `release-testing`) is misaligned with the team's
  actual distribution flow.
- Crash analytics: dSYM upload script in a Run Script Build Phase but
  guarded by `${CONFIGURATION} = "Release"` and the Phase is set to
  "Based on dependency analysis", which silently skips the run because
  the script declares no inputs/outputs.
- SwiftPM: target dependency on a local SPM package via .package(path:
  "..") for the app target but the path is relative to a CI working
  dir; CI fails because the path doesn't resolve.
- Resources: `Bundle.module` references in SPM package code but the
  target manifest is missing `.process` or `.copy` declarations for
  the resource files — resources don't ship.

(4) Missing compound paths — separate findings in the synthesis that
combine into a worse outcome than any single finding represents:
- "Debug-flavored release ship" chain (SWIFT_OPTIMIZATION_LEVEL=-Onone
  + ENABLE_TESTABILITY=YES + DEBUG=1) — already covered, but check
  whether all three are actually present in Release config.
- "Unattributable crash" chain (DEBUG_INFORMATION_FORMAT=dwarf for
  Release + no dSYM upload destination + Bitcode disabled) — every
  crash from the App Store is permanently unsymbolicated.
- "Capability silently missing on TestFlight" chain (capability in
  Debug.entitlements but not Release.entitlements + manual signing
  with a stale Release profile).
- "Reproducibility chain" (Package.resolved not committed + `.branch()`
  SPM pin + CI allows automatic package resolution).

(5) Impractical / incomplete / wrong remediations — e.g.:
- "Move the setting to .xcconfig" without specifying which .xcconfig
  (the project may have a hierarchy where the canonical place is two
  levels up).
- "Switch from Automatic to Manual signing" without specifying the
  match/fastlane/CI flow that will populate the provisioning profile —
  going manual without a profile-management strategy is worse than
  staying automatic.
- "Pin SPM dep to .exact()" without acknowledging that .exact() is
  rigid; .upToNextMinor() may be the right answer.
- "Add a dSYM upload script" without specifying the run-phase inputs/
  outputs declaration that prevents the script being skipped.

(6) Verification steps that don't actually prove the fix works — e.g.
"verify by building in Xcode" when the issue only manifests in
xcodebuild archive; "manual code review" verification for a setting
whose effect only shows up at codesign / upload time; "check that the
setting is set in Xcode UI" when the canonical place is xcconfig and
the Xcode UI hides the xcconfig value.

Be specific. Every challenge must cite the finding ID and reference
the build setting / file path / lockfile line where applicable.

Do not read or reference any other review file beyond synthesis.md and
the tooling-raw/ directory.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type
  "no_challenges" and Confidence "high" stating that you attempted but
  found nothing worth surfacing.
- No emojis.
