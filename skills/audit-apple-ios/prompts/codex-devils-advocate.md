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
- Evidence: file:line citation, Info.plist key, or specific source symbol
- Confidence: high | medium | low

Cover these challenge categories:

(1) False positives — findings that don't actually apply in context.
Specifically for Apple iOS:
- `Plist:UIRequiresFullScreen=YES` flagged as Critical for "breaking
  iPad multitasking" — re-check whether the app is actually a game,
  immersive AR experience, or single-purpose camera tool where
  fullscreen IS the intended UX. The check is the App Store category:
  Games / AR / a kiosk-mode app legitimately wants this. Productivity
  / utility / lifestyle / social apps do not.
- `Plist:UISupportedInterfaceOrientations` portrait-only flagged on
  iPad — re-check whether the iPad target is intentionally
  iPhone-idiom (TARGETED_DEVICE_FAMILY=1) and only runs on iPad in
  compatibility mode; portrait-only is the OS default for iPhone-only
  apps and isn't a finding there.
- `Plist:UIBackgroundModes` flag flagged as "unused" because no direct
  callsite was found in source — re-check for use via a private API
  path (the flag may be required because a vendored framework / SDK
  uses the capability via its own internal call), or because the
  callsite is in an extension target (Notification Service Extension,
  Network Extension) not in the main app source.
- `Apple:DynamicIsland` flagged as "missing" because no
  `dynamicIsland` builder is present — re-check whether the app's
  activities are intentionally ephemeral (<8h) and rendered only on
  the Lock Screen (Apple's guidance: not every Live Activity needs
  Dynamic Island; pizza-tracker yes, single-shot timer yes,
  ride-share-arriving yes, a five-minute task-completion banner no).
- `Apple:UIPointerInteraction` flagged on an iPad-supporting app
  that's actually a game — pointer interactions are not expected on
  game canvases; the iPad-pointer finding applies to productivity
  surfaces.
- `Apple:AppShortcut` flagged as "missing for Action Button" on an
  app where the app's value prop has no single-press affordance
  (passive consumption app, social feed). The Action Button mapping
  is useful where there IS a recurring action; not every app needs
  one.

(2) Severity miscalibrations — findings rated too high (the
`UIRequiresFullScreen` setting IS in a game / AR / kiosk target where
it's correct; the missing `UIWindowSceneDelegate` is on a watchOS-only
target that doesn't have scenes anyway; the missing `BGTaskScheduler`
registration is on an iPad-only kiosk app permanently plugged in to a
charger) or too low (the missing register-too-late call DOES affect
every cold launch; the unused `UIBackgroundModes` flag IS the
App-Review-rejection root cause; the Stage Manager break IS direct
revenue loss).

(3) Missing findings — Apple-iOS issues both reviewers may have
missed:
- **Scene state-restoration NSUserActivity payload > 100KB** — the
  system silently drops oversized payloads and the app reopens to a
  blank state. Look for large model-object encoding into
  `stateRestorationActivity(for:)` without size budgeting.
- **Deep-link cold-launch race in `viewDidLoad`** — root VC sets the
  UNUserNotificationCenter delegate or the URL session delegate in
  `viewDidLoad`, but the cold-launch URL arrives in
  `scene(_:willConnectTo:)` *before* the root VC's view is loaded;
  the delegate is unset when the URL is delivered and the deep link
  is dropped.
- **Live Activity push token lifecycle** — code calls
  `Activity.request()` but never subscribes to
  `Activity.pushTokenUpdates` AND `Activity.pushToStartTokenUpdates`;
  server can never reach the activity to update / end it.
- **`apns-push-type: background` mismatch** — server sends silent
  push without the required `apns-push-type: background` header
  (Apple silently drops or throttles).
- **`UIScene` not declared in Info.plist's
  `UIApplicationSceneManifest`** — the app has a SceneDelegate in
  source but no scene configuration in Info.plist; the system falls
  back to a default scene config, scene-specific deep links don't
  reach the right delegate.
- **`BGTaskScheduler.shared.cancel(taskRequestWithIdentifier:)`
  missing on logout / data-reset** — old user's pending background
  task fires under a new user's session, refreshing data the new
  user shouldn't see.
- **`expirationHandler` is async** — `expirationHandler` body uses
  `Task { ... }` or `DispatchQueue.async` without an `await
  task.value` / synchronous waitFor; the OS kills the process before
  the async work completes, and the in-flight network call is lost
  (incomplete sync / corrupted local state).
- **`UIRequiredDeviceCapabilities` over-restricted** — declares
  capabilities the app doesn't actually need (e.g. `armv7` on a
  modern app, `telephony` on an iPad-only app), reducing the
  installable device population.
- **`UIPointerInteractionDelegate` returns nil for `region` /
  `style`** — pointer is technically adopted but does nothing
  visible; iPad cursor users see no hover affordance.
- **`AVCaptureControl` missing on a camera-first app on iOS 18+
  iPhone 16** — Camera Control button does nothing for this app
  when the user expects native camera control.

(4) Missing compound paths — separate findings in the synthesis that
combine into a worse outcome than any single finding represents:
- "iPad multitasking broken" chain — already documented; re-check
  whether all three constituents (UIRequiresFullScreen=YES,
  portrait-only orientations, missing scene manifest) are present
  before claiming the chain.
- "Cold-launch deep link lost" chain (pre-scene-lifecycle +
  AppDelegate-only handler + delegate set in viewDidLoad).
- "Background tasks silently never run" chain (register-too-late +
  missing PermittedIdentifiers + submit-never-called-on-launch).
- "Lock Screen widget AOD leak" chain (Live Activity ContentState
  with PII + missing privacySensitive + contentMarginsDisabled
  full-bleed).
- "Dynamic Island truncation" chain (variable-length content +
  no responsive compact-state design + no test for the longest
  string).
- "Action Button orphan" chain (iPhone 15 Pro+ user expects Action
  Button assignment + no AppShortcutsProvider declared).

(5) Impractical / incomplete / wrong remediations — e.g.:
- "Set `UIRequiresFullScreen = NO`" without specifying the
  multitasking-layout work that follows (the app's UI may have
  hardcoded width assumptions that break in Split View; flipping
  the key alone trades App-Review-pass for a broken layout).
- "Register BGTask in `applicationDidFinishLaunching`" without
  specifying which lifecycle method on the SwiftUI App / SceneDelegate
  pathway is the SwiftUI-equivalent entry point (`init()` of the
  `@UIApplicationDelegateAdaptor`).
- "Add `UIWindowSceneDelegate`" without acknowledging the migration
  work (state restoration model changes, AppDelegate URL handler
  must be removed or `application(_:open:)` will silently shadow
  `scene(_:openURLContexts:)`).
- "Add Dynamic Island support" without specifying how to test
  (the simulator does not render the Island; a real iPhone 14 Pro+
  is required).
- "Add `FocusFilterIntent`" without specifying the App Intents
  framework dependency and the `INFocusStatusCenter` authorization
  flow.

(6) Verification steps that don't actually prove the fix works — e.g.
"verify by running in simulator" for a Dynamic Island fix (simulator
does NOT render the Island); "verify by tapping the Action Button" for
an AppShortcut fix when the Action Button isn't assigned to the app
(the assignment happens in Settings, not via app code);
"verify by checking the Info.plist key" for a multitasking fix when
the actual symptom is at Stage Manager runtime; "manual code review"
verification for a BGTask registration timing issue (the timing only
manifests when the scheduler tries to launch the task, which only
happens via `_simulateLaunchForTaskWithIdentifier` or a real overnight
scheduler run).

Be specific. Every challenge must cite the finding ID and reference
the Info.plist key / source symbol / lockfile line where applicable.

Do not read or reference any other review file beyond synthesis.md and
the tooling-raw/ directory.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type
  "no_challenges" and Confidence "high" stating that you attempted but
  found nothing worth surfacing.
- No emojis.
