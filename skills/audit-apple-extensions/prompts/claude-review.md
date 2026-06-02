You are an INDEPENDENT reviewer. You did NOT write the code or artifact
under review — approach it with fresh eyes and review it on its merits alone.
(The Claude session that invoked this audit may well have authored what you
are now reviewing; that is exactly why this review is delegated to you rather
than done in that session, which would share its own blind spots.)

Write your findings to claude.md (ID prefix A) per the specification below.

Perform a thorough Apple app-extension review of the scope at the
project root you've been pointed at. The audit targets every `.appex`
extension target the project ships plus the App-Group / entitlement
plumbing that connects them to the host app. Tooling has already been
run; raw output is in the audit dir's tooling-raw/ subdirectory. Read
those files first:

- appex-targets.txt — every detected extension target, its
  NSExtensionPointIdentifier, NSExtensionPrincipalClass /
  NSExtensionMainStoryboard, and NSExtensionAttributes. **This is the
  authoritative list of extension types to walk.**
- extension-entitlements.txt — every .entitlements file in the project
- host-app-entitlements.txt — same file, kept separately for
  drift-diff convenience
- app-groups.txt — App Group identifiers declared in entitlements vs
  referenced in code (suiteName: / containerURL:)
- info-plists.txt — every Info.plist in the project
- extension-budgets.txt — OS-imposed memory budgets per extension type
  (reviewer reference; treat as anchors for Critical severity)

Write all findings to claude.md (in the audit dir you were granted write
access to) using this exact table format:

| ID | Severity | Anchor | Category | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix A (e.g. A001, A002). Every finding MUST include an
Anchor (e.g. ExtensionType:WidgetKit, Apple:NSExtension,
File:NSE/NotificationService.swift) and a Category from: WidgetKit,
LiveActivity, AppIntents, NotificationServiceExtension,
NotificationContentExtension, ShareExtension, ActionExtension,
SafariWebExtension, KeyboardExtension, FileProvider, AutoFillExtension,
ExtensionsCommon. Platform: iOS, iPadOS, macOS, MacCatalyst, watchOS,
tvOS, visionOS, or Multi.

DO NOT review host-app background execution (BGTaskScheduler, background
URLSession on the host) — that belongs in audit-apple-ios. DO
NOT review notification UX / authorization / permission flow (the
audit's notification scope is the NSE + content-extension *contract*,
not the host app's UNUserNotificationCenter flow) — that belongs in
audit-apple-notifications. DO NOT review Keychain access patterns or
ATS inside extensions — those belong in audit-apple-security.

Cover these 12 categories (skip if the project does not ship that
extension type):

(1) WidgetKit — iOS / iPadOS / macOS / watchOS (visionOS planned).
Widget memory budget (~30MB on iOS / iPadOS family, OS-killed above;
TimelineProvider / AppIntentTimelineProvider correctness; getTimeline()
return latency (5-15s practical; >30s and the OS marks the timeline
stale and renders the placeholder); relevance scoring via
TimelineEntryRelevance for Smart Stack ordering; family availability
declared in supportedFamilies modifier (.systemSmall / .systemMedium /
.systemLarge / .systemExtraLarge / .accessoryCircular /
.accessoryRectangular / .accessoryInline); Configuration Intent
handling for user-customizable widgets; ContainerBackground modifier
(iOS 17+; required for Smart Stack / StandBy / Lock Screen rendering
to compose correctly); deep-link from widget via widgetURL / Link;
widget bundle declared via @main on WidgetBundle for projects that
ship multiple widgets.

(2) LiveActivity — iOS 16.1+ only (iPhone). ActivityKit attributes
vs content state separation
(attributes are immutable across activity lifetime; content state is
what updates); dynamic island content per state (compact, minimal,
expanded — all three required for any activity that targets devices
with the dynamic island); push token registration via
Activity.pushTokenUpdates async sequence; ActivityAuthorizationInfo
gating (user can disable Live Activities globally); 8-hour stale-date
discipline (Apple revokes activities older than 8h foreground / 12h
background); frequent state-update throttling (the system throttles
activities updating more than ~once-per-second); stale-state vs
ended-state distinction (.end vs .stale on Activity).

(3) AppIntents — iOS / iPadOS / macOS / watchOS. AppIntent /
AppShortcut declaration with @Parameter
property wrappers; parameter validation via IntentParameter.requestValue
/ IntentParameter.requestDisambiguation; EntityQuery /
EnumerableEntityQuery correctness (Suggested entities for Spotlight,
EntityStringQuery for type-ahead, EntityPropertyQuery for filters);
focus-filter intents declared via SetFocusFilterIntent; Spotlight
indexing via IndexedEntity conformance; perform() return shape
(IntentResult value / dialog / view / opens-intent); static var
openAppWhenRun semantics — `true` makes the intent require the app
foreground, `false` keeps the intent in-extension; App Shortcuts
phrase synonyms (provide multiple invocations for naturalness);
@Parameter requestValueDialog .always vs .adaptive (.always always
prompts; .adaptive uses context); IntentDescription and
parameterSummary populated for Spotlight surface.

(4) NotificationServiceExtension — iOS / iPadOS / macOS / watchOS.
NSE memory budget (24MB hard cap on iOS;
crossing it silently reverts the push to its unmodified server form
for the user); didReceive(_:withContentHandler:) and
serviceExtensionTimeWillExpire() discipline — both MUST eventually
call contentHandler; expiry fallback path that returns the original
bestAttemptContent on timeout (30s wallclock budget total); async
network calls that can exceed the 30s budget; attachment downloads
that should stream rather than buffer (large attachments blow the
24MB cap); content mutation requires `mutable-content: 1` in the APNs
payload (otherwise NSE is never invoked); shared keychain / App Group
access in NSE must not trigger expensive Core Data faulting.

(5) NotificationContentExtension — iOS / iPadOS / watchOS. Custom
UI for an expanded notification; UNNotificationExtensionCategory declared in Info.plist
under NSExtensionAttributes (categories must match the host app's
UNNotificationCategory identifiers); UNNotificationExtensionDefaultContentHidden
to suppress the standard body when the custom UI renders it;
UNNotificationExtensionInitialContentSizeRatio for default height;
action button handling via didReceive(_:completionHandler:); media
attachment dimensions and aspect ratio.

(6) ShareExtension — iOS / iPadOS / macOS. Activation rules
(NSExtensionAttributes.NSExtensionActivationRule); broad activation
rules (e.g. NSExtensionActivationSupportsWebURLWithMaxCount=1000) are
a CRITICAL surface-area smell because the extension now appears for
content it cannot actually handle; SLComposeServiceViewController vs
UIViewController choice (SLComposeServiceViewController is restricted
to text+attachments — fine for a Twitter-style share, wrong for a
rich editor); input item processing via extensionContext.inputItems;
document picker / "Open in" handoff to host app via App Group; missing
sandbox-respect when reading file URLs from a host process.

(7) ActionExtension — iOS / iPadOS / macOS. "In-place modification"
semantics (the host
gives the extension content; the extension may return modified content);
declaration of accepted UTIs (declared via
NSExtensionActivationDictionary or specific NSExtensionActivationRule);
response shape via extensionContext.completeRequest(returningItems:);
"action goes to view" UI variant (NSExtensionMainStoryboard or
NSExtensionPrincipalClass for the UI); silent action variant
(NSExtensionServiceRoleType).

(8) SafariWebExtension — iOS / iPadOS / macOS. manifest.json present
in the extension
bundle's Resources/ (WebExtension MV3 format expected); applicationName
in manifest matches the host app; native messaging declared via
NSExtensionPrincipalClass implementing SFSafariExtensionHandler / the
WebExtension messaging protocol; content scripts vs background scripts
correctly partitioned; host_permissions declarations matching declared
activeTab usage (overbroad host_permissions trigger App Review
rejection); incognito / Private Browsing behavior declared.

(9) KeyboardExtension — iOS only. RequestsOpenAccess flag (granting network +
broader sandbox access; default-NO is the App-Review-safe setting and
keyboards that flip it without a strong feature reason are routinely
rejected); dictation handling; tracking concerns (App Review rejects
keyboards that exfiltrate keystrokes); full access required for some
features (autocorrect-via-server, custom suggestion engines) but flag
if claimed without that feature actually being present; primaryLanguage
in NSExtensionAttributes; KeyboardExtension presets / suggestion-bar
discipline.

(10) FileProvider — iOS / iPadOS / macOS. FileProviderExtension
productType; NSFileProviderItem
identifier stability across the working set (identifiers MUST be
stable across the item's entire lifetime — re-issuing the identifier
for the same logical item silently corrupts the user's file mirror);
NSFileProviderEnumerator pagination correctness; conflict resolution
via fetchContents and createItem(basedOn:) (write-write conflicts MUST
preserve both copies); working-set enumerator vs container enumerator
performance; bandwidth and disk budgets (the OS suspends providers
that hammer disk).

(11) AutoFillExtension — iOS / iPadOS / macOS. Credential / Password /
Verification Code AutoFill — ASCredentialIdentityStore reload after the user adds /
deletes a credential (without reload, AutoFill cannot suggest the new
credential); ASCredentialProviderViewController lifecycle (prepareCredentialList,
prepareInterfaceToProvideCredential, prepareInterface(forExtensionContext:),
prepareOneTimeCodeCredentialList); locking the extension behind device
biometrics via LAContext; AutoFill domain matching against
ASPasswordCredentialIdentity.serviceIdentifiers.

(12) ExtensionsCommon — Host-app communication via App Groups
(UserDefaults(suiteName:), shared Core Data / SwiftData store with
NSPersistentCloudKitContainer using the App-Group container URL, file
coordination via NSFileCoordinator); shared keychain access groups
(kSecAttrAccessGroup matching the keychain-access-groups entitlement
on BOTH sides); entitlement consistency between host app and
extensions (capability present on host but missing on extension is a
Critical drift); extension target deployment target matching app's
(extension cannot run on an OS older than its MinimumOSVersion, and
cannot be newer than the host); main `_TtC` symbol clash risk when
extension and host app both embed the same Swift framework as a static
library; arc4random / Foundation initialization race in extension
processes (extensions start cold every time; expensive init in main()
blows the wallclock budget).

Rate severity on evidence: impact (what ships broken / silently
degraded), reachability (does every user hit this — Release-config
extension), blast radius (every NSE invocation vs only one widget
family vs only macOS extension), compensating controls (does the host
app retry the operation if the extension fails).

Critical anchors (specific Apple-shipping consequences):
- NSE exceeds 24MB → reverted-to-unmodified push for every user
  whose payload requires mutation (loc keys, attachments, custom
  badge math).
- Widget timeline blocks main thread or getTimeline() >30s → OS marks
  the timeline stale and the widget renders blank for every user.
- App Intent perform() takes >30s during Spotlight execution → the
  intent fails and Siri reports a generic error to the user.
- Live Activity push token registration broken
  (Activity.pushTokenUpdates never observed or token never sent to
  server) → every subsequent push-driven activity fails to update.
- Extension target missing an entitlement the host app has (Push
  Notifications, App Groups, iCloud, HealthKit) → IPC fails silently;
  user sees "feature works on the host but not the extension."
- Share Extension NSExtensionActivationRule matches everything
  (NSExtensionActivationSupportsWebPageWithMaxCount=1000 or similar
  >100 catchall) → the extension appears for content it can't handle
  AND for content it shouldn't surface for; App Review-adjacent risk.
- FileProvider NSFileProviderItemIdentifier instability across the
  working set → user's file mirror silently corrupts (mismatched
  identifiers on conflict resolution).

High anchors:
- Widget refresh interval more aggressive than 5min → OS throttles +
  battery warning in Console.
- App Shortcut phrase that conflicts with another installed app's
  shortcut → Siri disambiguation prompt every time, user gives up.
- NSE downloads attachment via URLSession.shared on a single long-lived
  task (expensive; risks the 30s budget).
- Keyboard Extension with RequestsOpenAccess=YES but no documented
  feature requiring it → App Review rejection on next submission.
- AutoFill extension that does not reload ASCredentialIdentityStore
  on credential save → user adds password, AutoFill suggests nothing.

Medium anchors:
- Widget missing ContainerBackground modifier on iOS 17+ (Smart Stack
  / StandBy rendering misaligned).
- App Intent parameter not requesting a value when required → intent
  performs with a nil value and returns a partial result.
- AccentColor not configured for widget asset catalog → widget renders
  in default tint on Smart Stack.
- App Intent missing IntentDescription / parameterSummary → Spotlight
  surface looks unfinished.

Low anchors:
- Suboptimal widget family choices (e.g. shipping `.systemExtraLarge`
  on a widget that has no extra-large content).
- Deprecated WidgetKit APIs still in use (Configuration intents pre-AppIntent).
- App Shortcut declared without provided synonyms.

Every finding must include a Verification field — for extensions this
is usually:
- `code` — inspectable in the appex-targets / entitlements / Info.plist
  snapshot.
- `runtime` — requires Instruments (Allocations) on the extension
  process to confirm memory; or "Add to Home Screen" + Console.app to
  observe widget lifecycle logs; or XCUITest invocation via Siri to
  confirm intent perform() under real conditions; or an end-to-end
  push send to confirm NSE content-mutation against a real device.

"Manual review" alone is not sufficient verification for a Critical
finding — Critical memory-budget findings specifically require an
Instruments run on the extension.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to claude.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
