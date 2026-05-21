---
name: audit-apple-security
description: Dual-agent Apple platform security audit — native Apple apps against the Apple-specific threat model (Keychain, ATS, entitlements, App Sandbox, Hardened Runtime, StoreKit verification, CloudKit ACLs, WKWebView bridge safety, code signing). For backend services / web apps / IaC, use `audit-web-security`. Privacy compliance (Privacy Manifest, ATT, required-reason APIs) is covered separately by `audit-apple-privacy`.
---

# Apple Platform Security Audit

You are orchestrating a dual-agent security audit for native Apple
platform code (Swift / SwiftUI / UIKit / AppKit / WatchKit) against
Apple's platform-specific threat model.

**Required reading**: Before starting, read [`lib/audit-framework.md`](../lib/audit-framework.md).
This file specifies only the audit-specific deltas.

**Audit identifier**: `apple-security` — `$AUDIT_DIR` is
`~/Reports/<org>/<repo>/audits/<TS>-apple-security/`

**Scope**: Swift source files for native Apple apps. Obj-C coverage
is intentionally light — assume Swift unless `.m`/`.mm` files dominate.
For backend services / web apps / IaC / CI/CD / agent-config, use
`audit-web-security`. **Privacy compliance is a separate audit**:
Privacy Manifest, ATT, required-reason APIs, third-party SDK privacy
declarations live in `audit-apple-privacy`.

**Inherent limitations**: Apple security review is heavier on manual
code reading than tooling can support — fewer SAST tools exist for
Swift than for web ecosystems. Many findings require runtime
verification with `codesign --display --entitlements -`, Console.app,
or Xcode's Accessibility Inspector / Static Analyzer.

---

## Schema extensions

Beyond the framework baseline, add:

| Column | Description |
|---|---|
| `CWE/Apple` | CWE identifier where applicable + an Apple anchor (e.g. `CWE-522 / Apple:Keychain`, `Apple:JSBridge`). Required on every finding. |
| `Category` | One of: `Storage`, `ATS`, `URLScheme`, `IPC`, `Entitlements`, `CloudKit`, `StoreKit`, `WebView`, `Crypto`, `Logging`, `Dependency`, `Secrets` |
| `Platform` | `iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`, `visionOS`, or `Multi` |
| `Verification` | `code` (inspectable) or `runtime` (requires built app + codesign / Console.app / Xcode Static Analyzer) |

Full schema:
```
| ID | Severity | CWE/Apple | Category | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

---

## Categories

The audit reviews 12 categories (Privacy moved to `audit-apple-privacy`):

| Category | Covers |
|---|---|
| `Storage` | Keychain access groups, `kSecAttrAccessible*` flags, Secure Enclave, `NSFileProtection*`, never UserDefaults/plist for secrets |
| `ATS` | App Transport Security, `NSAllowsArbitraryLoads`, `NSExceptionDomains`, certificate pinning, TLS minimums |
| `URLScheme` | Custom URL scheme handlers (`application(_:open:options:)`), Universal Link domain verification (`apple-app-site-association`), deep link input validation |
| `IPC` | XPC peer verification (`audit_token` + codesign req), App Groups isolation, pasteboard leaks, document picker / open-in input handling |
| `Entitlements` | Least-privilege entitlements, App Sandbox, Hardened Runtime exceptions (`com.apple.security.cs.allow-jit`, `allow-unsigned-executable-memory`, `disable-library-validation`), code signing, provisioning, notarization |
| `CloudKit` | Public vs private DB scoping, record-level permissions, `CKShare` participant ACLs, shared zone permissions |
| `StoreKit` | StoreKit 2 `Transaction.currentEntitlements` consumed only via `VerificationResult.verified`; server-side validation recommended; `originalTransactionID`, `revocationDate` tracking |
| `WebView` | Never `UIWebView` (deprecated); `WKScriptMessageHandler` input validation; `evaluateJavaScript` with user input; `file://` scope via `loadFileURL`; `WKWebpagePreferences.allowsContentJavaScript` |
| `Crypto` | CryptoKit (preferred over CommonCrypto); keys in Keychain or Secure Enclave; `SecRandomCopyBytes` for crypto random; no MD5/SHA1/DES/RC4/ECB; no hardcoded keys/IVs; non-constant-time compare |
| `Logging` | `os_log` privacy qualifiers (`%{public}` only for non-sensitive); `print()`/`NSLog` removed from release builds (visible in Console.app); flag any logging of Keychain values, tokens, PII |
| `Dependency` | SPM `Package.resolved` audit, Cocoapods `Podfile.lock` review, XCFramework binary provenance, third-party SDK code quality |
| `Secrets` | Hardcoded credentials in source — emergency-exit case |

---

## Severity calibration

| Severity | Anchor examples |
|---|---|
| **Critical** | Live credentials hardcoded; `NSAllowsArbitraryLoads=true` shipping; StoreKit purchase used without `VerificationResult.verified`; WKWebView with `allowsContentJavaScript` loading arbitrary user URLs; CloudKit public DB for private user data; `disable-library-validation` Hardened Runtime exception without need |
| **High** | Weak Keychain accessibility (`AccessibleAlways` for sensitive data); missing cert pinning on financial/health API; `os_log` with `%{public}` on PII; URL scheme handler with no validation on state-changing path; XPC service without audit-token/codesign requirement; over-broad entitlement granted |
| **Medium** | Deprecated `UIWebView` usage in maintained code; Cocoapods without `Podfile.lock` committed; `arc4random` used where `SecRandomCopyBytes` would be appropriate; SPM dep without checksum verification; `print()`/`NSLog` in release config |
| **Low** | Minor entitlement pruning; deprecated-but-functional crypto with no immediate risk; defense-in-depth gaps |

---

## Compound findings

Apple-specific compound patterns:

- **Account takeover via URL scheme**: URL scheme without validation +
  WKWebView with JS bridge → code execution in app context via crafted
  deep link
- **Receipt forgery accepted**: StoreKit verified only on-device +
  permanent entitlement granted → forged purchase yields permanent
  access
- **Mass private-data exposure**: CloudKit public database + PII
  fields → all users can read all users' data
- **Physical-access exploit**: Weak Keychain accessibility + biometric
  not required → physical-access attacker reads credentials
- **Library injection**: Hardened Runtime exceptions
  (`disable-library-validation`) + dynamic library loading → arbitrary
  code at app startup

---

## Phase 1: Audit-specific orient

### Tooling

```bash
mkdir -p "$AUDIT_DIR/tooling-raw"

# Secrets
command -v gitleaks >/dev/null && \
  timeout 300 gitleaks detect --source "$PROJECT_CWD" \
    --report-format json \
    --report-path "$AUDIT_DIR/tooling-raw/gitleaks.json" \
    --no-banner 2>&1 | tee "$AUDIT_DIR/tooling-raw/gitleaks.log"

# Semgrep with Swift rules (limited but useful)
command -v semgrep >/dev/null && \
  timeout 600 semgrep --config=p/security-audit --config=p/swift \
    --json --output "$AUDIT_DIR/tooling-raw/semgrep.json" "$PROJECT_CWD" \
    2>&1 | tee "$AUDIT_DIR/tooling-raw/semgrep.log"

# Xcode static analyzer (heavy — requires build). Skip with SKIP_XCODEBUILD=1.
if [[ -z "$SKIP_XCODEBUILD" ]] && command -v xcodebuild >/dev/null; then
  PROJ=$(ls *.xcodeproj 2>/dev/null | head -1)
  [[ -n "$PROJ" ]] && {
    SCHEME=$(xcodebuild -project "$PROJ" -list 2>/dev/null \
      | awk '/Schemes:/{flag=1;next}/^$/{flag=0}flag{print $1; exit}')
    timeout 1800 xcodebuild analyze -project "$PROJ" -scheme "$SCHEME" \
      CODE_SIGNING_ALLOWED=NO -quiet \
      > "$AUDIT_DIR/tooling-raw/xcodebuild-analyze.log" 2>&1
  }
fi

# Source-level Apple artifact snapshots
find "$PROJECT_CWD" -name "*.entitlements" -not -path '*/.*' \
  -exec sh -c 'echo "=== $1 ==="; cat "$1"' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/entitlements-declared.txt" 2>&1

# Note: PrivacyInfo.xcprivacy and Info.plist purpose strings are
# audited by audit-apple-privacy, not this audit.
```

**Realistic caveat**: Apple-specific SAST is thinner than the web
ecosystem. Reviewers must do more manual code reading.

### Emergency exit — exposed credentials

After tooling runs, if `gitleaks.json` shows a live credential
(private key, API token with recognized prefix). For Apple specifically,
also flag whether the leaked credential is:

- A code-signing certificate (P12, .p8 file)
- An App Store Connect API key (`.p8`)
- A push notification certificate / APNs auth key
- A service-side key (Firebase, etc.)

Each has its own rotation procedure. Write `$AUDIT_DIR/EMERGENCY.md`
and halt before Phase 2.

### Survey

Beyond the framework baseline:

- Identify Apple project artifacts: `Package.swift` (+ `Package.resolved`),
  `*.xcodeproj/`, `*.xcworkspace/`, `Info.plist`, `*.entitlements`,
  `Podfile` + `Podfile.lock`
- Identify Swift files; detect frameworks via imports (`import Security`,
  `import CryptoKit`, `import LocalAuthentication`, `import StoreKit`,
  `import CloudKit`, `import WebKit`, `import NetworkExtension`,
  `import XPC`)
- Determine target platforms from `Package.swift` `platforms` array or
  `Info.plist`
- **Trust-boundary checklist** — Apple-specific:
  - Custom URL scheme handlers (`application(_:open:options:)`)
  - Universal Link handlers (`application(_:continue:restorationHandler:)`)
  - WKWebView script message handlers
  - WKWebView arbitrary URL loading
  - XPC service connections (incoming and outgoing)
  - App Groups shared containers
  - Pasteboard read/write surfaces
  - Document picker / document provider
  - File coordination with untrusted apps
  - Bonjour / mDNS (Local Network entitlement)
  - Network Extension consumers (VPN, content filter)
  - Push notification payload handling (`UNNotificationServiceExtension`)
  - Share extension input
  - Widget intent inputs
  - App Intents (`AppIntent`, Shortcuts) parameters
  - Custom keyboard / keyboard extension data

---

## Phase 2: Codex prompt body

Substitute into the canonical invocation (framework Phase 2 Step 1):

```text
Perform a thorough Apple platform security review of [RESOLVED_SCOPE].
Tooling has already been run; raw output is in $AUDIT_DIR/tooling-raw/.
Read those files first: gitleaks.json (secrets), semgrep.json (SAST),
xcodebuild-analyze.log (Xcode static analyzer), entitlements-declared.txt
(capability claims). Apple SAST is thinner than the web ecosystem —
most findings come from manual code reading. Validate, do not
duplicate, automated findings.

Write all findings to $AUDIT_DIR/codex.md using this exact table
format:
| ID | Severity | CWE/Apple | Category | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
where ID uses prefix C (e.g. C001, C002). Every finding MUST include a
CWE and/or Apple anchor (e.g. CWE-522 / Apple:Keychain) and a Category
from: Storage, ATS, URLScheme, IPC, Entitlements, CloudKit, StoreKit,
WebView, Crypto, Logging, Dependency, Secrets. Platform: iOS, iPadOS,
macOS, MacCatalyst, watchOS, tvOS, visionOS, or Multi.

DO NOT review Privacy Manifest, ATT, required-reason APIs, or
third-party SDK privacy declarations — those belong in
audit-apple-privacy, run separately.

Cover these 12 categories (skip if not applicable):
(1) Storage — Keychain access groups, kSecAttrAccessible* flags
(especially flagging AccessibleAlways when AccessibleWhenUnlocked-
ThisDeviceOnly would suffice); Secure Enclave for biometric-gated
keys; NSFileProtection class on stored files; never UserDefaults /
plist / CoreData unencrypted for secrets.
(2) ATS — flag NSAllowsArbitraryLoads=true; audit NSExceptionDomains
for cleartext or weak-TLS exceptions; certificate pinning gaps on
sensitive APIs; TLS 1.2+ minimums.
(3) URLScheme — custom URL scheme handlers must validate input;
Universal Link domain verification via apple-app-site-association;
deep link injection paths.
(4) IPC — XPC connections must verify peer via audit token and
codesign requirement; App Groups data isolation; UIPasteboard.general
sensitive-data writes; document picker / open-in input validation.
(5) Entitlements — review *.entitlements for least-privilege; flag
Hardened Runtime exceptions (com.apple.security.cs.* — allow-jit,
allow-unsigned-executable-memory, disable-library-validation) unless
clearly justified; App Sandbox on macOS; Network Extension flagged
for justification.
(6) CloudKit — public database used only for genuinely public data;
private DB with per-user ownership; CKShare participant ACLs; shared
zone permissions; CloudKit Web Services tokens never embedded.
(7) StoreKit — StoreKit 2 Transaction.currentEntitlements consumed
only via VerificationResult.verified (never .unverified); receipt
validation also server-side for non-consumable / subscription content;
originalTransactionID + revocationDate tracked; restores
re-validated.
(8) WebView — never UIWebView; WKScriptMessageHandler bridge inputs
validated; evaluateJavaScript never with user-controlled input
concatenated; file:// scoped via loadFileURL(_:allowingReadAccessTo:);
WKWebpagePreferences.allowsContentJavaScript false unless needed.
(9) Crypto — CryptoKit preferred; keys in Keychain or Secure Enclave;
SecRandomCopyBytes for crypto random (never arc4random_uniform); flag
MD5/SHA1/DES/RC4/ECB; no hardcoded keys/IVs.
(10) Logging — os_log MUST use %{public} only for non-sensitive
values; print()/NSLog removed from release builds; flag logging of
Keychain values, tokens, PII.
(11) Dependency — SPM Package.resolved committed; Cocoapods
Podfile.lock committed; XCFramework binary deps reviewed for
provenance.
(12) Secrets — verify no hardcoded API tokens, signing certs, push
certs, App Store Connect API keys (Phase 1 emergency-exit handles
the case where they're found).

Rate severity on evidence: impact, exploitability, blast radius,
reachability. Critical = live credentials in source, ATS arbitrary
loads shipping, StoreKit purchase without verification, WKWebView
with JS + arbitrary URLs, CloudKit public DB for private data.
High = weak Keychain accessibility, missing cert pinning on sensitive
APIs, os_log %{public} on PII, URL scheme without validation, XPC
without peer auth.

Every finding must include a Verification field — for Apple this often
means runtime verification with codesign / Console.app / Xcode static
analyzer. Note when verification requires a built app.

Do not read or reference any other review file.
```

## Phase 2: Claude review checklist

Same 12 categories. **Do not duplicate `audit-apple-privacy`** —
Privacy Manifest, ATT, required-reason APIs, purpose strings, and
third-party SDK privacy live there.

Note that many Apple security findings require runtime verification
(built app + `codesign --display --entitlements -`, Console.app for
`os_log` qualifiers). Mark Verification column `runtime` accordingly.

---

## Phase 4: Devil's advocate prompt body

```text
Read $AUDIT_DIR/synthesis.md and the raw tooling output in
$AUDIT_DIR/tooling-raw/. Your job is to attack the synthesis, not
improve it. Write your challenge to $AUDIT_DIR/devils-advocate.md
covering:
(1) False positives — findings that don't actually apply in context
(e.g. a Keychain accessibility flag flagged as weak is actually
correct for the data type; an entitlement flagged as broad is
required for documented Apple functionality; an ATS exception is for
a legitimate corp-managed domain; a WKWebView with JS bridge loads
only first-party HTML).
(2) Severity miscalibrations — findings rated too high or too low
given actual VoiceOver/Switch Control impact and user exclusion.
(3) Missing findings — Apple-specific issues both reviewers missed,
especially: side-channel via memory/disk caching, race conditions in
file coordination, NSXPCConnection auth gaps, App Group container
pollution, Universal Link domain verification gaps, Push payload
injection, App Intents parameter validation gaps, share extension
input handling, widget intent gaps, custom keyboard data exfil.
(4) Missing compound paths — separate findings that combine into a
worse exploit.
(5) Remediation steps that are impractical, incomplete, or wrong —
e.g. moving secrets from UserDefaults to Keychain but with
AccessibleAlways; switching to WKWebView but keeping JS bridge
unvalidated.
(6) Verification steps that don't actually prove the fix works —
Apple-specific verification often requires a built app + codesign or
Console.app; "manual review" verification is insufficient.
Be specific. Every challenge must cite the finding ID and reference
the CWE or Apple anchor.
```

---

## Phase 5: Sprint mapping override

Critical findings are operationally different — for Apple apps,
"Immediate Action" frequently means: pull the build from TestFlight,
hotfix, re-submit.

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | **Immediate Action — fix before next release / out-of-band patch** |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

---

## Output checklist additions

Beyond framework baseline:

- [ ] `$AUDIT_DIR/tooling-raw/` populated with at least gitleaks and
      semgrep, plus `entitlements-declared.txt`
- [ ] Every finding has a CWE or Apple anchor (CWE-XX / Apple:Topic)
- [ ] No Privacy Manifest / ATT / required-reason / purpose-string
      findings here — those belong in audit-apple-privacy
- [ ] Critical findings broken out into **Immediate Action** above P0
- [ ] Each task's Verification field describes the Apple-specific
      tooling needed
- [ ] Compound findings section populated when applicable
- [ ] Sensitive-content warning + TestFlight-pull guidance in hand-off
- [ ] Emergency-exit handled if triggered

---

## Reference

- Audit reference doc: [`docs/apple-security/README.md`](../docs/apple-security/README.md)
- Framework: [`lib/audit-framework.md`](../lib/audit-framework.md)
- Apple Platform Security Guide: https://support.apple.com/guide/security/welcome/web
- App Sandbox: https://developer.apple.com/documentation/security/app_sandbox
- Hardened Runtime: https://developer.apple.com/documentation/security/hardened_runtime
- App Transport Security: https://developer.apple.com/documentation/security/preventing_insecure_network_connections
- StoreKit 2 verification: https://developer.apple.com/documentation/storekit/in-app_purchase/original_api_for_in-app_purchase/validating_receipts_with_the_app_store
- CWE: https://cwe.mitre.org/
- gitleaks: https://github.com/gitleaks/gitleaks
- semgrep: https://semgrep.dev/
