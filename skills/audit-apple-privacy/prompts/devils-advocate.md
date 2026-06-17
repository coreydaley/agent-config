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
- Evidence: file:line citation, parent-manifest reference, or specific code reference
- Confidence: high | medium | low

Cover these challenge categories:

(1) False positives — privacy findings that don't actually apply in context.
Specifically for Apple privacy:
- A Privacy Manifest entry the reviewer flagged as missing is actually
  declared in a parent / aggregated manifest the build system merges.
- Required-reason API access in a context that doesn't trigger Apple's
  declaration requirement (e.g. a system framework accesses UserDefaults
  internally; only direct app access requires declaration).
- ATT findings on an app that doesn't actually access IDFA (the
  ASIdentifierManager import is dead code or behind a #if DEBUG).
- A "missing purpose string" for a permission the app code never actually
  requests (only references the API type but doesn't invoke).
- A "tracking domain" call to a domain that's first-party despite the
  domain name resembling a known tracker.
- A flagged third-party SDK that's actually wrapped behind a runtime flag
  and never linked in App Store builds.

(2) Severity miscalibrations — Submission Impact rated higher than
warranted (App Review enforcement varies in practice — some "Blockers"
are practically warnings on first submission; some "Risks" reliably
reject) or lower than warranted for an imminent submission. Specifically:
- A "Blocker" that's actually only flagged in App Store Connect's
  pre-submission validation, not enforced by the human reviewer.
- A "Risk" that's deterministic rejection on macOS Catalyst but not iOS.
- A finding rated Medium that's actually a Submission Blocker because
  the data type is on Apple's "sensitive data" list.

(3) Missing findings — Apple-privacy issues the review missed:
- Data collection happening BEFORE ATT consent (SDK initialized in
  application(_:didFinishLaunchingWithOptions:); ATT prompted later).
- Fingerprinting via device characteristics not declared as tracking
  (boot time + disk space + active keyboards + locale fan-in).
- Shared web views (WKWebView, SFSafariViewController) with third-party
  cookies undeclared.
- Analytics SDK initialized before consent gate.
- PII leakage in crash reports or os_log %{public} output exfiltrated by
  third-party crash SDK.
- Clipboard data access (UIPasteboard) used without user action and
  without privacy-pasteboard declaration.
- On-device ML model training on user data without disclosure.
- Live Activity / Dynamic Island showing PII publicly on the lock screen.
- App Intents and Spotlight indexing exposing private data system-wide.
- Push notification payloads containing PII visible on lock screen.
- Background refresh / silent push tracking without disclosure.
- Local Network usage without NSLocalNetworkUsageDescription on iOS 14+.

(4) Missing compound paths — separate findings in the synthesis that
combine into a worse exploit than any single finding represents. Be
explicit about the chain and the combined severity.

Privacy compound chains:
- SDK initialized at launch + ATT prompt later = tracking-before-consent
- Manifest declares N data types + new SDK collects N+1 = declaration
  diverges in production; App Privacy Report catches it
- Vague purpose string + PII in analytics event names = covert
  collection beyond declared intent
- Required-reason API used by app for fingerprinting + no
  NSPrivacyTrackingDomains declaration = undeclared tracking via
  fingerprint fan-in

(5) Impractical/incomplete/wrong remediations — e.g. adding a Privacy
Manifest entry when the underlying behavior should change instead;
adding a purpose string but not gating the API call on the permission
result; declaring a tracking domain when the domain shouldn't be called
at all; pinning an SDK version that ostensibly has a manifest but the
build still bundles the older copy from a different dep tree.

(6) Verification steps that don't actually prove the fix works —
Apple-privacy verification often requires BOTH App Store Connect's
Privacy Manifest validation (post-TestFlight upload) AND on-device App
Privacy Report. "Manual review of Info.plist" is insufficient for
runtime data-flow findings. Negative-test verification (run the app, do
the user journey, confirm App Privacy Report shows no undeclared
access) is preferred for runtime concerns.

Be specific. Every challenge must cite the finding ID and reference the
Concern column.

Do not read or reference any other review file beyond synthesis.md and
the tooling-raw/ directory.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type "no_challenges"
  and Confidence "high" stating that you attempted but found nothing
  worth surfacing.
- No emojis.
