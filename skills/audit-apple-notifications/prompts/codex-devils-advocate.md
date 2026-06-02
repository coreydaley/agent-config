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
- Evidence: file:line citation, entitlement value, APNs header reference, or specific source line
- Confidence: high | medium | low

Cover these challenge categories:

(1) False positives — findings that don't actually apply in context.
Specifically for Apple notifications:
- An `aps-environment=development` flagged as Critical is actually in
  a Debug-only entitlements file used only by local builds; the
  Release config has its own entitlements file with `production`.
  Re-read aps-environments.txt and identify which configuration each
  entitlement file feeds before flagging Critical.
- A `UNUserNotificationCenter.current().delegate` assignment that
  looks late (in a view controller) is actually mirrored by an
  earlier assignment in `application(_:didFinishLaunchingWithOptions:)` —
  the later one is defensive / redundant rather than the canonical
  wiring site.
- A `.criticalAlert` request flagged as Critical may be guarded by a
  feature flag or by a check for the entitlement before requesting —
  the request never actually goes out without the entitlement present.
- A `requestAuthorization` flagged as "at launch" is actually inside
  a conditional that only fires for a specific user journey
  (post-sign-in, post-onboarding-step-3); the surrounding context
  makes it contextual rather than first-launch.
- Missing `INSendMessageIntent` donation flagged on a non-messaging app
  — Communication Notifications apply only to messaging-style apps;
  the "Communication" capability declaration is the actual
  prerequisite to flag, not the absence of donation in a feed app.
- Missing NSE for a payload that includes `mutable-content: 1` may be
  for a target that ships without rich attachments by design; the
  server may set `mutable-content` defensively but the client doesn't
  use it. Verify against the actual payload-strings.txt usage before
  declaring "rich-notification dead-letter".

(2) Severity miscalibrations — findings rated too high (the issue is
in a Debug-only entitlements file; the issue is gated by a feature
flag; the issue is in a non-shipping internal-tools target; the
authorization request is contextual when read with surrounding
control flow) or too low (the entitlement mismatch is in the Release
config but the synthesis rated it High — it's Critical because every
Release user is affected; the delegate is wired only inside a
ViewController.viewDidLoad and the app is push-driven — every cold
launch loses the first push; the payload includes literal hardcoded
PII in `loc-args` — promote from PayloadHygiene Medium to High because
of privacy implications).

(3) Missing findings — Apple-notifications issues both reviewers may
have missed:
- macOS / Mac Catalyst-specific: `aps-environment` declared in iOS
  entitlements but not in the macOS target's entitlements; or the
  reverse — declared on macOS without the user-facing notification
  flow being implemented on the Mac.
- watchOS-specific: Apple Watch shows iPhone notifications by default
  (forwarded), but if the watch app schedules its own local
  notifications, it needs `UNUserNotificationCenter` configured on the
  watch side too.
- visionOS-specific: notification permission flow on visionOS
  surfaces differently (ornament vs alert); flag if the visionOS
  target uses an iPad-style flow without adaptation.
- Push topic mismatches: `apns-topic` literal in test fixtures or
  server SDK glue doesn't match the actual bundle id; the test push
  succeeds but production pushes fail with bad-topic.
- Notification Service Extension that exists but never short-circuits
  to `contentHandler(bestAttemptContent)` in
  `serviceExtensionTimeWillExpire()` — the NSE times out and the
  original (unmodified) content is shown; users see the plain payload
  instead of the rich one. (This is NSE *implementation* — would also
  be caught by audit-apple-extensions, but flag here when it's
  obvious from the host-app wiring.)
- `application(_:didRegisterForRemoteNotificationsWithDeviceToken:)`
  not implemented at all, only `applicationDidFailToRegisterForRemoteNotifications`
  — the app never sends the device token to the server, so push will
  never work no matter how perfect the entitlements are.
- `UNUserNotificationCenter.current().getDeliveredNotifications` /
  `getPendingNotificationRequests` used in a way that doesn't
  account for the async nature — assumptions about delivered state in
  synchronous code lead to bad badge counts and stale UI.
- App Group missing for an NSE that needs to share attachment cache
  with the host; the NSE downloads the attachment but the host can't
  read it later from the notification UI.
- `interruptionLevel: .active` (the default) on a notification that
  has urgent / time-sensitive content — opportunity miss for
  `.timeSensitive` when the user has Focus enabled.

(4) Missing compound paths — separate findings in the synthesis that
combine into a worse outcome than any single finding represents:
- "Push silent on Release" chain (aps-environment=development in
  Release.entitlements + no NSE + first push happens on cold launch)
  — already covered, but check whether all conditions are present.
- "App Review rejection on resubmission" chain (.criticalAlert in
  authorization options + no Apple-issued critical-alerts entitlement +
  alert copy claiming "critical").
- "First push lost" chain (delegate assigned in viewDidLoad / .onAppear
  + app is push-driven so cold launch IS the entry).
- "Communication notification empty avatar" chain (no INSendMessageIntent
  donation + Communication capability declared + thread-id payload).
- "Rich-notification dead-letter" chain (mutable-content:1 + no NSE +
  payload references attachment).

(5) Impractical / incomplete / wrong remediations — e.g.:
- "Move `aps-environment` to `production`" without acknowledging that
  the entitlements file must be re-signed and the build re-archived —
  changing the .entitlements file in Xcode alone doesn't update the
  signed `.app`.
- "Move `requestAuthorization` to a contextual moment" without
  specifying which onboarding step or user action — the developer
  needs a concrete location, not just "later."
- "Add an NSE" without specifying the NSE target's bundle id /
  entitlements / App Group — adding the target template is the start,
  not the fix.
- "Donate INSendMessageIntent" without specifying the INPersonHandle
  identifier format the server uses — a malformed handle still breaks
  the avatar render.
- "Set the delegate in AppDelegate" when the project is a SwiftUI App
  without a UIApplicationDelegateAdaptor — the developer needs the
  adaptor pattern, not just "use AppDelegate."

(6) Verification steps that don't actually prove the fix works — e.g.
"verify by sending a local notification" when the issue is APNs
remote-push delivery (local notifications bypass the APNs gateway
entirely); "verify in Simulator" when push delivery requires a real
device (Simulator does support push as of recent Xcode but only via
the .apns file drag — true APNs gateway testing needs hardware);
"verify by inspecting the entitlements file" when the canonical
source of truth is the signed `.app`'s embedded entitlements
(developers fix the source file but forget to re-archive); "verify by
checking the OS prompt appears" when the bug is the prompt's options
list being wrong.

Be specific. Every challenge must cite the finding ID and reference
the entitlement value / APNs header / source line where applicable.

Do not read or reference any other review file beyond synthesis.md and
the tooling-raw/ directory.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type
  "no_challenges" and Confidence "high" stating that you attempted but
  found nothing worth surfacing.
- No emojis.
