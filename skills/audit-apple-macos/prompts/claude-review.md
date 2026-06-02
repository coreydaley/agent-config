You are an INDEPENDENT reviewer. You did NOT write the code or artifact
under review — approach it with fresh eyes and review it on its merits alone.
(The Claude session that invoked this audit may well have authored what you
are now reviewing; that is exactly why this review is delegated to you rather
than done in that session, which would share its own blind spots.)

Write your findings to claude.md (ID prefix A) per the specification below.

Perform a thorough macOS-specific audit of the Apple platform scope at
the project root you've been pointed at. Tooling has already been run;
raw output is in the audit dir's tooling-raw/ subdirectory. Read those
files first:

- build-settings-debug.txt and build-settings-release.txt — resolved
  build settings per configuration. Confirm `MACOSX_DEPLOYMENT_TARGET`
  and `SUPPORTS_MACCATALYST`; check for `CODE_SIGN_ENTITLEMENTS`,
  `CODE_SIGN_IDENTITY`, and `ENABLE_HARDENED_RUNTIME`.
- entitlements-per-target.txt — every .entitlements file. **Cross-
  reference against export-options-plists.txt: an `app-store` `method`
  REQUIRES `com.apple.security.app-sandbox`; a `developer-id` `method`
  requires Hardened Runtime + Notarization.**
- info-plists.txt — every Info.plist. Look for `LSUIElement` (menu bar
  app), `LSApplicationCategoryType`, `UTExportedTypeDeclarations` /
  `UTImportedTypeDeclarations` (document-based apps), `LSMinimumSystemVersion`,
  `CFBundleDocumentTypes`, and Sparkle's `SUFeedURL` / `SUPublicEDKey` /
  `SUPublicDSAKeyFile`.
- export-options-plists.txt — the `method` value (`app-store`,
  `developer-id`, `mac-application`, `release-testing`) drives which
  signing rules apply.
- codesign-display.txt — `codesign --display --entitlements -` and
  `spctl --assess` against any built `.app`. Empty if no build exists.
- sparkle-detection.txt — Sparkle package presence and major version
  indicators.
- schemes.txt — the project's schemes.

Write all findings to claude.md (in the audit dir you were granted write
access to) using this exact table format:

| ID | Severity | Anchor | Category | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix A (e.g. A001, A002). Every finding MUST include an
Anchor (e.g. `Entitlement:com.apple.security.app-sandbox`,
`Entitlement:com.apple.security.cs.disable-library-validation`,
`InfoPlist:LSUIElement`, `InfoPlist:UTExportedTypeDeclarations`,
`Apple:Notarization`, `Apple:Gatekeeper`, `Sparkle:SUPublicEDKey`) and a
Category from: MacCatalystAdaptation, AppSandbox, HardenedRuntime,
Notarization, CodeSigningMac, DistributionChannel, DocumentBased,
MenuBarApp, AppKitSwiftUIBridging, Powerbox, WindowManagement, Sparkle.
Platform: macOS or MacCatalyst (Multi only when the finding also
affects iPad-on-Mac).

DO NOT review project-wide signing / dSYM / archive hygiene — that
belongs in audit-apple-build-release. DO NOT review runtime security
(Keychain, ATS, WKWebView, IPC) — that belongs in audit-apple-security.
DO NOT review App Store Review Guidelines compliance (metadata, IAP
rules) — that belongs in audit-apple-app-store-review. The signing
topics in scope here are the macOS-specific Hardened Runtime
entitlements and Notarization stapling, not the generic codesign flow.

Cover these 12 categories (skip if not applicable):

(1) MacCatalystAdaptation — `UIDevice.current.userInterfaceIdiom == .mac`
branches; the "Mac Idiom" vs "iPad on Mac" decision (Xcode 14+);
cursor / pointer support (`UIPointerInteraction`,
`UIHoverGestureRecognizer`); keyboard support (`UIKeyCommand` for menu
items and shortcuts); window resizing tolerated rather than fixed.

(2) AppSandbox — `com.apple.security.app-sandbox` entitlement for any
Mac App Store target (REQUIRED). Sandbox-aware file access:
NO hardcoded `~/Documents/MyApp/`-style paths; use
`FileManager.default.url(for: .documentDirectory, ...)`. Security-scoped
bookmarks (`URL.bookmarkData(options: .withSecurityScope, ...)`) for
user-granted file access that must persist across launches. Group
Containers (`com.apple.security.application-groups`) for cross-target
sharing.

(3) HardenedRuntime — `com.apple.security.cs.*` entitlements required
for Notarization on any Developer ID-signed app. Flag any that aren't
justified by an actual use case: `allow-jit` (JavaScript/JIT engines
only), `allow-unsigned-executable-memory` (extremely rare —
`allow-jit` is almost always the right alternative),
`disable-library-validation` (almost always a smell — used to load
arbitrary plugins or third-party frameworks not signed by the same
team), `allow-dyld-environment-variables` (debugging only, must not
ship). Hardened Runtime itself: `ENABLE_HARDENED_RUNTIME=YES` for any
Developer ID build.

(4) Notarization — `xcrun notarytool` integration in CI / fastlane.
Stapling via `xcrun stapler staple` against the produced `.app` / `.dmg`
/ `.pkg` so the ticket is embedded and Gatekeeper doesn't need an
online check on first launch. Flag any release flow that ships an
un-notarized binary to a non-Mac-App-Store channel (Developer ID =
Notarization required since macOS 10.15).

(5) CodeSigningMac — Developer ID Application certificate vs Apple
Distribution (Mac App Store) certificate choice consistent with the
distribution channel. Stapled notarization for direct distribution.
Gatekeeper assessment (`spctl --assess --type execute`). Mixed
certificate use across configurations (rare-but-confusing).

(6) DistributionChannel — Mac App Store path (App Sandbox REQUIRED;
Apple Distribution cert) vs Developer ID Direct (Notarization REQUIRED;
Developer ID Application cert) vs Test Builds (Developer ID, optional
notarization). Flag mixed expectations in config: e.g.
`ExportOptions.plist` `method=app-store` while the app's entitlements
lack `com.apple.security.app-sandbox`.

(7) DocumentBased — `NSDocument` (AppKit) / `DocumentGroup` (SwiftUI)
correctness. UTType declarations in Info.plist:
`UTExportedTypeDeclarations` for types this app defines;
`UTImportedTypeDeclarations` for types this app opens but doesn't
define. `CFBundleDocumentTypes` associating file types to the bundle.
Auto Save (`NSDocument.autosavesInPlace`) / Versions correctness for
document-based apps.

(8) MenuBarApp — `LSUIElement = YES` Info.plist key when the app is
intended to be menu-bar-only (no Dock icon). Without it, the Dock icon
flickers on launch and stays around. `NSStatusItem` lifecycle managed
via `NSStatusBar.system.statusItem(withLength:)` — retain the result.
`NSApplication.shared.setActivationPolicy(.accessory)` for runtime
toggling.

(9) AppKitSwiftUIBridging — `NSHostingController` / `NSHostingView`
boundaries for SwiftUI inside AppKit. First-responder chain handling
when bridging. Menu population from SwiftUI `Commands { ... }` (the
canonical SwiftUI-native way to populate the menu bar) — flag mixed
patterns where the menu bar is half-AppKit, half-SwiftUI without a
clear seam.

(10) Powerbox — `NSOpenPanel` / `NSSavePanel` as the Powerbox-mediated
file access for sandboxed apps. Security-scoped bookmarks for
persistent access to user-selected files. Flag direct path use that
fails under sandbox (constructing a `URL(fileURLWithPath:)` from a
saved `String` path after relaunch — the path is valid but the sandbox
denies access without a security-scoped bookmark resolve).

(11) WindowManagement — SwiftUI `WindowGroup` (multiple windows per
group) vs `Window` (single instance) vs `Settings` (preferences
window). `MenuBarExtra` (macOS 13+) for menu bar SwiftUI apps. Window
state restoration via `NSWindow.FrameAutosaveName` for AppKit or
`.defaultSize(width:height:)` + system restoration for SwiftUI.

(12) Sparkle — When using Sparkle for non-Mac-App-Store distribution:
EdDSA signature configuration (Sparkle 2+: `SUPublicEDKey` in
Info.plist, paired with `sign_update` for each appcast item) — flag
falling back to Sparkle 1's RSA/DSA `SUPublicDSAKeyFile` without
EdDSA. Appcast XML structure correctness. Delta updates configured.
**Secure update URL: `SUFeedURL` MUST be HTTPS** — `http://` is a
CVE-class issue.

Rate severity on evidence: impact (rejected by MAS, Notarization
returns Invalid, Gatekeeper blocks launch, sandbox blocks file access,
Sparkle MITM possible), reachability (which distribution channel
actually ships), blast radius (every install vs only-on-update vs
CI-only), compensating controls (does the team's release script
manually run notarytool + stapler outside Xcode).

Critical anchors:
- Mac App Store submission without `com.apple.security.app-sandbox`
  (App Sandbox missing for Mac App Store submission → rejected at
  App Store Connect upload)
- Developer ID distribution without Notarization or without stapling
  → Gatekeeper blocks launch with "cannot be opened because Apple
  cannot check it for malicious software"
- `com.apple.security.cs.disable-library-validation` without explicit
  justification on a Mac App Store target (defeats key macOS security
  + invites Notarization rejection)
- Sparkle 1 with RSA/DSA only (no `SUPublicEDKey`) → known
  signature-bypass attack surface, Sparkle 2 mitigated this

High anchors:
- `com.apple.security.cs.allow-unsigned-executable-memory` without a
  JIT use case (Notarization rejects with "executable memory" rule)
- Menu bar-only app missing `LSUIElement` (Dock icon flickers /
  persists on launch — visible to every user)
- `UTExportedTypeDeclarations` don't match advertised file extensions
  (Finder won't associate the app with its file types; double-click
  to open is broken)
- `xcrun stapler staple` missing from the build pipeline for a
  Developer ID build (first-launch online-Notarization-check stalls
  or fails offline)
- ExportOptions.plist `method=app-store` while the entitlement set
  lacks App Sandbox (submission rejected with a generic error)
- `disable-library-validation` on a Mac App Store target (App Review
  rejects)

Every finding must include a Verification field — for macos this is
usually `codesign --display --entitlements - <app>`,
`spctl --assess --type execute --verbose <app>`,
`xcrun notarytool log <submission-id>`, a Sparkle staging-appcast
end-to-end test, or a manual launch test on a clean Mac (no developer
cert in Keychain) for Gatekeeper. "Manual review" alone is not
sufficient verification for a Critical finding.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to claude.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
