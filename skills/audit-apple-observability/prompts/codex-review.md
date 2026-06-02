Perform a thorough Apple platform observability review of the scope at
the project root you've been pointed at. Tooling has already been run;
raw output is in the audit dir's tooling-raw/ subdirectory. Read those
files first:

- logger-call-sites.txt — Logger( / os_log / OSLog occurrences
- privacy-specifiers.txt — every `privacy:` argument and %{public} /
  %{private} marker. **Grepping this file for `.public` on anything
  that looks like a token / URL / email / userID / authHeader is the
  single highest-yield activity for this audit.**
- signpost-call-sites.txt — OSSignposter / os_signpost / interval +
  event APIs
- metrickit-call-sites.txt — MXMetricManager subscribers + diagnostic
  payload handlers
- print-nslog-call-sites.txt — print() / NSLog() / debugPrint() /
  dump() occurrences, with surrounding context for #if DEBUG checks
- oslog-preferences.txt — Info.plist OSLogPreferences definitions
  (per-subsystem default log levels)

Write all findings to codex.md (in the audit dir you were granted write
access to) using this exact table format:

| ID | Severity | Anchor | Category | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix C (e.g. C001, C002). Every finding MUST include
an Anchor (e.g. Apple:Logger, Apple:MetricKit, Apple:OSSignposter,
Apple:OSLogStore, File:Sources/Networking/Client.swift) and a Category
from: LoggerAdoption, PrivacySpecifiers, OSSignposter, MetricKit,
CrashHangDiagnostics, LogLevelDiscipline, Subsystems, LogRedaction,
SignpostInstrumentsIntegration, PerformanceMarkers,
PrintNSLogElimination, OSLogStore. Platform: iOS, iPadOS, macOS,
MacCatalyst, watchOS, tvOS, visionOS, or Multi.

DO NOT review runtime security broadly (Keychain, ATS, WKWebView, IPC)
— that belongs in audit-apple-security. PII-in-logs at the security
level is also covered there; this audit covers the broader
observability discipline (subsystem hygiene, signpost coverage,
MetricKit ingestion, log-level discipline) on top of that. DO NOT
review Privacy Manifest / ATT / sysdiagnose-export compliance — that
belongs in audit-apple-privacy.

Cover these 12 categories (skip if not applicable):

(1) LoggerAdoption — `Logger(subsystem:category:)` (iOS 14+) preferred
over the deprecated `os_log` C function. Subsystem follows reverse-DNS
(`com.org.app.networking`); category groups related logs. Project on
mixed APIs (some files using Logger, some still on os_log, some on
print) is a hygiene issue worth flagging.

(2) PrivacySpecifiers — `\(value, privacy: .public)` should appear
only on non-sensitive data; default `.auto` redacts non-numeric /
non-Bool values to `<private>` automatically. Flag any `%{public}` or
`\(_, privacy: .public)` on PII / credentials / access tokens /
refresh tokens / auth headers / device identifiers / location / user
emails. Prefer `.private(mask: .hash)` for stable correlation IDs
that need to be matched across log entries without leaking the value.

(3) OSSignposter — `OSSignposter` (iOS 15+ / macOS 12+) preferred
over the deprecated `os_signpost` C function. Signpost intervals
scoped via `withIntervalSignpost`. Signposts present in critical-path
code: app launch, scene activation, list scrolling, network requests,
expensive computation. Instruments will surface these in the
Points-of-Interest track.

(4) MetricKit — `MXMetricManager.shared.add(self)` subscriber
installed early in the launch sequence (typically `AppDelegate
application(_:didFinishLaunchingWithOptions:)` or a SwiftUI
`@main` init). `didReceive(_ payloads: [MXMetricPayload])` and
`didReceive(_ payloads: [MXDiagnosticPayload])` implementations route
payloads to analytics. PII redaction performed before any
transmission.

(5) CrashHangDiagnostics — `MXCrashDiagnostic` /
`MXHangDiagnostic` / `MXDiskWriteExceptionDiagnostic` /
`MXCPUExceptionDiagnostic` ingested via the same MetricKit subscriber.
`ApplicationExitInfo` handling on next launch (`MXMetaData` ABI for
prior-launch crash context).

(6) LogLevelDiscipline — Appropriate level per call site: `.debug`
(developer-only, not persisted), `.info` (default not persisted),
`.notice` (default persisted — used for normal-operation milestones),
`.error` (recoverable but unexpected), `.fault` (system-level
issues). Flag chatty `.info` / `.notice` in tight loops, and
`.fault` used as a generic error.

(7) Subsystems — Logical subsystem partition by module
(`com.org.app.networking`, `com.org.app.persistence`,
`com.org.app.ui`, etc.) enabling Console.app filtering. Not one giant
subsystem for the whole app. Subsystem string declared once as a
constant (e.g. `Bundle.main.bundleIdentifier!`) and reused, not
hardcoded per-file.

(8) LogRedaction — Custom `CustomStringConvertible` /
`CustomDebugStringConvertible` on PII-bearing model types so that
even an accidental `\(user)` interpolation produces a safe string
(e.g. `"User(id: 42)"` not `"User(email: 'jane@example.com')"`).

(9) SignpostInstrumentsIntegration — Custom Instruments package
(`.instrdst`) registered when the project ships its own; otherwise
signpost category names that align with built-in Instruments tracks.
Avoid signposts named identically to system tracks (causes overlay
confusion in Instruments).

(10) PerformanceMarkers — Specific high-value signposts: app launch
start / first-frame, scene activation, network request start/end with
`httpStatus` metadata, list scroll begin/end, expensive computation
markers. Absence of any signpost coverage at all on a 50k-LOC app is
itself a finding.

(11) PrintNSLogElimination — `print()` / `NSLog()` / `debugPrint()`
/ `dump()` removed from Release builds. Any usage outside `#if DEBUG`
is a finding. Note that even guarded `print` calls compile their
string-construction code into the binary in some optimization
configurations; the only fully-safe approach is to remove or convert
to `Logger`.

(12) OSLogStore — `OSLogStore` introspection for in-app log retrieval
(support / bug-report flow). When used, the predicate and time bounds
must be specific (don't pull all logs since process start). The
entitlement `com.apple.developer.os.log-store` is required on iOS.

Rate severity on evidence: impact (what leaks — token vs email vs
device ID), reachability (does the call site execute in Release?),
blast radius (Console.app over USB vs sysdiagnose vs TestFlight
diagnostics vs MetricKit-to-server), compensating controls (already
wrapped through redacting CustomStringConvertible, subsystem disabled
at `.error`+ via OSLogPreferences, server-side redaction).

Critical anchors:
- `%{public}` or `\(_, privacy: .public)` on tokens / credentials /
  Keychain values / Auth headers / passwords / refresh tokens /
  session cookies → leaks via Console.app to anyone with USB access
  to the device, plus every sysdiagnose ever taken, plus TestFlight
  diagnostics share, plus any third-party crash analytics that
  ingests OSLogStore.
- `print()` / `NSLog()` of PII / credentials in Release builds (not
  behind `#if DEBUG`) → compiled into binary, retrievable from device
  via `idevicesyslog` over USB, captured in every sysdiagnose.
- Wrong-privacy-default pattern: project blanket-wraps every
  interpolation `\(value, privacy: .public)` "to make Console useful
  in debug" → ships to Release; every value the app logs leaks.

High anchors:
- `Logger` / `os_log` of full URL with query params containing tokens
  or auth params (even with `.private`, the path itself can leak if
  it includes UUIDs that map to users).
- `MXMetricPayload` / `MXDiagnosticPayload` transmitted to a server
  without PII redaction (device locale + region + app state can
  fingerprint).
- Missing `MXMetricManager.shared.add(self)` subscriber entirely →
  every Apple-Diagnostics-API crash invisible to the dev team; App
  Store Connect shows ~14-day-delayed low-signal crash data only.
- Deprecated `os_log` C function used in code that should be on
  `Logger` (iOS 14+).
- Subsystem hardcoded as a string literal in every call site (refactor
  blocker — moving the subsystem name later touches every file).

Every finding must include a Verification field. For code findings:
re-grep the captured tooling-raw files after the fix. For runtime
findings: requires reproducing the scenario on a real device with
Console.app open, or capturing a sysdiagnose and grepping the bundle.
"Manual review" alone is not sufficient verification for a Critical
finding involving credentials.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to codex.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
