Perform a thorough Apple platform security review of the scope at the
project root you've been pointed at. Tooling has already been run; raw
output is in the audit dir's tooling-raw/ subdirectory. Read those files
first: gitleaks.json (secrets), semgrep.json (SAST),
xcodebuild-analyze.log (Xcode static analyzer),
entitlements-declared.txt (capability claims).

Apple SAST is thinner than the web ecosystem — most findings come from
manual code reading. Validate, do not duplicate, automated findings.

Write all findings to codex.md (in the audit dir you were granted write
access to) using this exact table format:

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
codesign requirement (XPC is primarily macOS; deeper XPC service
patterns belong in audit-apple-macos); App Groups data isolation;
UIPasteboard.general sensitive-data writes; document picker /
open-in input validation.

(5) Entitlements — review *.entitlements for least-privilege at the
cross-platform-runtime level (App Sandbox + Hardened Runtime
`com.apple.security.cs.*` entitlement depth is macOS-distinct — for
that detail send the finding to audit-apple-macos); flag obviously
dangerous Hardened Runtime exceptions inline (allow-jit,
allow-unsigned-executable-memory, disable-library-validation); flag
Network Extension and other capability-granting entitlements for
justification.

(6) CloudKit — public database used only for genuinely public data;
private DB with per-user ownership; CKShare participant ACLs; shared
zone permissions; CloudKit Web Services tokens never embedded.

(7) StoreKit — StoreKit 2 Transaction.currentEntitlements consumed
only via VerificationResult.verified (never .unverified); receipt
validation also server-side for non-consumable / subscription content;
Transaction.originalID + revocationDate tracked; restores
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
certs, App Store Connect API keys (the orient phase emergency-exits
on live credentials; here flag near-misses and dev/test stubs that
shouldn't ship).

Rate severity on evidence: impact, exploitability, blast radius,
reachability, compensating controls.

Critical anchors:
- Live credentials in source
- NSAllowsArbitraryLoads=true shipping
- StoreKit purchase without VerificationResult.verified
- WKWebView with JS + arbitrary URLs
- CloudKit public DB for private data
- disable-library-validation without need

High anchors:
- Weak Keychain accessibility (AccessibleAlways for sensitive data)
- Missing cert pinning on sensitive APIs
- os_log %{public} on PII
- URL scheme handler without validation on state-changing paths
- XPC service without audit-token/codesign requirement
- Over-broad entitlements

Every finding must include a Verification field — for Apple this often
means runtime verification with codesign / Console.app / Xcode static
analyzer. Note when verification requires a built app.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to codex.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
