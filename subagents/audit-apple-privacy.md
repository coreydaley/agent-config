---
name: audit-apple-privacy
description: Dual-agent Apple platform privacy compliance audit — Privacy Manifest (PrivacyInfo.xcprivacy, required since May 2024), Info.plist purpose strings, ATT (App Tracking Transparency) / IDFA, required-reason API declarations, third-party SDK privacy declarations, data-minimization patterns, App Privacy Report alignment. Separate from `audit-apple-security` (which focuses on attack-resistant code).
---

# Apple Platform Privacy Audit

You are orchestrating a dual-agent privacy compliance audit of a
native Apple app against Apple's privacy requirements.

**Required reading**: Before starting, read [`lib/audit-framework.md`](../lib/audit-framework.md).
This file specifies only the audit-specific deltas.

**Audit identifier**: `apple-privacy` — `$AUDIT_DIR` is
`~/Reports/<org>/<repo>/audits/<TS>-apple-privacy/`

**Scope**: Swift source files, `PrivacyInfo.xcprivacy` files,
`Info.plist`, third-party SDK directories, asset catalogs.

**Relationship to `audit-apple-security`**: Privacy is a separate
audit because Apple treats it separately at App Review time and the
concerns are different (privacy = data-practice compliance and user
expectations; security = attack-resistant code). When run together,
this audit handles Privacy Manifest, purpose strings, ATT, and
required-reason APIs; `audit-apple-security` handles Keychain, ATS,
entitlements, code signing, etc. There's slight overlap in
emergency-exit territory (third-party SDK without a Privacy Manifest
shipping to App Store).

**Inherent limitations**: Privacy compliance is partly mechanical
(Privacy Manifest present? purpose strings present?) and partly
about actual app behavior matching declared behavior. Static review
catches the mechanical parts; runtime verification (App Privacy
Report on device, App Store Connect Privacy Manifest validation)
catches divergences.

---

## Schema extensions

Beyond the framework baseline, add:

| Column | Description |
|---|---|
| `Concern` | One of: `PrivacyManifest`, `PurposeStrings`, `ATT`, `RequiredReason`, `SDKPrivacy`, `DataMinimization`, `Tracking`, `Permissions` |
| `Submission Impact` | `Submission Blocker` (App Review will reject), `Submission Risk` (likely to be flagged), `Compliance` (legally required regardless of Apple), or `Best Practice` |
| `Verification` | `code` (inspectable) or `runtime` (requires App Privacy Report on device or App Store Connect Privacy Manifest validation) |

Full schema:
```
| ID | Severity | Concern | Submission Impact | Title | Location | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

---

## Categories

The audit reviews eight categories:

| # | Category | Covers |
|---|---|---|
| 1 | Privacy Manifest presence & accuracy | `PrivacyInfo.xcprivacy` present in app bundle and accurate; data collection categories (`NSPrivacyCollectedDataTypes`); tracking declaration (`NSPrivacyTracking`); required-reason API declarations (`NSPrivacyAccessedAPITypes`); tracking domains (`NSPrivacyTrackingDomains`) |
| 2 | Info.plist purpose strings | Every accessed sensitive resource has a clear `NS*UsageDescription` (`NSCameraUsageDescription`, `NSMicrophoneUsageDescription`, `NSLocationWhenInUseUsageDescription`, `NSPhotoLibraryUsageDescription`, `NSContactsUsageDescription`, `NSFaceIDUsageDescription`, etc.); strings are localized per supported language |
| 3 | App Tracking Transparency (ATT) | If `IDFA` is accessed via `ASIdentifierManager.shared().advertisingIdentifier`: ATT request flow implemented via `ATTrackingManager.requestTrackingAuthorization`; `NSUserTrackingUsageDescription` purpose string present; tracking only after authorization granted |
| 4 | Required-reason APIs (Apple May 2024 rules) | UserDefaults APIs, fileTimestamp APIs (`creationDate`, `modificationDate`, `attributeModificationDate`), systemBootTime APIs, diskSpace APIs, activeKeyboards APIs — each accessed-API set must have a declared `NSPrivacyAccessedAPITypeReasons` value in the Privacy Manifest |
| 5 | Third-party SDK privacy | Each third-party SDK that ships to the App Store must have its own `PrivacyInfo.xcprivacy` (Apple's "commonly used SDKs" list — required since May 2024). Verify SDKs in `Pods/`, SPM dependencies, and binary frameworks include their manifests; SDK signing required |
| 6 | Data minimization | Code only collects data it has declared; analytics events / telemetry don't include unintended PII (email, location, device identifiers in event names); local data retention bounded; no over-collection |
| 7 | Tracking domains | Network calls to known tracking domains (analytics, ad networks, fingerprinting services) declared in `NSPrivacyTrackingDomains`; conditional on ATT authorization for tracking domains |
| 8 | Permission UX | Permission prompts use clear pre-prompts; permissions requested at point-of-use (not on launch); graceful degradation if denied; settings deep-link via `UIApplication.openSettingsURLString` for changing settings |

---

## Severity calibration

| Severity | Anchor |
|---|---|
| **Critical** | Missing `PrivacyInfo.xcprivacy` for an app submitting to App Store after May 2024 (App Review will reject); third-party SDK on Apple's required list missing its Privacy Manifest (App Review will reject); IDFA accessed without ATT flow; purpose string missing for an accessed sensitive resource (App Review will reject) |
| **High** | Privacy Manifest present but declared data types don't match what the code actually collects; purpose strings present but vague / misleading ("for app functionality" — App Review will flag); tracking domain calls without ATT authorization gating |
| **Medium** | Required-reason API access not declared (gray area pre-rejection); SDK Privacy Manifests outdated; data-minimization gaps (analytics over-collecting) |
| **Low** | Permission UX improvements; missing pre-prompts; non-Apple-required compliance considerations |

Calibration is **especially evidence-driven** here — Submission
Impact column anchors severity. `Submission Blocker` → Critical,
`Submission Risk` → High by default.

---

## Phase 1: Audit-specific orient

### Tooling

```bash
mkdir -p "$AUDIT_DIR/tooling-raw"

# Privacy Manifest snapshots (app + every SDK)
find "$PROJECT_CWD" -name "PrivacyInfo.xcprivacy" -not -path '*/.*' \
  -exec sh -c 'echo "=== $1 ==="; cat "$1"' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/privacy-manifests.txt" 2>&1

# Info.plist purpose strings
find "$PROJECT_CWD" -name "Info.plist" -not -path '*/.*' -not -path '*/Pods/*' \
  -exec sh -c 'echo "=== $1 ==="; \
    /usr/libexec/PlistBuddy -c "Print" "$1" 2>/dev/null \
    | grep -E "UsageDescription|NSApp|NSPrivacy|UIRequires" || true' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/info-plist-privacy.txt" 2>&1

# List third-party SDKs (SPM + Cocoapods + binary frameworks)
{
  echo "=== SPM dependencies ===";
  [[ -f Package.resolved ]] && cat Package.resolved;
  echo;
  echo "=== Cocoapods ===";
  [[ -f Podfile.lock ]] && cat Podfile.lock;
  echo;
  echo "=== XCFrameworks ===";
  find "$PROJECT_CWD" -name "*.xcframework" -not -path '*/.*' -not -path '*/build/*' \
    -maxdepth 4 2>/dev/null;
} > "$AUDIT_DIR/tooling-raw/third-party-sdks.txt"

# Check for IDFA / ATT usage
{
  echo "=== IDFA usage ===";
  grep -rn "ASIdentifierManager\|advertisingIdentifier" --include="*.swift" "$PROJECT_CWD" 2>/dev/null;
  echo;
  echo "=== ATT usage ===";
  grep -rn "ATTrackingManager\|requestTrackingAuthorization" --include="*.swift" "$PROJECT_CWD" 2>/dev/null;
} > "$AUDIT_DIR/tooling-raw/idfa-att.txt"

# Required-reason API candidates
{
  echo "=== UserDefaults ===";
  grep -rn "UserDefaults" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50;
  echo;
  echo "=== File timestamps ===";
  grep -rn "creationDate\|modificationDate\|fileAttributes" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50;
  echo;
  echo "=== System boot time ===";
  grep -rn "systemUptime\|kern.boottime" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50;
} > "$AUDIT_DIR/tooling-raw/required-reason-candidates.txt"
```

### Emergency exit — App Store rejection imminent

After tooling runs, if any of these are true, halt immediately:

1. **Project ships to App Store** (Xcode project with App Store
   distribution provisioning, not a side project) **AND no
   `PrivacyInfo.xcprivacy` exists** → write `EMERGENCY.md`; App
   Review will reject
2. **Third-party SDK in Apple's required-manifest list** is bundled
   without its `PrivacyInfo.xcprivacy` (commonly-required SDKs
   include Firebase, Branch, GoogleSignIn, AppsFlyer, Amplitude, etc.)
   → write `EMERGENCY.md`; App Review will reject
3. **IDFA accessed** but **no ATT flow** in the code → write
   `EMERGENCY.md`; App Review will reject

If `--allow-noncompliant` flag is set, proceed but flag everything as
Critical instead of halting.

### Survey

Beyond the framework baseline:

- Read `tooling-raw/privacy-manifests.txt` — does the app have a
  manifest? Do the bundled SDKs have manifests?
- Read `tooling-raw/idfa-att.txt` — is IDFA accessed? Is ATT flow
  present?
- Read `tooling-raw/info-plist-privacy.txt` — note declared purpose
  strings and supported locales
- Detect intended distribution channel: App Store provisioning vs
  Enterprise vs Developer ID (macOS) vs side-loading — calibrates
  severity
- Detect required-reason API candidates from
  `required-reason-candidates.txt` for cross-reference

---

## Phase 2: Codex prompt body

Substitute into the canonical invocation (framework Phase 2 Step 1):

```text
Perform a thorough Apple platform privacy compliance audit of
[RESOLVED_SCOPE]. Tooling output is in $AUDIT_DIR/tooling-raw/.

Write all findings to $AUDIT_DIR/codex.md using this exact table
format:
| ID | Severity | Concern | Submission Impact | Title | Location | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
where ID uses prefix C (e.g. C001, C002).

Concern column: PrivacyManifest, PurposeStrings, ATT, RequiredReason,
SDKPrivacy, DataMinimization, Tracking, Permissions.
Submission Impact: "Submission Blocker" (App Review will reject),
"Submission Risk" (likely to be flagged), "Compliance" (legally
required regardless of Apple), or "Best Practice".
Verification: code (inspectable) or runtime (requires App Privacy
Report on device or App Store Connect Privacy Manifest validation).

DO NOT review Keychain / ATS / entitlements / code signing — those
belong in audit-apple-security, run separately.

Cover these 8 categories:
(1) Privacy Manifest presence & accuracy — PrivacyInfo.xcprivacy in
the app bundle and accurate; NSPrivacyCollectedDataTypes declares
real collection; NSPrivacyTracking matches actual tracking;
NSPrivacyAccessedAPITypes declares required-reason API usage;
NSPrivacyTrackingDomains lists tracking endpoints. App Store
submission post-May-2024 requires this.
(2) Info.plist purpose strings — every accessed sensitive resource
has a clear NS*UsageDescription (NSCamera, NSMicrophone,
NSLocationWhenInUse, NSPhotoLibrary, NSContacts, NSFaceID, etc.);
strings localized per supported language; strings should explain
WHY, not just WHAT.
(3) App Tracking Transparency (ATT) — if IDFA accessed via
ASIdentifierManager.shared().advertisingIdentifier: ATT request flow
via ATTrackingManager.requestTrackingAuthorization;
NSUserTrackingUsageDescription purpose string;
tracking ONLY after authorization granted.
(4) Required-reason APIs (Apple May 2024 rules) — UserDefaults
APIs, fileTimestamp APIs (creationDate, modificationDate,
attributeModificationDate), systemBootTime APIs, diskSpace APIs,
activeKeyboards APIs — each set must have declared
NSPrivacyAccessedAPITypeReasons in the Privacy Manifest.
(5) Third-party SDK privacy — each third-party SDK on Apple's
'commonly used SDKs' list must include its own PrivacyInfo.xcprivacy.
Check SDKs in Pods/, SPM dependencies, binary frameworks. SDK signing
required.
(6) Data minimization — code only collects data it has declared in
the manifest; analytics events / telemetry don't include unintended
PII (email, location, device IDs in event names); local retention
bounded; no over-collection.
(7) Tracking domains — network calls to known tracking domains
(analytics, ad networks, fingerprinting) declared in
NSPrivacyTrackingDomains; conditional on ATT authorization for
tracking.
(8) Permission UX — permissions use clear pre-prompts; requested at
point-of-use (not on launch); graceful degradation if denied;
deep-link to Settings via UIApplication.openSettingsURLString.

Submission Impact drives severity. Submission Blocker → Critical.
Submission Risk → High.

Do not read or reference any other review file.
```

## Phase 2: Claude review checklist

Same 8 categories. Read `tooling-raw/` first. Critical findings here
mean **App Review will reject** — be very confident before assigning
that severity.

---

## Phase 4: Devil's advocate prompt body

```text
Read $AUDIT_DIR/synthesis.md and the tooling output in
$AUDIT_DIR/tooling-raw/. Your job is to attack the synthesis, not
improve it. Write your challenge to $AUDIT_DIR/devils-advocate.md
covering:
(1) False positives — Privacy Manifest entries the reviewer flagged
as missing but are actually present in a parent manifest; required-
reason API access in a context that doesn't trigger Apple's
declaration requirement (e.g. UserDefaults access by a system
framework, not the app itself); ATT findings on an app not actually
accessing IDFA.
(2) Severity miscalibrations — Submission Impact rated higher than
warranted (App Review enforcement varies in practice — some
"Blockers" are actually warnings); or lower than warranted for an
imminent submission.
(3) Missing findings — privacy issues both reviewers missed,
especially: data collection happening BEFORE ATT consent;
fingerprinting via device characteristics not declared as tracking;
shared web views with third-party cookies; analytics SDK initialized
before consent; PII leakage in crash reports or os_log output;
clipboard data access; on-device ML model training on user data
without disclosure; Live Activity / Dynamic Island showing
PII publicly.
(4) Remediation steps that are impractical (e.g. removing a SDK that
provides essential functionality; adding a Privacy Manifest entry
when the underlying behavior should change instead).
Be specific. Every challenge must cite the finding ID and the
Concern.
```

---

## Phase 5: Sprint mapping override

Critical (Submission Blocker) findings → **Submission Blocker**
section above P0, not Immediate Action — they block App Store
submission specifically.

| Finding Severity | Sprint Priority |
|---|---|
| **Critical (Submission Blocker)** | **Submission Blocker — fix before next App Store submission** |
| High (Submission Risk) | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

Each task includes its Submission Impact in the task description.

---

## Output checklist additions

Beyond framework baseline:

- [ ] Each task has: finding ID, Concern, Submission Impact,
      Verification mode, location, issue, remediation, verification
      (App Store Connect Privacy Manifest validation or App Privacy
      Report on device)
- [ ] Submission Blocker findings broken out into separate section
      above P0
- [ ] Emergency-exit handled if triggered (missing Privacy Manifest,
      missing SDK manifests, IDFA without ATT)
- [ ] Hand-off note flags App Store rejection risk explicitly

---

## Reference

- Audit reference doc: [`docs/apple-privacy/README.md`](../docs/apple-privacy/README.md)
- Framework: [`lib/audit-framework.md`](../lib/audit-framework.md)
- Privacy Manifest files: https://developer.apple.com/documentation/bundleresources/privacy_manifest_files
- Required reason APIs: https://developer.apple.com/documentation/bundleresources/privacy_manifest_files/describing_use_of_required_reason_api
- App Tracking Transparency: https://developer.apple.com/documentation/apptrackingtransparency
- Apple privacy hub: https://developer.apple.com/privacy/
- Apple's "commonly used SDKs" requiring manifests: https://developer.apple.com/support/third-party-SDK-requirements/
