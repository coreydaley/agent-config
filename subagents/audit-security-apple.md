---
name: audit-security-apple
description: Dual-agent Apple platform security audit — Claude and Codex review native Apple apps (iOS, iPadOS, macOS, watchOS, tvOS, visionOS) independently against Apple's platform-specific threat model: Keychain, App Transport Security, entitlements, App Sandbox, Hardened Runtime, Privacy Manifest, StoreKit receipt validation, CloudKit ACLs, WKWebView bridge safety, code signing. Runs available tooling (gitleaks, semgrep, Xcode static analyzer where feasible), synthesizes findings, devil's advocate pass, output as findings report with Critical findings broken out as Immediate Action. For backend services / web apps / IaC, use `audit-security-web-application` instead. Invoke with a scope path or leave empty to audit the current working directory.
---

# Apple Platform Security Audit: Dual-Agent Review

You are orchestrating a dual-agent **Apple platform** security audit
for native apps (iOS, iPadOS, macOS, watchOS, tvOS, visionOS, Mac
Catalyst). Available tooling runs first; Claude and Codex then review
independently against Apple's platform-specific threat model
(Keychain, ATS, entitlements, App Sandbox, Hardened Runtime, Privacy
Manifest, StoreKit, CloudKit, WKWebView, code signing). Findings are
synthesized, Codex attacks the synthesis, and the final output is a
sprint document written to `$AUDIT_DIR/REPORT.md`.

For **backend services / web applications / IaC / CI/CD / agent-config**,
use `audit-security-web-application` — the threat model (OWASP Top 10,
injection, SSRF, K8s misconfigs) is largely disjoint from Apple-native
concerns.

The scope to audit is provided in your input prompt. If no scope is
specified, audit the current working directory.

## Scope Handling

Parse your input prompt for a path or paths to audit. Examples:
- No path specified → scope is the current working directory
- `Sources/App` → scope is `Sources/App`
- `App/Features Shared/Auth` → scope is multiple paths
- `--diff-only` → scope is files changed in `git diff main...HEAD`

Scope is validated as a path in Phase 1 before being used anywhere else —
raw user input is never interpolated into shell strings.

## Workflow Overview

This is a **5-phase workflow** with an emergency-exit early in Phase 1:

1. **Orient** — Determine scope, detect Apple project type and target
   platforms, run available tooling (gitleaks, semgrep, optionally
   `xcodebuild analyze`), enumerate trust boundaries, **halt early if
   exposed credentials are found in source**
2. **Independent Reviews** — Claude and Codex review in parallel,
   grounded in the tooling output from Phase 1
3. **Synthesis** — Deduplicate findings; flag agreements as higher
   confidence; calibrate severity against the rubric; note compound
   findings
4. **Devil's Advocate** — Codex attacks the synthesis for false
   positives, severity miscalibrations, and gaps
5. **Report Output** — Produce `$AUDIT_DIR/REPORT.md` with findings as
   tasks, with Critical findings broken out as "Immediate Action"
   above P0

**Inherent limitations**: Apple security review is heavier on manual
code reading than tooling can support — fewer static-analysis tools
exist for Swift/Obj-C than for web ecosystems. Many findings require
runtime verification with Xcode's Accessibility Inspector,
`codesign --display --entitlements`, the App Privacy Report on device,
or App Store Connect's Privacy Manifest validation. Treat this audit
as a structured starting point, not a conformance certification.

---

## Finding Schema

All intermediate audit files must use this table format so synthesis
and devil's advocate phases operate on consistent data:

```
| ID | Severity | CWE/Apple | Category | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
|----|----------|-----------|----------|-------|----------|----------|--------------|----------------|-----------------|----------------|
| X001 | High | CWE-522 / Apple:Keychain | Storage | Short title | App/AuthStore.swift:42 | iOS,iPadOS | code | Impact explanation | Concrete fix | Code quote |
```

**ID prefix convention:**
- Claude's review: `A001`, `A002`... (Audit)
- Codex's review: `C001`, `C002`... (Codex)
- Synthesis: `S001`, `S002`... (Synthesis canonical)

**CWE/Apple column**: Map every finding to a CWE identifier where
applicable and an Apple-platform anchor. Examples:
- `CWE-522 / Apple:Keychain` — insufficiently protected credentials
- `CWE-319 / Apple:ATS` — cleartext transmission (NSAllowsArbitraryLoads)
- `CWE-925 / Apple:URLScheme` — URL scheme without origin validation
- `CWE-749 / Apple:JSBridge` — exposed dangerous WKScriptMessageHandler
- `CWE-326 / Apple:Crypto` — weak crypto / wrong Keychain accessibility
- `CWE-285 / Apple:Entitlements` — over-broad entitlement granted
- `CWE-200 / Apple:Logging` — `os_log` with `%{public}` on PII
- `Apple:PrivacyManifest` — missing or incomplete `PrivacyInfo.xcprivacy`
- `Apple:StoreKit` — purchase used without `VerificationResult.verified`
- `Apple:CloudKit` — public database used where private+share appropriate

A finding without a CWE or Apple anchor is not a valid finding and must
be omitted.

**Category column** (one per finding):

| Category | Covers |
|---|---|
| `Storage` | Keychain access groups + `kSecAttrAccessible*` flags, Secure Enclave, `NSFileProtection*`, never UserDefaults/plist for secrets |
| `ATS` | App Transport Security, `NSAllowsArbitraryLoads`, `NSExceptionDomains`, certificate pinning, TLS minimums |
| `URLScheme` | Custom URL scheme handlers, Universal Links (`apple-app-site-association`), deep link input validation |
| `IPC` | XPC service auth (audit_token, codesign req), App Groups isolation, pasteboard leaks, document handling |
| `Entitlements` | Least-privilege entitlements, App Sandbox, Hardened Runtime exceptions, code signing, provisioning profile, notarization |
| `Privacy` | `PrivacyInfo.xcprivacy`, `Info.plist` purpose strings, ATT/IDFA, required-reason API declarations |
| `CloudKit` | Public vs private DB scoping, record-level permissions, `CKShare` participant validation, shared zone ACLs |
| `StoreKit` | StoreKit 2 `VerificationResult` handling, server-side receipt validation, `originalTransactionID`, `revocationDate` |
| `WebView` | WKWebView (never UIWebView), `WKScriptMessageHandler` bridge safety, `evaluateJavaScript` with user input, `file://` access |
| `Crypto` | CryptoKit usage, Secure Enclave for sensitive keys, `SecRandomCopyBytes` for crypto random, no MD5/SHA1/DES, no hardcoded keys |
| `Logging` | `os_log` privacy qualifiers (`%{public}` vs `%{private}`), `print()`/`NSLog` removed from release, crash report PII |
| `Dependency` | SPM `Package.resolved` audit, Cocoapods `Podfile.lock`, third-party SDK data collection, XCFramework provenance |
| `Secrets` | Hardcoded credentials in source (Keychain keys, API tokens, signing keys) — handled by emergency-exit if found |

**Platform column**: Which Apple platforms are affected. Values:
`iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`, `visionOS`,
or `Multi` for cross-platform code. Combine when relevant
(e.g. `iOS,iPadOS`).

**Verification column**: `code` (inspectable from source alone) or
`runtime` (requires built app + `codesign --display --entitlements -`,
Console.app, Xcode static analyzer, Accessibility Inspector, App Privacy
Report on device, or App Store Connect Privacy Manifest validation).

**Severity levels:** Critical, High, Medium, Low

### Severity Calibration

Same evidence framework as `audit-security-web-application`:

- **Impact** — what does an exploit achieve? (credential exfil, data
  leak, fraudulent purchase, privacy violation, privilege escalation,
  App Store rejection)
- **Exploitability** — what attacker capability is required?
  (any installed app on device, jailbroken device, network attacker,
  malicious server, malicious user input)
- **Blast radius** — single user, all users of a feature, all users of
  the app, all users sharing a CloudKit zone
- **Reachability** — is the vulnerable code on a hot path, behind
  authentication, or only in a dev build configuration?

Severity anchors (starting point — override based on the four factors
above):

| Severity | Anchor examples |
|---|---|
| **Critical** | Live credentials hardcoded in source; `NSAllowsArbitraryLoads=true` shipping; StoreKit purchase used without `VerificationResult.verified`; WKWebView with `allowsContentJavaScript` loading arbitrary user URLs; CloudKit public database used for private user data; `disable-library-validation` Hardened Runtime exception without need; missing `PrivacyInfo.xcprivacy` for an app shipping post-May-2024 (App Store rejection) |
| **High** | Weak Keychain accessibility (`AccessibleAlways` for sensitive data); missing certificate pinning on financial/health API; `os_log` with `%{public}` on PII; URL scheme handler with no validation on a state-changing path; XPC service without audit-token / codesign requirement; over-broad entitlement granted (e.g. `Apple Events` to all targets when one suffices); StoreKit receipt validated only on-device |
| **Medium** | Deprecated `UIWebView` usage in maintained code; missing purpose strings for sensitive resources (Info.plist); Cocoapods without `Podfile.lock` committed; `arc4random` used where `SecRandomCopyBytes` would be appropriate; SPM dep without checksum verification; `print()`/`NSLog` left in release configuration |
| **Low** | Minor entitlement pruning opportunities; deprecated-but-functional crypto with no immediate risk; defense-in-depth gaps with no current exploit |

Agreement between reviewers raises **confidence**, not severity.
Severity is also independent of remediation cost.

### Compound Findings

When two or more separate findings combine to enable a worse exploit
than either alone, the synthesis must add a `Compounded By` note:

- **Account takeover via URL scheme**: URL scheme without validation
  (`S003`) + WKWebView with JS bridge (`S007`) → arbitrary code in
  app context via a crafted deep link
- **Receipt forgery accepted**: StoreKit verified on-device only
  (`S005`) + entitlement granted permanently (`S009`) → forged
  purchase yields permanent entitlement
- **Private data exposure**: CloudKit public database (`S001`) +
  PII fields on record (`S002`) → all users of the app can read all
  users' data

Reviewers should call these out explicitly during synthesis rather
than treating each in isolation.

---

## Phase 1: Orient

**Goal**: Validate scope, **detect Apple project type and run available
tooling**, enumerate trust boundaries, halt early if exposed
credentials are found, and determine the output location.

### Orient Steps

1. **Validate and resolve scope** from the input prompt:
   - If no path specified: scope is the current working directory
   - If a path is provided: verify the path exists
   - If `--diff-only`: scope is files changed in `git diff main...HEAD`
   - Exclude: `.build/`, `DerivedData/`, `Pods/`, `Carthage/Build/`,
     `.swiftpm/`, generated files, and vendored third-party Swift code
     unless explicitly included
   - Store the resolved scope path — do not use raw input text in any
     Codex exec prompt string

2. **Identify Apple project artifacts** in or above the resolved scope:
   - `Package.swift` (Swift Package Manager) — and `Package.resolved`
   - `*.xcodeproj/`, `*.xcworkspace/` (Xcode project)
   - `Info.plist` — declared target capabilities and supported platforms
   - `*.entitlements` files — capability and sandbox claims
   - `PrivacyInfo.xcprivacy` — privacy manifest (required since May 2024
     for App Store submissions)
   - `Podfile` and `Podfile.lock` (Cocoapods)
   - `*.xcassets/` — asset catalogs (App Icon, accent color)
   - Storyboards and XIBs (`*.storyboard`, `*.xib`) — legacy but still
     relevant

3. **Identify Swift / Obj-C source** in the resolved scope and detect
   frameworks via imports:
   - `*.swift`, `*.m`, `*.mm`, `*.h` files
   - `import SwiftUI`, `import UIKit`, `import AppKit` / `import Cocoa`,
     `import WatchKit`, `import WidgetKit`, `import ActivityKit`
   - `import Security` (Keychain APIs), `import CryptoKit`,
     `import LocalAuthentication`, `import StoreKit`, `import CloudKit`,
     `import WebKit`, `import NetworkExtension`, `import XPC`

4. **Determine target platforms**: read `Package.swift` `platforms` array
   or `Info.plist` to identify which Apple platforms this code ships
   on. Record this — it determines which Platform values are valid for
   findings and which APIs apply.

5. **No Apple source files found**: if no Swift/Obj-C files exist in
   the resolved scope, notify the user and stop:
   > No Apple platform source files found in [scope]. Re-scope to a
   > directory containing Apple app code, or use
   > `/audit-security-web-application` if this is a backend/services
   > codebase.
   Do not create a sprint or artifact files.

6. **Determine output location**:
   ```bash
   REMOTE=$(git remote get-url upstream 2>/dev/null || git remote get-url origin 2>/dev/null || echo "")
   ORG_REPO=$(echo "$REMOTE" | sed 's|.*github\.com[:/]||; s|\.git$||')
   REPORTS_BASE="$HOME/Reports/$ORG_REPO"
   REPORT_TS=$(date +%Y-%m-%dT%H-%M-%S)
   AUDIT_DIR="$REPORTS_BASE/audits/$REPORT_TS-security-apple"
   PROJECT_CWD="$(pwd)"
   mkdir -p "$AUDIT_DIR/tooling-raw"
   ```

7. **Run available tooling** (best-effort; capture stdout+stderr;
   document what ran in `$AUDIT_DIR/tooling-raw/STATUS.md`):

   ```bash
   # Secret scanning (always run if gitleaks is installed)
   command -v gitleaks >/dev/null && \
     timeout 300 gitleaks detect --source "$PROJECT_CWD" --report-format json \
       --report-path "$AUDIT_DIR/tooling-raw/gitleaks.json" \
       --no-banner 2>&1 | tee "$AUDIT_DIR/tooling-raw/gitleaks.log"

   # Semgrep with Swift / mobile rulesets
   command -v semgrep >/dev/null && \
     timeout 600 semgrep --config=p/security-audit --config=p/swift \
       --json --output "$AUDIT_DIR/tooling-raw/semgrep.json" "$PROJECT_CWD" \
       2>&1 | tee "$AUDIT_DIR/tooling-raw/semgrep.log"

   # Xcode static analyzer — runs the same checks as Build > Analyze.
   # Heavy: requires a full build. Skip if no .xcodeproj or if BUILD_TIME
   # budget is tight. Caller can set SKIP_XCODEBUILD=1 to bypass.
   if [[ -z "$SKIP_XCODEBUILD" ]] && command -v xcodebuild >/dev/null; then
     PROJ=$(ls *.xcodeproj 2>/dev/null | head -1)
     [[ -n "$PROJ" ]] && \
       timeout 1800 xcodebuild analyze -project "$PROJ" \
         -scheme "$(xcodebuild -project "$PROJ" -list 2>/dev/null | awk '/Schemes:/{flag=1;next}/^$/{flag=0}flag{print $1; exit}')" \
         CODE_SIGNING_ALLOWED=NO -quiet \
         > "$AUDIT_DIR/tooling-raw/xcodebuild-analyze.log" 2>&1
   fi

   # Inspect declared entitlements (source-level — what we asked for)
   find "$PROJECT_CWD" -name "*.entitlements" -not -path '*/.*' \
     -exec sh -c 'echo "=== $1 ==="; cat "$1"' _ {} \; \
     > "$AUDIT_DIR/tooling-raw/entitlements-declared.txt" 2>&1

   # Inspect Privacy Manifest if present
   find "$PROJECT_CWD" -name "PrivacyInfo.xcprivacy" -not -path '*/.*' \
     -exec sh -c 'echo "=== $1 ==="; cat "$1"' _ {} \; \
     > "$AUDIT_DIR/tooling-raw/privacy-manifest.txt" 2>&1

   # Inspect Info.plist purpose strings
   find "$PROJECT_CWD" -name "Info.plist" -not -path '*/.*' \
     -not -path '*/Pods/*' \
     -exec sh -c 'echo "=== $1 ==="; /usr/libexec/PlistBuddy -c "Print" "$1" 2>/dev/null | grep -E "UsageDescription|NSApp" || cat "$1" | grep -A1 "UsageDescription"' _ {} \; \
     > "$AUDIT_DIR/tooling-raw/info-plist-purpose-strings.txt" 2>&1
   ```

   **Realistic caveat**: Apple-specific static analysis tools are
   thinner than the web ecosystem. Reviewers must do more manual code
   reading; tooling output is necessary but not sufficient.

   If a tool isn't installed, isn't applicable, or fails: write a line
   to `$AUDIT_DIR/tooling-raw/STATUS.md` and continue.

8. **🚨 EMERGENCY EXIT — exposed credentials**:

   After step 7, if `gitleaks.json` (or manual inspection) shows what
   appears to be a live credential (private key, API token with a
   recognized prefix like `ghp_`, `sk_live_`, `AKIA`, etc.) committed
   to the working tree:

   - **HALT the audit immediately**. Do not proceed to Phase 2.
   - Write `$AUDIT_DIR/EMERGENCY.md` with: which file, which line,
     which credential type was matched, and the rotation steps
     (rotate at provider → purge from git history → invalidate any
     downstream usage).
   - For Apple-app context: also flag whether the leaked credential is
     a code-signing certificate, App Store Connect API key, push
     notification certificate, or service-side key — each has its own
     rotation procedure.
   - Tell the user out-of-band in the conversation: this is a
     rotate-immediately event.
   - Only resume the full audit after the user has confirmed rotation
     is underway.

9. **Survey the scope and enumerate Apple-specific trust boundaries**:
   - Review recent changes: `git log --oneline -20`
   - For `--diff-only` mode, focus reviewers on the changed surface
   - **Explicit trust-boundary checklist** (enumerate which apply,
     before findings begin):
     - Custom URL scheme handlers (`application(_:open:options:)`)
     - Universal Link handlers (`application(_:continue:restorationHandler:)`)
     - WKWebView script message handlers (`WKScriptMessageHandler`)
     - WKWebView arbitrary URL loading
     - XPC service connections (incoming and outgoing)
     - App Groups shared containers
     - Pasteboard read/write surfaces
     - Document picker / document provider handling
     - File coordination with untrusted apps
     - Bonjour / mDNS service exposure (Local Network entitlement)
     - Network Extension entitlement consumers (VPN, content filters)
     - Push notification payload handling (`UNNotificationServiceExtension`)
     - Share extension input
     - Widget intent inputs
     - App Intents (`AppIntent`, Shortcuts) parameter validation
     - Inter-process keyboard / shared keyboard extensions

### Orient Deliverable

A brief orientation note (6-8 bullets) covering:
- Resolved scope and what it includes/excludes (note `--diff-only`)
- Detected frameworks (SwiftUI / UIKit / AppKit / etc.) and Swift/Obj-C
  file count
- Target platforms from `Package.swift` / `Info.plist`
- Capability surfaces detected: Keychain usage, ATS exceptions in
  `Info.plist`, declared entitlements summary, Privacy Manifest
  presence, StoreKit / CloudKit / WebKit / NetworkExtension imports
- Tooling that ran successfully vs. tooling missing
- **Whether the emergency-exit triggered** (yes/no)
- Enumerated trust-crossing surfaces (the checklist above, filtered)
- Audit output directory (`AUDIT_DIR`)

---

## Phase 2: Independent Reviews (Parallel)

**Goal**: Get two independent Apple-platform security perspectives,
both grounded in the tooling output from Phase 1.

### Step 1 — Launch Codex in Background

The flags below are non-negotiable; see [`lib/codex-invocation.md`](../lib/codex-invocation.md) for per-flag rationale and failure modes. `--add-dir` points at `$AUDIT_DIR` so Codex can write its artifact under `~/Reports/`; `-C` points at `$PROJECT_CWD` so Codex reads the code being audited.

```bash
codex exec \
  -s workspace-write \
  --add-dir "$AUDIT_DIR" \
  -C "$PROJECT_CWD" \
  -- "Perform a thorough Apple platform security review of [RESOLVED_SCOPE]. \
  Tooling has already been run; raw output is in $AUDIT_DIR/tooling-raw/. \
  Read those files first: gitleaks.json (secrets), semgrep.json \
  (SAST), xcodebuild-analyze.log (Xcode static analyzer), \
  entitlements-declared.txt (capability claims), privacy-manifest.txt \
  (PrivacyInfo.xcprivacy), info-plist-purpose-strings.txt. \
  Apple-specific static tooling is thinner than the web ecosystem — \
  most findings will come from manual code reading. Validate, do not \
  duplicate, automated findings. \
  Write all findings to $AUDIT_DIR/codex.md using this exact \
  table format for each finding: \
  | ID | Severity | CWE/Apple | Category | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes | \
  where ID uses prefix C (e.g. C001, C002). Every finding MUST include \
  a CWE and/or Apple-platform anchor (e.g. CWE-522 / Apple:Keychain) \
  and a Category from: Storage, ATS, URLScheme, IPC, Entitlements, \
  Privacy, CloudKit, StoreKit, WebView, Crypto, Logging, Dependency, \
  Secrets. Platform column: iOS, iPadOS, macOS, MacCatalyst, watchOS, \
  tvOS, visionOS, or Multi. Verification: code or runtime (where \
  runtime means requires built app + codesign / Console.app / Xcode \
  Static Analyzer / Accessibility Inspector / App Privacy Report). \
  Cover these 13 categories (skip any not applicable to the scope): \
  (1) Storage — Keychain access groups, kSecAttrAccessible* flags \
  (especially flagging AccessibleAlways or AccessibleAfterFirstUnlock \
  when AccessibleWhenUnlockedThisDeviceOnly would suffice); Secure \
  Enclave for biometric-gated keys; NSFileProtection class on stored \
  files; never UserDefaults/plist/CoreData unencrypted for secrets. \
  (2) ATS — App Transport Security: flag NSAllowsArbitraryLoads=true, \
  audit NSExceptionDomains for any cleartext or weak-TLS exceptions, \
  certificate pinning gaps on sensitive APIs, missing TLS 1.2+ minimums. \
  (3) URLScheme — custom URL scheme handlers must validate input; \
  Universal Link domain verification via apple-app-site-association; \
  flag application(_:open:options:) handlers that route to state-changing \
  paths without authentication or input validation. \
  (4) IPC — XPC service connections must verify peer via audit token \
  and codesign requirement string; App Groups data must not leak across \
  trust boundaries; UIPasteboard.general writes of sensitive data; \
  document picker / open-in handler input validation. \
  (5) Entitlements — review *.entitlements files for least-privilege \
  violations; flag Hardened Runtime exceptions (com.apple.security.cs.\\\\* \
  especially allow-jit, allow-unsigned-executable-memory, \
  disable-library-validation) unless clearly justified; sandbox entitlement \
  required on macOS for App Store; Network Extension and other powerful \
  entitlements flagged for justification. \
  (6) Privacy — PrivacyInfo.xcprivacy MUST be present and accurate for \
  App Store submissions since May 2024; Info.plist purpose strings \
  (NS*UsageDescription) MUST be present for every sensitive resource \
  the app accesses; App Tracking Transparency (ATT) flow required if \
  IDFA accessed; required-reason API declarations (UserDefaults, \
  fileTimestamp, systemBootTime, diskSpace APIs). \
  (7) CloudKit — public database used only for genuinely public data; \
  private database with per-user ownership; CKShare participant ACLs; \
  shared zone permissions; CloudKit Web Services tokens never embedded. \
  (8) StoreKit — StoreKit 2 Transaction.currentEntitlements consumed \
  only via VerificationResult.verified (never .unverified); receipt \
  validation should also happen server-side for non-consumable / \
  subscription content; originalTransactionID and revocationDate \
  tracked; restoring purchases re-validates. \
  (9) WebView — never UIWebView (deprecated, insecure); WKWebView \
  WKScriptMessageHandler bridge inputs validated; evaluateJavaScript \
  never called with user-controlled input concatenated; file:// access \
  scoped via loadFileURL(_:allowingReadAccessTo:); \
  WKWebpagePreferences.allowsContentJavaScript false unless needed. \
  (10) Crypto — CryptoKit preferred over CommonCrypto for new code; \
  symmetric keys stored in Keychain or generated in Secure Enclave; \
  SecRandomCopyBytes for crypto random (never arc4random_uniform); \
  flag MD5, SHA1, DES, RC4, ECB mode; no hardcoded keys / IVs. \
  (11) Logging — os_log MUST use %{public} qualifier only for \
  non-sensitive values (default qualifier is %{private}, which is still \
  visible to attached debugger); print() / NSLog removed from release \
  builds (use compile-time flag like #if DEBUG); flag any logging of \
  Keychain values, tokens, user PII. \
  (12) Dependency — SPM Package.resolved committed; Cocoapods \
  Podfile.lock committed; third-party SDK Privacy Manifests reviewed \
  (each SDK >100MB or with API tracking obligations must have its own); \
  XCFramework binary deps reviewed for provenance. \
  (13) Secrets — any hardcoded credential triggers the emergency-exit \
  in Phase 1; verify no leftover hardcoded API tokens, signing certs, \
  Push notification certs, App Store Connect API keys. \
  Rate severity on evidence: impact, exploitability, blast radius, \
  reachability. Critical = live credentials in source, ATS arbitrary \
  loads shipping, StoreKit purchase without verification, WKWebView \
  with JS + arbitrary URLs, CloudKit public DB for private data, \
  PrivacyManifest missing on App Store-shipping app. \
  High = weak Keychain accessibility, missing cert pinning on \
  sensitive APIs, os_log %{public} on PII, URL scheme without \
  validation, XPC without peer auth. \
  Medium = UIWebView in maintained code, missing purpose strings, \
  arc4random for crypto, missing Podfile.lock. \
  Low = minor entitlement pruning, deprecated-but-functional crypto, \
  print() left in code. \
  Every finding must include a Verification field describing how to \
  confirm the fix — for Apple, this often means runtime verification \
  with codesign / Console.app / Xcode static analyzer / App Privacy \
  Report / App Store Connect Privacy Manifest validation. Note when \
  verification requires a built app. \
  Do not read or reference any other review file." \
  < /dev/null
```

### Step 1.5 — Verify the Codex artifact

The most common Codex failure mode is silent (sandbox denial, missing flag,
prompt parse error — see `lib/codex-invocation.md`). After the background
Codex job returns, verify:

```bash
[[ -s "$AUDIT_DIR/codex.md" ]] && grep -q '|.*|.*|' "$AUDIT_DIR/codex.md" \
  || echo "⚠️ Codex did not produce a usable $AUDIT_DIR/codex.md"
```

If verification fails: inspect the Codex stderr output, fix the issue if
identifiable, and re-run the command once. Only after a second failure
should you accept the single-agent degradation documented in Phase 3.

### Step 2 — Claude's Independent Review (Simultaneous)

While Codex runs, write your own independent Apple security review to
`$AUDIT_DIR/claude.md` using the same finding schema (ID prefix `A`).
Read `$AUDIT_DIR/tooling-raw/` first.

Cover the same 13 categories listed in Codex's prompt above:

1. **Storage** — Keychain accessibility flags, Secure Enclave, NSFileProtection, never UserDefaults for secrets
2. **ATS** — `NSAllowsArbitraryLoads`, `NSExceptionDomains` audit, cert pinning, TLS minimums
3. **URLScheme** — `application(_:open:options:)` validation, Universal Links, deep link injection
4. **IPC** — XPC peer verification (audit token + codesign req), App Groups, pasteboard, document handling
5. **Entitlements** — least-privilege, Hardened Runtime exceptions, App Sandbox, Network Extension, provisioning
6. **Privacy** — `PrivacyInfo.xcprivacy` presence + accuracy, `Info.plist` purpose strings, ATT/IDFA, required-reason APIs
7. **CloudKit** — public vs private DB scoping, record ACLs, `CKShare` validation, shared zones
8. **StoreKit** — `VerificationResult.verified` consumption, server-side validation, `originalTransactionID`, restores
9. **WebView** — WKWebView only, JS bridge inputs, `evaluateJavaScript` with user data, `file://` scope
10. **Crypto** — CryptoKit, Secure Enclave, `SecRandomCopyBytes`, no MD5/SHA1/DES, no hardcoded keys
11. **Logging** — `os_log` privacy qualifiers, `print()`/`NSLog` in release, PII in logs
12. **Dependency** — SPM `Package.resolved`, Cocoapods `Podfile.lock`, third-party SDK Privacy Manifests, XCFramework provenance
13. **Secrets** — hardcoded credentials (emergency-exit case)

Note: many Apple findings require runtime verification (built app +
`codesign --display --entitlements -`, Console.app, App Privacy Report
on device). Mark Verification column `runtime` accordingly.

Wait for Codex to finish before proceeding to Phase 3.

---

## Phase 3: Synthesis

**Goal**: Produce a unified, deduplicated finding list with calibrated
severity, confidence, and explicit compound-finding notes.

### Synthesis Steps

1. **Verify both reviews exist and are non-empty**:
   - If Phase 2 Step 1.5 already triggered a single-agent fallback,
     the synthesis warning was already decided there
   - Otherwise, check `$AUDIT_DIR/claude.md` and `$AUDIT_DIR/codex.md`
     contain at least one finding row each
   - If one is missing or empty: add a prominent warning at the top of
     `$AUDIT_DIR/synthesis.md`: "⚠️ Single-agent synthesis — [agent]
     review was unavailable. Coverage may be incomplete."

2. **Deduplicate findings**:
   - Compare both reviews for overlapping findings
   - When the same issue appears in both, merge into one synthesis row —
     note both source IDs (e.g. `A002, C003`)
   - When merging: preserve the most specific `Location` and the best
     `Evidence/Notes`; preserve the most specific `Platform` (if one
     reviewer noted iOS+iPadOS and the other just iOS, keep the broader)
   - Agreement = higher confidence, not higher severity

3. **Calibrate severity** against the rubric in the Finding Schema
   section. Do not automatically escalate severity because both
   reviewers flagged the same issue.

4. **Identify compound findings**: scan all unified findings for pairs
   or chains that combine into a worse exploit. Apple-specific compound
   patterns to watch for:
   - URL scheme without validation + WKWebView with JS bridge → code
     execution in app context
   - StoreKit verified only on-device + permanent entitlement granted
     → forged purchase yields permanent access
   - CloudKit public DB + PII in record → mass user data exposure
   - Weak Keychain accessibility + biometric not required → physical-
     access attacker reads creds
   - Hardened Runtime exceptions + dynamic library loading → arbitrary
     code execution at app startup

5. **Write synthesis** to `$AUDIT_DIR/synthesis.md`:

   ```markdown
   # Apple Security Audit Synthesis — [REPORT_TS]

   ## Scope
   [Resolved scope path(s); note --diff-only if used]

   ## Target Platforms
   [iOS / iPadOS / macOS / etc., from Package.swift or Info.plist]

   ## Capability Surfaces Detected
   [Summary from Phase 1: declared entitlements, ATS exceptions, frameworks
   in use (WebKit / CloudKit / StoreKit / NetworkExtension / etc.),
   Privacy Manifest status]

   ## Tooling Summary
   - Ran: [list]
   - Skipped/failed: [list with reason]
   - Emergency exit triggered: [yes/no]

   ## Summary
   - Total findings: N (Critical: X, High: X, Medium: X, Low: X)
   - By category: Storage: X, ATS: X, ... (only non-zero)
   - Reviewers: Claude (A-prefix), Codex (C-prefix)
   - [Single-agent warning if applicable]

   ## Unified Findings

   | ID | Severity | CWE/Apple | Category | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes | Sources |
   |----|----------|-----------|----------|-------|----------|----------|--------------|----------------|-----------------|----------------|---------|
   | S001 | ... | Apple:Keychain | Storage | ... | ... | iOS | code | ... | ... | ... | A001, C002 |

   ## Compound Findings
   [Pairs/chains that escalate when combined.]

   ## Findings Present in Only One Review
   [Uncorroborated findings with rationale for retaining or dropping]
   ```

Phase 3 is complete when `$AUDIT_DIR/synthesis.md` is written.

---

## Phase 4: Devil's Advocate

**Goal**: Challenge the synthesis for false positives, severity
miscalibrations, missed findings, and missed compound paths.

### Step 1 — Launch Codex Devil's Advocate

```bash
codex exec \
  -s workspace-write \
  --add-dir "$AUDIT_DIR" \
  -C "$PROJECT_CWD" \
  -- "Read $AUDIT_DIR/synthesis.md and the raw tooling output in \
  $AUDIT_DIR/tooling-raw/. Your job is to attack the synthesis, not \
  improve it. Write your challenge to $AUDIT_DIR/devils-advocate.md \
  covering: \
  (1) False positives — findings that don't actually apply in context \
  (e.g. a Keychain accessibility flag flagged as weak is actually \
  correct for the data type; an entitlement flagged as broad is \
  required for documented Apple functionality; an ATS exception is \
  for a legitimate corp-managed domain; a WKWebView with JS bridge \
  loads only first-party HTML). \
  (2) Severity miscalibrations — findings rated too high (low-impact, \
  well-mitigated) or too low (under-counting App Store rejection risk, \
  under-counting CloudKit public-DB blast radius). \
  (3) Missing findings — Apple-specific issues both reviewers missed, \
  especially: side-channel via memory/disk caching, race conditions in \
  file coordination, NSXPCConnection auth gaps, App Group container \
  pollution, Universal Link domain verification gaps, Push payload \
  injection, App Intents parameter validation gaps, share extension \
  input handling, widget intent gaps, custom keyboard data exfil. \
  (4) Missing compound paths — separate findings that combine into a \
  worse exploit. \
  (5) Remediation steps that are impractical, incomplete, or wrong — \
  e.g. moving secrets from UserDefaults to Keychain but with \
  AccessibleAlways; switching to WKWebView but keeping JS bridge \
  unvalidated. \
  (6) Verification steps that don't actually prove the fix works — \
  Apple-specific verification often requires a built app + \
  codesign --display --entitlements - / Console.app / App Privacy \
  Report on device; a 'manual review' verification is insufficient. \
  Be specific. Every challenge must cite the finding ID and reference \
  the CWE or Apple anchor." \
  < /dev/null
```

After the call, verify the artifact: `[[ -s "$AUDIT_DIR/devils-advocate.md" ]] || echo "⚠️ Codex devil's advocate produced no output"`.

### Step 2 — Incorporate Valid Challenges

Once `$AUDIT_DIR/devils-advocate.md` is written, read it and:

- **Remove** confirmed false positives from the working finding list
- **Recalibrate** severity where the challenge is valid and evidence
  supports it
- **Add** genuinely missed findings with new synthesis IDs
- **Add** missed compound paths to the synthesis's Compound Findings
  section
- **Document every rejected challenge** in a "Rejected Challenges"
  section at the bottom of `$AUDIT_DIR/synthesis.md`:

  ```markdown
  ## Rejected Devil's Advocate Challenges

  | Finding/Claim | Reason Rejected |
  |---|---|
  | [Claim from devil's advocate] | [Why it was not accepted] |
  ```

Phase 4 is complete when challenges are incorporated and rejections
are documented.

---

## Phase 5: Report Output

**Goal**: Produce a findings report at `$AUDIT_DIR/REPORT.md` with
Apple security findings as sprint tasks, **Critical findings broken
out as "Immediate Action" above P0**.

### Sprint Mapping Rules

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | **Immediate Action — fix before next release / out-of-band patch** |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

For Apple apps, "Immediate Action" frequently means: pull the build
from TestFlight, hotfix, re-submit. Critical findings should not wait
for a planned release window.

Each task must include:
- Finding ID (from synthesis)
- CWE / Apple anchor
- Category
- Platform(s) affected
- Verification mode (`code` or `runtime`)
- File and line reference where applicable
- Clear description of the issue
- Concrete remediation: the specific Apple API to add/change and where
- **Verification step**: ideally a negative test + tooling verification
  (e.g. `codesign --display --entitlements - $APP | grep ...` to
  confirm an entitlement was removed; App Privacy Report on device to
  confirm tracking stopped; App Store Connect Privacy Manifest
  validation passes)

### No-Findings Case

If the synthesis contains zero findings after Phase 4:
- Create a single P0 task: "Verify no findings — [scope], [date]"
- The task description must document: scope, target platforms, tooling
  ran, 13 categories reviewed, date, reviewer agents
- Do not produce an empty sprint

### Write the Report

Create `$AUDIT_DIR/REPORT.md`:

```markdown
# Apple Platform Security Audit — [scope] ([YYYY-MM-DD])

## Overview

[1-2 paragraphs: audit scope, target platforms, tooling summary, total
findings by severity, top 3 issues. Remind the reader that Apple
static analysis tools are thinner than the web ecosystem — many
findings require runtime verification with built-app tooling
(codesign, Console.app, App Privacy Report, App Store Connect).]

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
| [Only non-zero categories shown] | N |

Target platforms: [iOS / iPadOS / macOS / etc.]
Capability surfaces: [summary from Phase 1]

Intermediate audit artifacts: `$AUDIT_DIR/tooling-raw/`, `$AUDIT_DIR/claude.md`, `$AUDIT_DIR/codex.md`, `$AUDIT_DIR/synthesis.md`, `$AUDIT_DIR/devils-advocate.md`

## Implementation Plan

### 🚨 Immediate Action (Critical)

[One task per Critical finding. For Apple apps this may mean pulling a
TestFlight build, hotfix, re-submit.]

**Task: [Finding ID] — [Category] — [Title]**
- Location: `path/to/file.swift:line`
- CWE / Apple: [identifier]
- Platform: [iOS / macOS / etc.]
- Verification: [code / runtime — with specific tool to run]
- Issue: [description]
- Remediation: [specific Apple API to add/change]
- **Operational note**: [credential rotation? push cert? App Store
  Connect API key? Build pull from TestFlight? user comms?]

### P0: Must Ship (High)

[High findings, same format]

### P1: Ship If Capacity Allows (Medium)

### Deferred (Low)

## Compound Findings

[Pairs/chains that escalate when combined.]

## Definition of Done

- [ ] All Critical (Immediate Action) tasks completed and verified
- [ ] All P0 tasks completed and verified
- [ ] Runtime-verification tasks tested with: built app +
      `codesign --display --entitlements - $APP`, Console.app for
      `os_log` qualifiers, App Privacy Report on device for tracking,
      App Store Connect Privacy Manifest validation
- [ ] No new Critical/High findings introduced by the remediations
- [ ] PrivacyInfo.xcprivacy validated for App Store submission if
      relevant findings were addressed
- [ ] Compound-finding paths confirmed closed

## Security Considerations

- **Sensitive content**: this report may contain exploit details and
  Apple-platform attack-path descriptions. Review before sharing.
- **App Store rejection risk**: Privacy Manifest, purpose strings,
  required-reason API findings can trigger App Store rejection — fix
  before submission, not after.
- **Runtime verification matters more here**: Apple static-analysis
  tooling is limited. Several findings (entitlements, code signing,
  logging qualifiers, ATS effective behavior) require building the
  app and inspecting it.

## Dependencies

- Raw tooling output: `$AUDIT_DIR/tooling-raw/`
- Audit intermediate files: `$AUDIT_DIR/claude.md`, `$AUDIT_DIR/codex.md`, `$AUDIT_DIR/synthesis.md`, `$AUDIT_DIR/devils-advocate.md`
- Emergency-exit document (if applicable): `$AUDIT_DIR/EMERGENCY.md`
```

### Register and Hand Off

Inform the user:

   > ✅ Apple platform security audit complete.
   >
   > **Report:** <literal absolute path to $AUDIT_DIR/REPORT.md>
   >
   > **Summary:** <Critical: X, High: Y, Medium: Z, Low: W>; top finding:
   > <one-line description>
   >
   > **⚠️ Sensitive content**: this report contains exploit details.
   > Review before sharing.
   >
   > **Next:** Run `/sprint-plan` against the report:
   >
   > ```
   > /sprint-plan <literal absolute path>
   > ```
   >
   > **Important:** Critical findings in the "Immediate Action" section
   > should not wait for the next release window — patch out-of-band,
   > pull from TestFlight if necessary, and re-submit.
   >
   > **App Store rejection risk**: any Privacy Manifest, purpose
   > strings, or required-reason API findings should be addressed
   > before submission.

If the emergency-exit triggered in Phase 1, the hand-off message
instead points the user at `$AUDIT_DIR/EMERGENCY.md`.

---

## Output Checklist

At the end of this workflow, verify:

- [ ] `$AUDIT_DIR/tooling-raw/` — populated with tool output and Apple
      artifact snapshots (entitlements, privacy manifest, purpose
      strings)
- [ ] `$AUDIT_DIR/claude.md` — finding schema with CWE/Apple +
      Category + Platform + Verification columns, ID prefix A
- [ ] `$AUDIT_DIR/codex.md` — same schema, ID prefix C
- [ ] Both files are non-empty (or single-agent warning added)
- [ ] `$AUDIT_DIR/synthesis.md` — unified findings with canonical
      S-prefix IDs, Compound Findings section
- [ ] `$AUDIT_DIR/devils-advocate.md` — Codex challenge complete
- [ ] Valid devil's advocate challenges incorporated
- [ ] Rejected challenges documented with reasoning
- [ ] `$AUDIT_DIR/REPORT.md` — Critical findings in **Immediate
      Action** section above P0
- [ ] Each task has Apple-specific runtime verification guidance
- [ ] No-findings case handled if applicable
- [ ] Sensitive-content + App Store rejection warnings in hand-off
- [ ] Emergency-exit handled if triggered

---

## Reference

- Report output: `~/Reports/<org>/<repo>/audits/<TS>-security-apple/`
- Audit artifacts: `$AUDIT_DIR/{tooling-raw/, claude,codex,synthesis,devils-advocate,REPORT}.md` plus optional `EMERGENCY.md`
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
