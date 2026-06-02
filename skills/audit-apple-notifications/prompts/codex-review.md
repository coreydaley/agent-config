Perform a thorough Apple platform notifications review of the scope at
the project root you've been pointed at. Tooling has already been run;
raw output is in the audit dir's tooling-raw/ subdirectory. Read those
files first:

- aps-environments.txt — every aps-environment value extracted from every
  entitlement file. **Diffing the value against the configuration the
  target ships in is the single highest-yield activity for this audit.**
  A `development` value in Release.entitlements silently breaks push on
  every Release device — production tokens are rejected by the sandbox
  gateway and the device never receives anything.
- background-modes.txt — UIBackgroundModes per Info.plist; presence of
  `remote-notification` is required for silent push (`content-available:
  1`) to wake the app.
- un-center-calls.txt — UNUserNotificationCenter / authorization grep:
  requestAuthorization options, getNotificationSettings, .notDetermined
  / .authorized / .denied / .provisional handling.
- categories-and-actions.txt — UNNotificationCategory /
  UNNotificationAction / UNTextInputNotificationAction / setNotificationCategories
  declarations.
- intents-donation.txt — INSendMessageIntent / INPersonHandle /
  INInteraction / .donate( calls. Communication Notifications require
  donation before scheduling for the avatar / Communication tile to
  render correctly.
- nse-targets.txt — Notification Service Extension target detection (host
  for rich notifications, encrypted-payload decryption, dynamic
  modification).
- nce-targets.txt — Notification Content Extension target detection
  (custom UI for the expanded notification).
- delegate-wiring.txt — UNUserNotificationCenter.delegate assignments,
  willPresent / didReceive locations, didRegisterForRemoteNotificationsWithDeviceToken.
- payload-strings.txt — literal apns-push-type / apns-priority / apns-topic /
  mutable-content / content-available / interruption-level / thread-id
  occurrences in Swift / Obj-C / JSON.

Write all findings to codex.md (in the audit dir you were granted write
access to) using this exact table format:

| ID | Severity | Anchor | Category | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix C (e.g. C001, C002). Every finding MUST include an
Anchor (e.g. Apple:UNUserNotificationCenter, Entitlement:aps-environment,
APNs:apns-push-type, Apple:INSendMessageIntent, Info.plist:UIBackgroundModes)
and a Category from: APNsEntitlement, AuthorizationFlow, Categories,
Actions, RichNotifications, CommunicationNotifications,
FocusCriticalAlerts, TimeSensitive, ProvisionalAuth, PayloadHygiene,
DelegateLifecycle, NotificationsExtensionsLink. Platform: iOS, iPadOS,
macOS, MacCatalyst, watchOS, tvOS, visionOS, or Multi.

DO NOT review Notification Service Extension / Notification Content
Extension *internals* (memory budget, time budget, App Group attachment
plumbing, NSE-internal threading) — that belongs in
audit-apple-extensions. This audit flags that an NSE is *required*
given the payload shape and that the wiring is correct at the host-app
boundary; it does not review NSE implementation depth. DO NOT review
iOS-distinctive silent-push *lifecycle* (UIApplicationDelegate
`application(_:didReceiveRemoteNotification:fetchCompletionHandler:)`,
UIBackgroundFetchResult, BGTask scheduling triggered by silent push,
fetch frequency throttling, background work the push initiates,
`UIBackgroundModes:remote-notification` semantics) — that belongs in
audit-apple-ios. This audit flags that `apns-push-type: background` is
set; iOS lifecycle depth lives in audit-apple-ios. DO NOT review
macOS-distinctive notification delivery (NSUserNotificationCenter
legacy bridges, menu-bar notification center) — that belongs in
audit-apple-macos. DO NOT review watchOS notification-forwarding rules
(iPhone-vs-watch delivery decisions, WCSession mirroring) — that
belongs in audit-apple-watchos. DO NOT review Privacy Manifest /
Required Reason API declarations — those belong in audit-apple-privacy.

Cover these 12 categories (skip if not applicable):

(1) APNsEntitlement — `aps-environment` set to `development` or
`production` and consistent with the build configuration that ships the
target. Release.entitlements MUST be `production` for App Store /
TestFlight builds; `development` silently fails on every Release device
because production tokens are rejected by the sandbox gateway. APNs
auth key (`.p8`, preferred) vs certificate (`.p12`, legacy — flag if
nearing expiration). Bundle identifier matches the APNs topic on the
server.

(2) AuthorizationFlow — `UNUserNotificationCenter.current().requestAuthorization(options:)`
called with appropriate options (`.alert`, `.badge`, `.sound`, and
optionally `.provisional`, `.criticalAlert`, `.timeSensitive`).
Requested at a contextual moment (mid-onboarding, after a user-driven
action), NOT on first launch (anti-pattern; conversion is poor and
documented as such). `getNotificationSettings` called before any UI
that depends on authorization state. `.notDetermined`, `.denied`, and
`.authorized` paths handled distinctly — code that assumes binary
denied/authorized misses the not-yet-asked state.

(3) Categories — `UNNotificationCategory` declared with a stable
identifier and a sane action set. `UNNotificationAction` instances
configured with `destructive` / `foreground` / `authenticationRequired`
options as appropriate. `setNotificationCategories(_:)` called on
`UNUserNotificationCenter.current()` before any notification using the
category is scheduled — declared-but-never-registered categories are
ignored, action buttons silently don't appear.

(4) Actions — `UNTextInputNotificationAction` for reply flows; action
handler logic in `userNotificationCenter(_:didReceive:withCompletionHandler:)`;
the `completionHandler` MUST be called or the system stalls waiting
and the notification UI doesn't dismiss cleanly. Same for the `willPresent`
foreground-presentation handler.

(5) RichNotifications — Server payload includes `mutable-content: 1`
AND a Notification Service Extension target exists in the bundle AND
the NSE's `aps-environment` matches the host's (development matches
development, production matches production). The `category` value on
the payload matches a declared `UNNotificationCategory`. Attachment
URLs referenced in the modified content are reachable / cacheable.

(6) CommunicationNotifications — `INSendMessageIntent` donated via
`INInteraction(intent:response:).donate(completion:)` BEFORE the
notification is scheduled. `INPersonHandle.value` and `.type`
populated correctly so iOS can map sender → contact. Avatar image
attached via `INImage(imageData:)` or `INImage(url:)`. `NSUserActivityTypes`
in Info.plist contains the intent type. The "Communication" capability
declared in Xcode (Signing & Capabilities). Without these the avatar /
tinted Communication tile falls back to a generic look and the iOS 15+
Communication design wins are lost.

(7) FocusCriticalAlerts — `UNAuthorizationOptions.criticalAlert`
requires the `com.apple.developer.usernotifications.critical-alerts`
entitlement, which is issued only via Apple application + approval.
Requesting `criticalAlert` without the entitlement causes App Review
rejection (the developer must justify the criticality on submission
and Apple grants per-app). `interruptionLevel: .critical` only on
truly critical content (medical alerts, security incidents). Note
that `summary` / `summaryArgument` from iOS 12 are deprecated in
favor of `interruptionLevel` + `relevanceScore` for stacking — flag
mixed-era code.

(8) TimeSensitive — `interruptionLevel: .timeSensitive` requires the
`com.apple.developer.usernotifications.time-sensitive` entitlement
(unlike `.critical`, this entitlement does not require Apple approval —
it's declared by the developer, but Apple may flag abuse on review).
Time-sensitive notifications break through Focus modes when the user
opts in. Used sparingly is the principle — if every notification is
`.timeSensitive`, Focus filtering kicks in anyway and trust is lost.

(9) ProvisionalAuth — `.provisional` option allows quiet-only
delivery without prompting the user; appropriate for messaging-style
or feed-style apps that want to demonstrate value before asking for
full permission. The OS surfaces "Keep" / "Turn Off" actions in the
delivered notification; the app handles these via
`UNUserNotificationSettings` changes on next `getNotificationSettings`
call.

(10) PayloadHygiene — All platforms. APNs request headers correct:
`apns-push-type` matches the payload shape (`alert | background |
location | voip | complication | fileprovider | mdm`); missing
`apns-push-type: background` on a silent push causes APNs to drop
without delivery. (Note: `background` push *delivery* lifecycle is
iOS / iPadOS / visionOS only — for the host-app lifecycle hook depth,
see audit-apple-ios.)
`apns-priority` set to 10 (immediate) or 5 (power-conserving) — never
omitted; 10 with `content-available: 1` is rate-limited by APNs.
`apns-topic` matches the receiving bundle id (or `<bundle-id>.complication`
etc. for variants). `apns-collapse-id` for deduplication.
`apns-expiration` to prevent stale notifications. Payload size MUST be
under 4KB (APNs rejects with PayloadTooLarge). Use of `title-loc-key` /
`loc-key` / `loc-args` for localization instead of hardcoded strings.
`thread-id` for grouping in chat-style apps.

(11) DelegateLifecycle — `UNUserNotificationCenter.current().delegate`
assignment timing. iOS / iPadOS / tvOS / visionOS (UIKit family):
inside `application(_:didFinishLaunchingWithOptions:)` (the
UIApplicationDelegate). SwiftUI apps: inside the `App.init()` or via
a `@UIApplicationDelegateAdaptor` AppDelegate. macOS (AppKit): inside
`applicationDidFinishLaunching(_:)` of the NSApplicationDelegate or
`App.init()` for SwiftUI. NEVER in `viewDidLoad` of a root view
controller or in `.onAppear` of the first scene — those fire AFTER
the system has already attempted to deliver the cold-launch
notification, and the first push is lost. `willPresent` and
`didReceive` must always invoke their completion handler. Flag the
legacy `application(_:didReceiveRemoteNotification:fetchCompletionHandler:)`
still being present alongside the modern delegate (mostly harmless
but a code-hygiene flag; iOS-lifecycle depth lives in audit-apple-ios).

(12) NotificationsExtensionsLink — Notification Service Extension /
Notification Content Extension entitlements consistent with the host
app's `aps-environment`. App Group declared on BOTH host and NSE for
shared attachment / state access (an NSE that needs to cache an
attachment for the host app cannot do it without the App Group). Deep
link handling from `response.notification.request.content.userInfo`
parses into the same routing layer used by Universal Links (no
duplicated parsing — they should both feed one Router).

Rate severity on evidence: impact (what fails for users), reachability
(does the Release config see it), blast radius (every push user vs
only-first-cold-launch vs only-Focus-users), compensating controls (server
retry on alt gateway, feature-flag gating).

Critical anchors:
- `aps-environment=development` in Release.entitlements — push silently
  fails on every Release device (sandbox tokens, production gateway
  rejects them)
- `.criticalAlert` requested in authorization options without the
  Apple-issued `com.apple.developer.usernotifications.critical-alerts`
  entitlement — App Review rejects on submission
- `willPresent` / `didReceive` completion handler not invoked — system
  stalls, notification UI doesn't render
- `UNUserNotificationCenter.current().delegate` assigned after first
  push delivery (in a view controller's `viewDidLoad`, in `.onAppear`
  of a scene) — first push from a cold launch is silently dropped, the
  most common entry path for push-driven apps
- Server payload includes `mutable-content: 1` but no NSE target
  exists in the bundle — server expects content modification that
  never happens; attachments don't render and rich-notification design
  intent is lost

High anchors:
- `requestAuthorization` called on app launch instead of a contextual
  moment — anti-pattern; conversion is poor and App Review may flag
- `apns-push-type: background` missing on a silent push — APNs drops
- Payload size exceeds 4KB — APNs rejects with PayloadTooLarge
- Communication Notification flow without `INSendMessageIntent`
  donation — avatar falls back to generic, breaks iOS 15+ Communication
  tile
- `.timeSensitive` requested without the
  `com.apple.developer.usernotifications.time-sensitive` entitlement —
  Apple silently demotes to `.active`, no error surfaced

Every finding must include a Verification field — for notifications
this is usually a *live sandbox APNs push* (via `apns` CLI or `Knuff`
against the device token) with `Console.app` filtered on `subsystem:
com.apple.usernotifications`. For entitlement findings: `codesign
--display --entitlements -` against the built `.app`. For
delegate-lifecycle: a cold-launch-from-notification-tap test. "Manual
code review" alone is not sufficient verification for a Critical.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to codex.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
