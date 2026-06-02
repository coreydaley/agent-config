You are an INDEPENDENT reviewer. You did NOT write the code or artifact
under review — approach it with fresh eyes and review it on its merits alone.
(The Claude session that invoked this audit may well have authored what you
are now reviewing; that is exactly why this review is delegated to you rather
than done in that session, which would share its own blind spots.)

Write your findings to claude.md (ID prefix A) per the specification below.

Perform a thorough Apple iOS / iPadOS-distinctive review of the scope
at the project root you've been pointed at. Tooling has already been
run; raw output is in the audit dir's tooling-raw/ subdirectory. Read
those files first:

- ios-deployment.txt — IPHONEOS_DEPLOYMENT_TARGET, TARGETED_DEVICE_FAMILY,
  SUPPORTED_PLATFORMS. **The deployment target gates which iOS features
  are even available** (Lock Screen widgets iOS 16+, Dynamic Island iOS
  16.1+, StandBy iOS 17+, Action Button iOS 17+ on iPhone 15 Pro+).
- ios-info-plists.txt — iOS-relevant Info.plist keys. **The single
  highest-yield artifact for this audit.** Look for
  UIRequiresFullScreen (highest-risk key), UIApplicationSceneManifest,
  UISupportedInterfaceOrientations, UIBackgroundModes,
  BGTaskSchedulerPermittedIdentifiers, UILaunchScreen vs
  UILaunchStoryboardName, UIViewControllerBasedStatusBarAppearance,
  NSSupportsLiveActivities.
- scene-lifecycle.txt — UIWindowSceneDelegate / UISceneSession adoption
  vs AppDelegate-only legacy.
- bg-task-scheduler.txt — BGTaskScheduler.register calls and identifier
  alignment with BGTaskSchedulerPermittedIdentifiers.
- ui-background-modes.txt — UIBackgroundModes flag usage and silent-push
  handler.
- ipad-input.txt — UIPointerInteraction, UIKeyCommand, PKCanvasView,
  Scribble.
- hardware-buttons.txt — AppShortcut / AppShortcutsProvider (Action
  Button surface), AVCaptureControl (Camera Control iPhone 16).
- live-activity.txt — ActivityKit, Live Activity, Dynamic Island
  presentation regions, Lock Screen widget families.
- live-text.txt — ImageAnalysisInteraction, VNRecognizeTextRequest.
- focus.txt — FocusFilterIntent, notification-filtering entitlement.

Write all findings to claude.md (in the audit dir you were granted write
access to) using this exact table format:

| ID | Severity | Anchor | Category | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix A (e.g. A001, A002). Every finding MUST include an
Anchor (e.g. Plist:UIRequiresFullScreen, Apple:UIWindowSceneDelegate,
Apple:BGTaskScheduler, Apple:DynamicIsland, Apple:UIPointerInteraction,
Apple:AppShortcut, Apple:FocusFilterIntent,
Apple:ImageAnalysisInteraction) and a Category from: SceneLifecycle,
BGTaskScheduler, UIBackgroundModes, SilentPushiOS, LockScreenWidgets,
DynamicIsland, iPadCursorPencil, HardwareButtons, FocusModes,
LiveTextVisualLookUp, iOSInfoPlistSurface, SafeAreaHomeIndicator.
Platform: iOS, iPadOS, or Multi (when a finding spans both). macOS /
watchOS / visionOS findings do NOT belong in this audit.

DO NOT review macOS-distinctive concerns (App Sandbox, Hardened
Runtime, Notarization, AppKit/SwiftUI bridging, Sparkle, document-based
apps, menu bar apps) — that belongs in audit-apple-macos. DO NOT review
watchOS-distinctive concerns (WCSession, HKLiveWorkoutBuilder, WidgetKit
complications, always-on display, ~24MB budget) — that belongs in
audit-apple-watchos. DO NOT review visionOS-distinctive concerns
(ImmersiveSpace, RealityKit, hand-tracking, gaze + pinch) — that
belongs in audit-apple-visionos. DO NOT review the extension-target
plumbing behind Widgets / Live Activities / App Intents (NSExtension
Info.plist, memory budgets, getTimeline contract) — that belongs in
audit-apple-extensions; THIS audit covers the iOS UX layer ABOVE the
extension target (Dynamic Island state design, Lock Screen widget
tinting, Action Button assignment via AppShortcutsProvider). DO NOT
review iPad multitasking *layout adaptation* (size classes,
ViewThatFits, Stage Manager-responsive layout) — that belongs in
audit-apple-adaptivity; THIS audit covers the foundational iOS-only
settings (UIRequiresFullScreen, UIApplicationSceneManifest) that
determine whether multitasking is possible at all. DO NOT review APNs
end-to-end (entitlement, certificate, payload, authorization) — that
belongs in audit-apple-notifications; THIS audit covers the iOS-only
silent-push *lifecycle* (content-available + didReceiveRemoteNotification
+ UIBackgroundFetchResult).

Cover these 12 categories (skip if not applicable):

(1) SceneLifecycle — UIWindowSceneDelegate adoption (required for
multi-scene on iPad on iOS 13+), UISceneSession discipline,
UISceneConfiguration in
`application(_:configurationForConnecting:options:)`, scene-aware deep
links via `scene(_:continue:)` and `scene(_:openURLContexts:)`, state
restoration via `stateRestorationActivity(for:)`. Flag projects still
on AppDelegate-only lifecycle on iOS 13+ codebases. Flag deep-link
handling in `application(_:open:)` only when a SceneDelegate exists —
the AppDelegate handler doesn't fire when scenes are connected.

(2) BGTaskScheduler — BGAppRefreshTask + BGProcessingTask registration
via `BGTaskScheduler.shared.register(forTaskWithIdentifier:using:launchHandler:)`
from `applicationDidFinishLaunching` (or `init` of the
@UIApplicationDelegateAdaptor) — **registering later silently fails**
because the system has already decided which identifiers are
launchable. `BGTaskSchedulerPermittedIdentifiers` array in Info.plist
must contain every identifier used at register-time. `expirationHandler`
must synchronously cancel ongoing work — async cancellation is too
late and the OS kills the process. `earliestBeginDate` is advisory;
`requiresExternalPower` and `requiresNetworkConnectivity` for
processing tasks only.

(3) UIBackgroundModes — Info.plist `UIBackgroundModes` array entries
(audio, location, voip, fetch, remote-notification,
background-processing, external-accessory, bluetooth-central,
bluetooth-peripheral, nearby-interaction). Only declare flags actually
used — App Review flags unused declarations. `voip` is deprecated for
new apps (use PushKit + CallKit). `fetch` is largely obsoleted by
BGAppRefreshTask. `remote-notification` is required for silent push.

(4) SilentPushiOS — `content-available: 1` payload handling, server
must set `apns-push-type: background` and `apns-priority: 5` (Apple
throttles violators), `application(_:didReceiveRemoteNotification:fetchCompletionHandler:)`
has a 30-second budget, completion handler MUST be called exactly
once with `UIBackgroundFetchResult.newData` / `.noData` / `.failed`.
Returning `.noData` repeatedly causes APNs to throttle future silent
pushes for this app. iOS 13+ uses scene delegate
`scene(_:didReceive:)` for the user-tap path but the silent-push
handler stays on the AppDelegate.

(5) LockScreenWidgets — WidgetKit accessory families on iOS 16+:
`accessoryCircular`, `accessoryRectangular`, `accessoryInline`.
StandBy mode (iOS 17+) renders widgets full-screen on a charging
device — design widgets to look good at large scale. Live Activity
Lock Screen presentation distinct from Dynamic Island.
`.contentMarginsDisabled()` for full-bleed when intended.
`.privacySensitive()` modifier for fields that should redact on a
locked or AOD device.

(6) DynamicIsland — Live Activity dynamic-island presentation regions:
`compactLeading`, `compactTrailing`, `minimal`, `expanded`. Available
on iPhone 14 Pro / 15 Pro / 16 Pro+. Flag activities whose minimal
state lacks brand recognizability, compact state can't fit variable
content (delivery ETA, song title, score), expanded state truncates
under variable-length data, or `ContentState` not designed for AOD
luminance-reduced rendering. Live Activity push-token lifecycle
(`Activity.pushTokenUpdates`) for server-driven updates.

(7) iPadCursorPencil — `UIPointerInteraction` on tappable elements
(SwiftUI `.hoverEffect` or UIKit `UIPointerInteractionDelegate`),
`UIHoverGestureRecognizer` for hover affordances, `UIKeyCommand` /
SwiftUI `.keyboardShortcut` for keyboard shortcuts (iPad with Magic
Keyboard). Apple Pencil `PKCanvasView` / `PKToolPicker` /
`PKDrawing` for drawing / annotation / signature apps. Scribble
via `UIIndirectScribbleInteraction` for text-field handwriting
input. Flag iPad-supporting apps with significant tap surface
that have no pointer interactions.

(8) HardwareButtons — Action Button (iPhone 15 Pro+, iOS 17+) is
assigned via Settings → Action Button → Shortcut → <app>, so the
app must declare `AppShortcut` conformances inside an
`AppShortcutsProvider` to be assignable. Camera Control (iPhone 16,
iOS 18+) via `AVCaptureControl` (`AVCaptureSlider`,
`AVCaptureIndexPicker`) for camera-aware apps — flag camera apps
that don't surface their controls there.

(9) FocusModes — `FocusFilterIntent` conformance + `INFocusStatusCenter`
read access for app-Focus integration (the app changes content based
on the active Focus). `com.apple.developer.usernotifications.filtering`
entitlement for "Filter Notifications by Focus" (the app's
NotificationServiceExtension filters payloads against the user's
active Focus). Notification-heavy apps without Focus support are a
friction point; users either over-suppress (mute the app entirely)
or over-allow.

(10) LiveTextVisualLookUp — `ImageAnalysisInteraction` (iOS 16+) on
`UIImageView` or SwiftUI `Image` for in-place Live Text selection,
Visual Look Up, and Subject Lift. `VNRecognizeTextRequest` /
`VNDocumentCameraViewController` for programmatic OCR / document
scanning. Flag image-heavy apps (notes, receipts, whiteboard, document
scanner, screenshot review) that display images without Live Text
affordance.

(11) iOSInfoPlistSurface — `UIApplicationSceneManifest` required for
multi-scene (`UIApplicationSupportsMultipleScenes=YES` for iPad
multi-window). `UISupportedInterfaceOrientations` not over-restricted
— portrait-only on iPad is suspicious outside games and is flagged by
App Review. **`UIRequiresFullScreen=YES` is the highest-risk key**:
on non-game productivity / utility apps it breaks iPad multitasking +
Stage Manager, and App Review flags it on newer iPad reviews.
`UILaunchScreen` (SwiftUI dictionary form, iOS 14+) vs
`UILaunchStoryboardName` (storyboard form, legacy). Mixing both causes
drift. `UIViewControllerBasedStatusBarAppearance` discipline (true =
per-VC status bar control via `preferredStatusBarStyle`).
`UISupportsDocumentBrowser` for document-based apps.

(12) SafeAreaHomeIndicator — `preferredScreenEdgesDeferringSystemGestures`
only on genuine full-immersion content (rare and easy to misuse — abused
it triggers user friction trying to swipe home). `hidesBottomBarWhenPushed`
discipline (set on push transitions to navigate into a full-bleed
detail). SwiftUI `.ignoresSafeArea()` / `UIHostingController.safeAreaRegions`
discipline — flag uses that push content under the status bar or home
indicator without intentional design. `prefersHomeIndicatorAutoHidden`
for full-screen video / games.

Rate severity on evidence: impact (what ships broken on iOS),
reachability (which config / device sees it), blast radius (every iOS
user vs every iPad user vs every iPhone 14 Pro+ user), compensating
controls (a custom SceneDelegate that actually handles the AppDelegate
gap; an intentional fullscreen-game justification for
UIRequiresFullScreen=YES).

Critical anchors:
- Plist:UIRequiresFullScreen=YES on a non-game productivity / utility
  app (App Review flag + Stage Manager users locked out + iPad
  multitasking broken — direct revenue impact)
- Apple:BGTaskScheduler.register called after
  applicationDidFinishLaunching returns (tasks silently never run; the
  most common BGTask failure mode)
- Apple:DynamicIsland Live Activity compact state crashes on a real
  iPhone 14 Pro+ user (1-in-N crash on a passively-rendered surface)
- Plist:BGTaskSchedulerPermittedIdentifiers missing for an identifier
  the source registers (registration silently fails)

High anchors:
- Apple:UIWindowSceneDelegate missing on an iOS 13+ codebase
  (AppDelegate-only lifecycle; loses multi-scene + scene-aware deep
  links + iPad state restoration)
- Plist:UIBackgroundModes contains a flag with no callsite (App Review
  rejects on unused declarations)
- Apple:LockScreenWidgets only systemSmall/Medium/Large declared on
  iOS 16+ (Lock Screen / StandBy widget slot empty)
- Apple:FocusFilterIntent absent on a notification-heavy app
- Apple:SilentPushiOS handler always returns .noData (APNs throttles
  future silent pushes)

Every finding must include a Verification field. For iOS this is
usually `code` (inspectable from Info.plist / source) or `runtime`
(requires real-device test):
- Plist:UIRequiresFullScreen / Plist:UIApplicationSceneManifest /
  Plist:UISupportedInterfaceOrientations → runtime (rebuild + iPad
  simulator Stage Manager + Split View + Slide Over + rotation)
- Apple:BGTaskScheduler → runtime (lldb
  `_simulateLaunchForTaskWithIdentifier`)
- Apple:DynamicIsland → runtime (real iPhone 14 Pro+ — simulator does
  NOT render the Island)
- Apple:AppShortcut → runtime (real iPhone 15 Pro+ Action Button
  assignment via Settings)
- Apple:FocusFilterIntent → runtime (Settings → Focus → app filter)
- Apple:UIWindowSceneDelegate → runtime (cold-launch deep link from
  killed state via `xcrun simctl openurl booted <url>`)
- Pure Info.plist key changes with no scene / multitasking implication
  → code

"Manual review" alone is not sufficient verification for a Critical
finding on this audit.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to claude.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
