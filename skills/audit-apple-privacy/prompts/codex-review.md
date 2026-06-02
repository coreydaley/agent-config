Perform a thorough Apple platform privacy compliance audit of the scope
at the project root you've been pointed at. Tooling has already been run;
raw output is in the audit dir's tooling-raw/ subdirectory. Read those
files first: privacy-manifests.txt (PrivacyInfo.xcprivacy contents),
info-plist-privacy.txt (purpose strings), third-party-sdks.txt (SPM /
Cocoapods / XCFramework list), idfa-att.txt (IDFA + ATT call sites),
required-reason-candidates.txt (UserDefaults / file timestamps / boot
time / disk space / active keyboards), distribution-channel.txt
(provisioning hints).

Privacy compliance is partly mechanical (manifest present, purpose
strings present, ATT prompt present) and partly about whether declared
behavior matches actual code behavior. Static review catches the
mechanical parts and obvious mismatches; runtime verification (App
Privacy Report on device, App Store Connect Privacy Manifest validation)
catches divergences. Flag both kinds.

Write all findings to codex.md (in the audit dir you were granted write
access to) using this exact table format:

| ID | Severity | Concern | Submission Impact | Title | Location | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix C (e.g. C001, C002). Every finding MUST include:
- Concern: one of PrivacyManifest, PurposeStrings, ATT, RequiredReason,
  SDKPrivacy, DataMinimization, Tracking, Permissions.
- Submission Impact: "Submission Blocker" (App Review will reject),
  "Submission Risk" (likely to be flagged), "Compliance" (legally
  required regardless of Apple — GDPR/CCPA), or "Best Practice".
- Verification: code (inspectable in source) or runtime (requires App
  Privacy Report on device or App Store Connect Privacy Manifest
  validation).

DO NOT review Keychain / ATS / entitlements / code signing / WebView
bridge / StoreKit / Crypto / Logging / CloudKit ACLs — those belong in
audit-apple-security, run separately.

Cover these 8 concerns (skip if not applicable):

(1) PrivacyManifest — PrivacyInfo.xcprivacy in the app bundle and
accurate. NSPrivacyCollectedDataTypes declares real collection (not
empty, not over-declared, types match actual code behavior).
NSPrivacyTracking matches actual tracking. NSPrivacyAccessedAPITypes
declares required-reason API usage with Apple-assigned reason codes.
NSPrivacyTrackingDomains lists tracking endpoints. App Store submission
post-May-2024 requires this; absence = Submission Blocker.

(2) PurposeStrings — every accessed sensitive resource has a clear
NS*UsageDescription (NSCameraUsageDescription,
NSMicrophoneUsageDescription, NSLocationWhenInUseUsageDescription,
NSLocationAlwaysAndWhenInUseUsageDescription, NSPhotoLibraryUsageDescription,
NSPhotoLibraryAddUsageDescription, NSContactsUsageDescription,
NSFaceIDUsageDescription, NSCalendarsUsageDescription,
NSRemindersUsageDescription, NSMotionUsageDescription,
NSSpeechRecognitionUsageDescription, NSBluetoothAlwaysUsageDescription,
NSLocalNetworkUsageDescription, NSUserTrackingUsageDescription, etc.).
Strings localized per supported language. Strings explain WHY, not just
WHAT — "for app functionality" is a Submission Risk.

(3) ATT — iOS / iPadOS / tvOS / visionOS only; macOS does NOT have ATT
or IDFA (skip this category for macOS-only targets). For iOS-distinctive
prompt timing / pre-prompt UX depth see audit-apple-ios. If IDFA
accessed via ASIdentifierManager.shared().advertisingIdentifier: ATT
request flow via ATTrackingManager.requestTrackingAuthorization MUST
exist; NSUserTrackingUsageDescription purpose string MUST exist; IDFA
reads MUST be gated on .authorized status. IDFA without ATT =
Submission Blocker.

(4) RequiredReason — Apple May 2024 rules. Five categories:
NSPrivacyAccessedAPICategoryUserDefaults (any UserDefaults reads/writes),
NSPrivacyAccessedAPICategoryFileTimestamp (creationDate,
contentModificationDate, contentAccessDate, attributeModificationDate
via FileAttributeKey / URLResourceValues / stat / getattrlist),
NSPrivacyAccessedAPICategorySystemBootTime (systemUptime,
kern.boottime), NSPrivacyAccessedAPICategoryDiskSpace
(volumeAvailableCapacity, systemFreeSize),
NSPrivacyAccessedAPICategoryActiveKeyboards (activeInputModes,
UITextInputMode — iOS / iPadOS / visionOS only). Each accessed-API set must have an Apple-assigned
reason code (e.g. CA92.1, C56D.1, 0A2A.1, 35F9.1, C617.1, 85F4.1,
54BD.1) in the Privacy Manifest's NSPrivacyAccessedAPITypes array. Use
of an API category without a declared reason = Submission Risk.

(5) SDKPrivacy — each third-party SDK on Apple's "commonly used SDKs"
list (Firebase, Branch, GoogleSignIn, AppsFlyer, Amplitude, Adjust,
OneSignal, FBSDK, Mixpanel, Segment, Crashlytics, etc.) MUST include
its own PrivacyInfo.xcprivacy AND its signature (.xcprivacy.sig).
Check SDKs in Pods/, SPM dependencies, binary frameworks. Missing
manifest on a listed SDK = Submission Blocker.

(6) DataMinimization — code only collects data it has declared in the
manifest; analytics events / telemetry don't include unintended PII
(email, location, device IDs in event names or properties); local
retention bounded; no over-collection. Manifest/code drift over time is
the dominant failure mode here.

(7) Tracking — network calls to known tracking domains (analytics, ad
networks, fingerprinting services like fingerprintjs, doubleclick,
google-analytics, facebook.com/tr, branch.io, appsflyer, etc.) declared
in NSPrivacyTrackingDomains; conditional on ATT authorization for
tracking. Fingerprinting via device-characteristic fan-in (boot time +
disk space + active keyboards) is tracking even if no IDFA — Apple's
position.

(8) Permissions — permission prompts use clear pre-prompts; requested
at point-of-use (not on launch); graceful degradation if denied;
deep-link to Settings via UIApplication.openSettingsURLString for
re-enabling.

Submission Impact drives severity. Submission Blocker → Critical.
Submission Risk → High. Compliance findings → calibrate based on the
specific regulation and jurisdictional exposure. Best Practice → Low.

Critical anchors:
- Missing PrivacyInfo.xcprivacy for an App Store-bound submission
- Third-party SDK on Apple's required list missing its Privacy Manifest
- IDFA accessed without ATT flow
- Purpose string missing for an accessed sensitive resource

High anchors:
- Privacy Manifest declared types don't match actual code collection
- Purpose strings vague / misleading
- Tracking domain calls without ATT-authorization gating
- Required-reason API access without a declared reason code

Every finding must include a Verification field — for privacy this is
often "runtime" (App Store Connect Privacy Manifest validation after
TestFlight build, or on-device App Privacy Report). Code-level findings
(missing manifest file, missing purpose string in Info.plist) are
"code".

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to codex.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
