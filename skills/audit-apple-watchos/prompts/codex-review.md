Perform a thorough Apple watchOS audit of the scope at the project
root you've been pointed at. The project includes a watchOS target
(orient confirmed this; otherwise the audit would not have launched
you). Phase 1 tooling has been run; raw output is in the audit dir's
tooling-raw/ subdirectory. Read those files first:

- watch-targets.txt — detected watch targets and Info.plist subkeys
- watchos-deployment.txt — WATCHOS_DEPLOYMENT_TARGET (this drives
  ClockKit vs WidgetKit complication expectations)
- complication-impl.txt — ClockKit vs WidgetKit complication grep
- wcsession-usage.txt — WCSession callsites on both sides
- healthkit-workout-usage.txt — HKWorkoutSession / HKLiveWorkoutBuilder
  callsites and HealthKit entitlements
- watch-info-plists.txt — watch-target Info.plist subkeys
  (WKApplication, WKWatchOnly, WKCompanionAppBundleIdentifier,
  WKBackgroundModes)

Write all findings to codex.md (in the audit dir you were granted
write access to) using this exact table format:

| ID | Severity | Anchor | Category | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix C (e.g. C001, C002). Every finding MUST include
an Anchor (Apple symbol or doc reference — e.g.
Apple:WCSession, Apple:WidgetKit.accessoryCircular,
Apple:HKLiveWorkoutBuilder, Apple:isLuminanceReduced,
Apple:CLKComplicationDataSource,
Apple:WKApplicationRefreshBackgroundTask) and a Category from:
WCSession, Complications, AlwaysOnDisplay, BackgroundRefresh,
WatchOnlyVsCompanion, DigitalCrown, WorkoutsHealthKit,
WatchNavigation, WatchNotifications, WatchMemory, WatchInstaller,
WatchExtensionLifecycle. Platform: usually watchOS; Multi when a
paired iOS-side counterpart is involved.

Verification: code (inspectable from source) or runtime (requires a
real watch on the wrist — the simulator lies about memory pressure,
always-on rendering, and paired-iPhone reachability).

DO NOT review Widget / complication extension internals at the
NSExtension Info.plist / getTimeline budget level — that belongs in
audit-apple-extensions. DO NOT review iOS-side BGTaskScheduler — that
belongs in audit-apple-ios. This audit covers the watch app
itself: WCSession on the watch side, complications as watch features,
always-on rendering, HealthKit workouts on the watch, watch-side
memory budget, watch navigation, and the WatchKit-specific background
refresh task types.

Cover these 12 categories (skip if not applicable):

(1) WCSession — WCSession.default.activate() called on BOTH sides
(iPhone and Watch); WCSessionDelegate set before activate;
activationDidCompleteWith handler implemented; transferUserInfo
(queued, durable across launches) vs transferFile (large blobs) vs
sendMessage (live, both sides reachable) vs updateApplicationContext
(latest-only, replaces previous) chosen appropriately; isPaired /
isWatchAppInstalled / isReachable checks before sendMessage;
sessionReachabilityDidChange handling; sessionWatchStateDidChange
when complication state matters.

(2) Complications — WidgetKit-based complications on watchOS 10+:
StaticConfiguration / AppIntentConfiguration / IntentConfiguration
with supportedFamilies including .accessoryCircular,
.accessoryRectangular, .accessoryInline, .accessoryCorner. ClockKit
CLKComplicationDataSource acceptable ONLY when
WATCHOS_DEPLOYMENT_TARGET < 10.0. Flag ClockKit-only complication
code on a project whose watchOS deployment target is 10.0+ — Apple
has deprecated ClockKit and these complications will eventually break
on a future OS update.

(3) AlwaysOnDisplay — .privacySensitive() on views containing PII
(notifications, messages, health data, passwords); always-on
rendering downsampling; @Environment(\.isLuminanceReduced) observed
and the rendering path adapted (subdued colors, no animation, no
fine detail); brightness-aware color choices. Missing
.privacySensitive() on a PII-containing always-on view is a glance
attack — a sleeping device on a desk reveals notification content.

(4) BackgroundRefresh — WKApplicationRefreshBackgroundTask budget
(minutes per day, throttled aggressively by the OS);
WKURLSessionRefreshBackgroundTask for network completion;
WKSnapshotRefreshBackgroundTask for complication snapshot refresh;
WKRelevantShortcutRefreshBackgroundTask;
WKWatchConnectivityRefreshBackgroundTask;
scheduleBackgroundRefresh(withPreferredDate:userInfo:scheduledCompletion:)
discipline; setTaskCompletedWithSnapshot(_:) discipline — not calling
it leaks system time and the OS throttles future schedules.

(5) WatchOnlyVsCompanion — Architecture declared via WKWatchOnly=true
(independent, watchOS 9+) or WKCompanionAppBundleIdentifier (embedded
paired app). Flag companion-only workflows where the watch app does
nothing without iPhone reachability — Apple guidance is that watch
apps should provide some standalone utility where possible.

(6) DigitalCrown — .digitalCrownRotation modifier with appropriate
bounds (from:through:by:), sensitivity, isContinuous, and
isHapticFeedbackEnabled; .focusable() chained correctly so crown
rotation routes to the intended view; primary scrollable surfaces
respond to the crown (not just touch).

(7) WorkoutsHealthKit — HKWorkoutSession state-machine
(.prepare() → .startActivity(with:) → .end()) — misuse loses workout
data; HKLiveWorkoutBuilder .beginCollection / .endCollection /
.finishWorkout discipline; HKLiveWorkoutBuilderDelegate collecting
samples off the main thread; background delivery via HKObserverQuery
with enableBackgroundDelivery; watch-specific HealthKit entitlements
(com.apple.developer.healthkit, com.apple.developer.healthkit.background-delivery).

(8) WatchNavigation — NavigationSplitView (watchOS 10+) or
NavigationStack; deprecated NavigationView flagged on watchOS 10+;
TabView with .tabViewStyle(.verticalPage) for vertical paging where
appropriate; HStack-based UIs adapted to crown-driven scrolling.

(9) WatchNotifications — Watch-specific UNNotificationCategory and
notification actions; Notification Content Extension for watch where
rich content needed; iPhone-mirroring vs dedicated watch handling;
UNNotificationServiceExtension absent on watch target (NSE is
iOS-only — common confusion).

(10) WatchMemory — Active-app memory budget ~24MB; image loading via
low-res variants; avoid synchronous fetch of high-resolution remote
images on cold launch; SwiftUI body re-computation budget tighter
than iPhone (less main-thread headroom); large data structures kept
out of @State on the root view.

(11) WatchInstaller — Watch app bundle: embedded in iPhone app vs
independent (WKWatchOnly=true, watchOS 9+); WKCompanionAppBundleIdentifier
matches the iPhone target's bundle ID when embedded;
WKRunsIndependentlyOfCompanionApp consistent with the architectural
choice.

(12) WatchExtensionLifecycle — Connectivity-triggered launch budget
(small window to handle didReceiveMessage / file before suspension);
WCSessionDelegate.session(_:activationDidCompleteWith:error:) handler
discipline; complication snapshot delivered via
setTaskCompletedWithSnapshot(_:); cleanup on app-background
equivalent.

Rate severity on evidence: impact (workout data lost, watch app
crashes cold-launch, complication never updates, PII visible on
always-on, iPhone↔Watch sync silently broken), reachability (every
watch user vs paired-only vs locked-iPhone-only vs always-on-only),
blast radius, compensating controls.

Critical anchors:
- Watch app crashes on cold launch (typically: too-large startup
  memory exceeding ~24MB budget)
- WCSession not activated on one side → iPhone↔Watch communication
  silently impossible, every message queues forever
- HKWorkoutSession state-machine misuse → workout data lost mid-session

High anchors:
- ClockKit complication on watchOS 10+ (deprecated, will eventually
  break) — Apple:CLKComplicationDataSource
- Always-on display shows PII because .privacySensitive() is missing
  on the relevant view — Apple:isLuminanceReduced
- Background refresh budget exceeded — no scheduled updates fire,
  complication stales — Apple:WKApplicationRefreshBackgroundTask
- transferFile not deferred to transferUserInfo queue when reachability
  is false — file send drops silently

Every finding must include a Verification field. Memory, always-on,
and paired-reachability findings almost always require runtime
verification on real hardware — mark Verification=runtime.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to codex.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
