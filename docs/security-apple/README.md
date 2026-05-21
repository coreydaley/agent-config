# Apple Platform Security Audit Reference

Schema and severity reference for the `/audit-security-apple` command.
For backend services / web applications / IaC / CI/CD / agent-config,
see [`../security-web-application/README.md`](../security-web-application/README.md).

Audit artifacts are written outside this repo to
`~/Reports/<org>/<repo>/audits/<TS>-security-apple/` — `<org>/<repo>`
is derived from the `upstream` remote (falling back to `origin`), and
`<TS>` is the audit start timestamp (`YYYY-MM-DDTHH-MM-SS`).

Phase 1 runs the tooling that exists for Apple-platform static analysis
(gitleaks, semgrep with Swift rules, optionally `xcodebuild analyze`)
plus snapshots of source-level Apple artifacts (entitlements files,
Privacy Manifest, Info.plist purpose strings) into a `tooling-raw/`
subfolder. Apple static-analysis tooling is thinner than the web
ecosystem — reviewers do more manual code reading, and many findings
require runtime verification with built-app tooling.

## Output

Each audit run produces these files in its own timestamped
`$AUDIT_DIR`:

| File / Folder | Description |
|---|---|
| `tooling-raw/` | Raw output: `gitleaks.json`, `semgrep.json`, `xcodebuild-analyze.log` (if Xcode static analyzer ran), plus snapshots of `entitlements-declared.txt`, `privacy-manifest.txt`, `info-plist-purpose-strings.txt`. Includes `STATUS.md` noting skipped tools. |
| `EMERGENCY.md` | **Only present if Phase 1 emergency-exit triggered.** Describes exposed credentials, rotation steps. For Apple specifically: code-signing cert, App Store Connect API key, push notification cert, or service-side key each have their own rotation procedure. |
| `claude.md` | Claude's independent Apple security review (ID prefix `A`) |
| `codex.md` | Codex's independent Apple security review (ID prefix `C`) |
| `synthesis.md` | Unified, deduplicated findings (canonical `S`-prefix IDs), Compound Findings section, Rejected Devil's Advocate Challenges section |
| `devils-advocate.md` | Codex's challenge pass against the synthesis |
| `REPORT.md` | Final findings report — Critical broken out as **Immediate Action** above P0 |

`REPORT.md` is reference material. To act on the findings (High/Medium/Low),
run `/sprint-plan`:

```
/sprint-plan ~/Reports/<org>/<repo>/audits/<TS>-security-apple/REPORT.md
```

**Critical Apple findings should not wait for the next release window** —
pull from TestFlight if necessary, hotfix, re-submit.

## Finding Schema

All intermediate audit files (`claude.md`, `codex.md`, `synthesis.md`)
use this table format:

```
| ID | Severity | CWE/Apple | Category | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

`synthesis.md` adds a `Sources` column listing the source review IDs
each unified finding merges (e.g. `A002, C003`).

**ID prefix convention:**
- Claude's review: `A001`, `A002`... (Audit)
- Codex's review: `C001`, `C002`... (Codex)
- Synthesis: `S001`, `S002`... (Synthesis canonical)

**Severity levels:** Critical, High, Medium, Low

### CWE/Apple Column

Every finding maps to a [CWE](https://cwe.mitre.org/) identifier where
applicable and an Apple-platform anchor. A finding without either is
invalid and is omitted. Examples:

- `CWE-522 / Apple:Keychain` — insufficiently protected credentials
- `CWE-319 / Apple:ATS` — cleartext transmission (`NSAllowsArbitraryLoads`)
- `CWE-925 / Apple:URLScheme` — URL scheme without origin validation
- `CWE-749 / Apple:JSBridge` — exposed dangerous `WKScriptMessageHandler`
- `CWE-326 / Apple:Crypto` — weak crypto / wrong Keychain accessibility
- `CWE-285 / Apple:Entitlements` — over-broad entitlement granted
- `CWE-200 / Apple:Logging` — `os_log` with `%{public}` on PII
- `Apple:PrivacyManifest` — missing or incomplete `PrivacyInfo.xcprivacy`
- `Apple:StoreKit` — purchase used without `VerificationResult.verified`
- `Apple:CloudKit` — public database used where private+share appropriate

### Category Column

| Category | Covers |
|---|---|
| `Storage` | Keychain access groups, `kSecAttrAccessible*` flags, Secure Enclave, `NSFileProtection*`, never UserDefaults/plist for secrets |
| `ATS` | App Transport Security, `NSAllowsArbitraryLoads`, exception domains, cert pinning, TLS minimums |
| `URLScheme` | Custom URL schemes, Universal Links, `apple-app-site-association`, deep link input validation |
| `IPC` | XPC peer auth (audit_token + codesign req), App Groups, pasteboard, document handling |
| `Entitlements` | Least-privilege, App Sandbox, Hardened Runtime exceptions, code signing, provisioning, notarization |
| `Privacy` | `PrivacyInfo.xcprivacy`, `Info.plist` purpose strings, ATT/IDFA, required-reason APIs |
| `CloudKit` | Public vs private DB scoping, record ACLs, `CKShare` validation, shared zone permissions |
| `StoreKit` | StoreKit 2 `VerificationResult` handling, server-side validation, `originalTransactionID`, `revocationDate` |
| `WebView` | WKWebView (never UIWebView), `WKScriptMessageHandler` bridge, `evaluateJavaScript` with user input, `file://` scope |
| `Crypto` | CryptoKit, Secure Enclave for keys, `SecRandomCopyBytes`, no MD5/SHA1/DES, no hardcoded keys |
| `Logging` | `os_log` privacy qualifiers, `print()`/`NSLog` removed from release, crash report PII |
| `Dependency` | SPM `Package.resolved`, Cocoapods `Podfile.lock`, third-party SDK Privacy Manifests, XCFramework provenance |
| `Secrets` | Hardcoded credentials (triggers emergency-exit) |

### Platform Column

Which Apple platforms are affected. Values: `iOS`, `iPadOS`, `macOS`,
`MacCatalyst`, `watchOS`, `tvOS`, `visionOS`, or `Multi`. Combine when
relevant (e.g. `iOS,iPadOS`).

### Verification Column

`code` (inspectable from source alone) or `runtime` (requires built
app + Apple tooling).

Apple-specific runtime verification frequently uses:
- `codesign --display --entitlements -` on the built `.app` bundle
- Console.app — to inspect `os_log` output and confirm `%{public}` /
  `%{private}` qualifiers behave as intended
- Xcode's Accessibility Inspector + Static Analyzer
- **App Privacy Report** on iOS device (Settings → Privacy & Security →
  App Privacy Report) — confirms tracking behavior matches Privacy Manifest
- App Store Connect Privacy Manifest validation (pre-submission)
- `xcrun altool --notarization-info` (macOS notarization)

### Severity Calibration

Same evidence framework as the web-application audit. Anchors specific
to Apple platforms (starting point):

| Severity | Anchor examples |
|---|---|
| **Critical** | Live credentials hardcoded; `NSAllowsArbitraryLoads=true` shipping; StoreKit purchase used without `VerificationResult.verified`; WKWebView with `allowsContentJavaScript` loading arbitrary user URLs; CloudKit public DB for private user data; `disable-library-validation` Hardened Runtime exception without need; missing `PrivacyInfo.xcprivacy` for an app shipping post-May-2024 (App Store rejection) |
| **High** | Weak Keychain accessibility (`AccessibleAlways` for sensitive data); missing cert pinning on financial/health API; `os_log %{public}` on PII; URL scheme handler with no validation on state-changing path; XPC service without audit-token/codesign requirement; over-broad entitlement granted; StoreKit receipt validated only on-device |
| **Medium** | Deprecated `UIWebView` usage in maintained code; missing purpose strings for sensitive resources; Cocoapods without `Podfile.lock` committed; `arc4random` used where `SecRandomCopyBytes` would be appropriate; SPM dep without checksum verification; `print()`/`NSLog` in release config |
| **Low** | Minor entitlement pruning; deprecated-but-functional crypto with no immediate risk; defense-in-depth gaps |

### Compound Findings

Apple-specific compound patterns to watch for:

- **Account takeover via URL scheme**: URL scheme without validation +
  WKWebView with JS bridge → code execution in app context via crafted
  deep link
- **Receipt forgery accepted**: StoreKit verified only on-device +
  permanent entitlement granted → forged purchase yields permanent
  access
- **Private data exposure**: CloudKit public database + PII fields →
  mass user data exposure
- **Physical-access exploit**: Weak Keychain accessibility + biometric
  not required → physical-access attacker reads credentials
- **Library injection**: Hardened Runtime exceptions + dynamic library
  loading → arbitrary code at app startup

## Sprint Mapping

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | **Immediate Action — fix before next release / out-of-band patch** |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

For Apple apps, "Immediate Action" frequently means: pull the build
from TestFlight, hotfix, re-submit. Critical findings should not wait
for a planned release window.

Each task includes an Operational Note field for Critical findings
covering: credential rotation, push cert / App Store Connect API key
rotation, TestFlight pull required, user comms needed, incident-report
scope.

## App Store Rejection Risk

Several finding categories carry direct App Store rejection risk and
should be addressed **before** submission:

- Missing or inaccurate `PrivacyInfo.xcprivacy` (required since May 2024)
- Missing `Info.plist` purpose strings for accessed sensitive resources
- Missing required-reason API declarations (UserDefaults, fileTimestamp,
  systemBootTime, diskSpace APIs)
- App Tracking Transparency (ATT) flow not implemented when IDFA is
  accessed
- Hardened Runtime exceptions without documented justification (macOS
  notarization)
- Code signing / provisioning profile issues

## Modes

| Flag | Behavior |
|---|---|
| (none) | Audit the resolved scope path |
| `--diff-only` | Restrict the audit to files changed in `git diff main...HEAD` |
| `SKIP_XCODEBUILD=1` (env var) | Skip `xcodebuild analyze` (heavy — requires a full build) |

## Tooling

Apple static-analysis tooling is thinner than the web ecosystem. Phase
1 attempts:

| Tool | When | What it catches |
|---|---|---|
| `gitleaks` | Always | Secrets in source / git history |
| `semgrep` | Always | SAST via `p/security-audit` + `p/swift` rulesets |
| `xcodebuild analyze` | If `.xcodeproj` present and not skipped | Xcode static analyzer findings (heavy — requires build) |
| Entitlements snapshot | Always | Captures `*.entitlements` for review |
| Privacy Manifest snapshot | Always | Captures `PrivacyInfo.xcprivacy` for review |
| Purpose-strings snapshot | Always | Captures `Info.plist` `NS*UsageDescription` for review |

Reviewers must do more manual code reading than for the web audit —
the tooling is necessary but not sufficient.

## Sensitive Content

Reports describe vulnerabilities and may contain exploit details,
attack paths, and (in the emergency-exit case) credential names.
Because they live under `~/Reports/` outside any git repo by default,
they don't risk accidental commit. Review before sharing — especially
before sharing with App Review or any external party.

## Inherent Limitations

Apple security review cannot assess:
- Runtime ATS behavior (the source-level `NSExceptionDomains` may be
  overridden at build time)
- Effective entitlements after build (compare declared vs `codesign`
  output)
- Effective Privacy Manifest after build (App Store Connect validates)
- VoiceOver / Switch Control runtime behavior (separate accessibility
  audit)
- On-device behavior under different Accessibility / Privacy settings

Treat output as a structured starting point. Many findings require
runtime verification with built-app tooling before they can be
confirmed closed.

## References

- Subagent definition: [`../../subagents/audit-security-apple.md`](../../subagents/audit-security-apple.md)
- Apple Platform Security Guide: https://support.apple.com/guide/security/welcome/web
- Apple Privacy: https://developer.apple.com/privacy/
- Privacy Manifest documentation: https://developer.apple.com/documentation/bundleresources/privacy_manifest_files
- Required reason APIs: https://developer.apple.com/documentation/bundleresources/privacy_manifest_files/describing_use_of_required_reason_api
- App Sandbox: https://developer.apple.com/documentation/security/app_sandbox
- Hardened Runtime: https://developer.apple.com/documentation/security/hardened_runtime
- App Transport Security: https://developer.apple.com/documentation/security/preventing_insecure_network_connections
- StoreKit 2 verification: https://developer.apple.com/documentation/storekit/in-app_purchase/original_api_for_in-app_purchase/validating_receipts_with_the_app_store
- CWE: https://cwe.mitre.org/
- gitleaks: https://github.com/gitleaks/gitleaks
- semgrep: https://semgrep.dev/
