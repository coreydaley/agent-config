Perform a thorough Apple platform build & release review of the scope
at the project root you've been pointed at. Tooling has already been
run; raw output is in the audit dir's tooling-raw/ subdirectory. Read
those files first:

- build-settings-debug.txt and build-settings-release.txt — the resolved
  build settings per configuration. **Diffing these two files is the
  single highest-yield activity for this audit.**
- xcconfig-files.txt — every .xcconfig in the project
- entitlements-per-target.txt — every .entitlements file in the project
- info-plists.txt — every Info.plist in the project (when explicit
  rather than INFOPLIST_KEY_*-generated)
- package-resolved.txt — SPM Package.resolved content
- podfile-lock.txt — Podfile.lock content (if CocoaPods is in use)
- schemes.txt — the project's schemes
- export-options-plists.txt — any ExportOptions.plist (distribution config)

Write all findings to codex.md (in the audit dir you were granted write
access to) using this exact table format:

| ID | Severity | Anchor | Category | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix C (e.g. C001, C002). Every finding MUST include an
Anchor (e.g. BuildSetting:SWIFT_OPTIMIZATION_LEVEL, File:project.pbxproj,
Apple:DistributionGuide) and a Category from: ProjectStructure,
BuildSettings, DeploymentTarget, CodeSigning, Schemes, SPMDeps,
Cocoapods, Archive, AppIcon, InfoPlist, Resources, CI. Platform: iOS,
iPadOS, macOS, MacCatalyst, watchOS, tvOS, visionOS, or Multi.

DO NOT review runtime security (Keychain, ATS, WKWebView, IPC) — that
belongs in audit-apple-security. DO NOT review App Store Review
Guidelines compliance (metadata, screenshots, IAP rules) — that belongs
in audit-apple-app-store-review. DO NOT review Privacy Manifest /
ATT — that belongs in audit-apple-privacy. DO NOT review
macOS-distinctive Hardened Runtime / Notarization / Gatekeeper /
Sparkle appcast / Developer ID distribution depth — that belongs in
audit-apple-macos (this audit covers generic signing/archive/dSYM
hygiene that applies on all platforms). DO NOT review iOS-distinctive
Info.plist keys (UIBackgroundModes, UIApplicationSceneManifest,
UIRequiresFullScreen, UISupportedInterfaceOrientations) — those belong
in audit-apple-ios.

Cover these 12 categories (skip if not applicable):

(1) ProjectStructure — `.pbxproj` health: orphaned file references
that no longer exist on disk; broken paths (relative paths that don't
resolve); duplicate target memberships (the same source file compiled
into two targets unintentionally); unused targets; build phases that
produce files no one consumes; build phases that copy resources never
referenced from code; `Pods/`, `.build/`, `DerivedData/` checked into
git.

(2) BuildSettings — Debug vs Release divergence in SWIFT_OPTIMIZATION_LEVEL
(Debug -Onone, Release -O), GCC_OPTIMIZATION_LEVEL (Debug 0, Release s),
ONLY_ACTIVE_ARCH (Debug YES, Release NO), DEAD_CODE_STRIPPING (Release YES),
SWIFT_COMPILATION_MODE (Release wholemodule), ENABLE_TESTABILITY (Debug YES,
Release NO — CRITICAL if Release is YES), DEBUG_INFORMATION_FORMAT
(Release dwarf-with-dsym), GCC_PREPROCESSOR_DEFINITIONS (DEBUG=1 should
not be in Release). Inline settings in .pbxproj that should be in
.xcconfig. Inherited-without-override mistakes where a target overrides
$(inherited) and discards xcconfig values.

(3) DeploymentTarget — IPHONEOS_DEPLOYMENT_TARGET / MACOSX_DEPLOYMENT_TARGET
/ WATCHOS_DEPLOYMENT_TARGET / XROS_DEPLOYMENT_TARGET / TVOS_DEPLOYMENT_TARGET
consistency between app target, extensions, embedded frameworks, and SPM
dep `platforms:` array. Targets older than the App Store minimum (rejects
on upload). Targets newer than necessary (cuts users for no reason).
Extension targets out of sync with the app (extensions can't have a
lower minimum than the app).

(4) CodeSigning — All platforms. CODE_SIGN_STYLE (Automatic vs
Manual) per configuration; DEVELOPMENT_TEAM populated;
PROVISIONING_PROFILE_SPECIFIER matching the bundle id;
CODE_SIGN_IDENTITY per configuration (Apple Development for Debug,
Apple Distribution for Release). Entitlements file referenced for
Debug but not Release (capability silently dropped). Mixed
automatic/manual across configurations (rare-but-confusing). Team ID
hardcoded into multiple targets vs inherited from xcconfig. For
macOS-distinctive Hardened Runtime `com.apple.security.cs.*`
entitlement depth and Notarization stapling, defer to audit-apple-macos.

(5) Schemes — Only shared schemes (xcshareddata/xcschemes/) commit to
git; user-only schemes (xcuserdata) won't reproduce on a colleague's
machine or in CI. Test plan attached (`.xctestplan`) for parallel
testing and code coverage configuration. Run > Arguments containing
secrets, debug flags (-com.apple.CoreData.SQLDebug 1), or memory-debug
malloc flags shipping in Release. Environment variables that should be
secrets but are committed.

(6) SPMDeps — Package.resolved committed (commit it). Version pinning
quality: .exact() is rigid but reproducible; .upToNextMajor() is the
default-safe choice; .branch() / .revision() flagged as a release-day
risk (a force-push or a branch advance silently changes the build).
Package.resolved location: Xcode 13+ stores per-workspace at
`*.xcworkspace/xcshareddata/swiftpm/Package.resolved`; a Package-level
file at the project root can be stale. Transitive bloat: a heavy dep
pulled in for trivial use (e.g. Alamofire for one POST).

(7) Cocoapods (when used) — Podfile.lock committed. Pods/ directory
either committed (acceptable) or properly .gitignore'd; mixed state
("partial Pods/ in git") is bad. `pod 'X', :git => 'https://github.com/...'`
flagged as a release-day risk (force-push). `use_frameworks!` vs
`use_modular_headers!` discipline (mixing can break dynamic-framework
deps). Same dep through both Pods and SPM (double-include).

(8) Archive — DEBUG_INFORMATION_FORMAT=dwarf-with-dsym for Release
(otherwise no symbolicated crash logs); ENABLE_BITCODE=NO (Apple
removed Bitcode entirely; YES is a stale setting); SKIP_INSTALL=NO on
the app target and YES on every embedded framework / extension target
(violation causes invalid archives); STRIP_INSTALLED_PRODUCT=YES for
Release; COPY_PHASE_STRIP=NO for Release (set to YES only when
intentional — it strips embedded resources, can break some debug data);
dSYM upload destination configured to App Store Connect /
Sentry/Bugsnag/Datadog via a Run Script Build Phase or CI step.

(9) AppIcon — All icon slots populated in *.xcassets/AppIcon.appiconset
per platform; the required slots differ per platform. iOS / iPadOS:
marketing 1024×1024 is mandatory and uploads without it get rejected;
all in-app sizes (20×20 through 167×167) populated; alternate app
icons (if used) declared in Info.plist CFBundleAlternateIcons. macOS:
AppIcon.icns with all variants (16 through 1024). watchOS: watch face
icons per Apple Watch sizes. tvOS: layered App Icon. visionOS:
specific App Icon slots. ACCENT_COLOR_NAME set if the app uses a
tinted accent color in its asset catalog.

(10) InfoPlist — CFBundleShortVersionString and CFBundleVersion (build
number) discipline — applies to all Apple platforms. Common patterns:
a single Info.plist with these keys as $(MARKETING_VERSION) /
$(CURRENT_PROJECT_VERSION) and the project's MARKETING_VERSION /
CURRENT_PROJECT_VERSION setting cascading to all targets; hardcoded
versions in multiple targets cause cross-target skew at upload time.
LSMinimumSystemVersion (macOS) consistency. INFOPLIST_KEY_* (Xcode 15+
generated Info.plist keys) vs explicit Info.plist file — flag mixed
usage that causes drift between the two sources of truth. iOS-distinctive
keys (UIBackgroundModes, UIApplicationSceneManifest,
UIRequiresFullScreen, UISupportedInterfaceOrientations) belong in
audit-apple-ios — don't audit their semantics here.

(11) Resources — Localizable.strings or String Catalog (.xcstrings)
present per declared locale (CFBundleLocalizations / known_regions in
project). Resource bundle creation in SPM packages
(`.process("Resources")` vs `.copy()`). On-demand resources tagged
correctly via NSBundleResourceRequest. Asset catalog reference rot
(image set removed but a code reference Image("Foo") still exists,
caught only at runtime by Image picking a generic placeholder).

(12) CI — `xcodebuild` invocation flags: -skipPackagePluginValidation
(opts out of macOS 14+ plugin validation prompt; only safe if you trust
your dep tree); -disableAutomaticPackageResolution (set when caching
Package.resolved is reproducible); -resultBundlePath path/to/results
(critical for diagnosing CI failures — without it failure output is
lost); xcbeautify / xcpretty in front of xcodebuild output (untransformed
xcodebuild output is hard to read). Signing in CI: fastlane match,
manual import of .p12 + provisioning profile, or GitHub Actions
apple-actions/import-codesigning-certs. DerivedData reuse strategy
(persistent vs ephemeral; influences cache hit rate vs reproducibility).

Rate severity on evidence: impact (what ships broken), reachability
(does Release/AppStore see it), blast radius (every user vs CI-only vs
TestFlight-only), compensating controls (does the CI script override
the in-Xcode value).

Critical anchors:
- Release configuration ships with SWIFT_OPTIMIZATION_LEVEL=-Onone or
  ENABLE_TESTABILITY=YES (debug-flavored release ship)
- DEBUG_INFORMATION_FORMAT != dwarf-with-dsym for Release (crash logs
  unreadable forever)
- App Icon missing the 1024×1024 marketing slot (App Store upload
  rejects)
- Deployment target older than the current App Store minimum (upload
  rejects)
- Capability present in Debug.entitlements but missing from
  Release.entitlements (feature silently broken on TestFlight)

High anchors:
- CODE_SIGN_STYLE=Automatic for Release on a CI-built app (signing
  fragility — first cert expiration kills every CI build)
- SPM dep pinned to .branch("main") for a Release build
- DEBUG=1 preprocessor flag in Release configuration
- Package.resolved not committed
- Pods/ committed with stale Podfile.lock
- CFBundleVersion duplicated across builds (can't re-upload same number)
- No dSYM upload destination configured for Release

Every finding must include a Verification field — for build-release
this is usually a *clean archive* (`xcodebuild archive -workspace ...
-scheme ... -configuration Release`), a `codesign --display
--entitlements -` against the built `.app`, or `dwarfdump --uuid`
against the produced dSYM. "Manual review" alone is not sufficient
verification for a Critical finding.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to codex.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
