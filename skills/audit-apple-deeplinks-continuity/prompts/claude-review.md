You are an INDEPENDENT reviewer. You did NOT write the code or artifact
under review — approach it with fresh eyes and review it on its merits alone.
(The Claude session that invoked this audit may well have authored what you
are now reviewing; that is exactly why this review is delegated to you rather
than done in that session, which would share its own blind spots.)

Write your findings to claude.md (ID prefix A) per the specification below.

Perform a thorough Apple platform deep-links & continuity review of the
scope at the project root you've been pointed at. Tooling has already
been run; raw output is in the audit dir's tooling-raw/ subdirectory.
Read those files first:

- associated-domains.txt — `com.apple.developer.associated-domains`
  entries per entitlement file. **Cross-referencing this with
  aasa-references.txt is the single highest-yield activity for this
  audit.**
- url-types.txt — CFBundleURLTypes per Info.plist (declared incoming
  custom URL schemes)
- queries-schemes.txt — LSApplicationQueriesSchemes per Info.plist
  (declared outgoing schemes the app probes)
- user-activity-types.txt — NSUserActivityTypes per Info.plist
- continue-useractivity.txt — grep of application(_:continue:) /
  scene(_:continueUserActivity:) / .onContinueUserActivity, plus
  NSUserActivity construction sites
- url-scheme-handlers.txt — grep of application(_:open:) /
  scene(_:openURLContexts:) / .onOpenURL / openURL / canOpenURL
- spotlight-refs.txt — grep of CSSearchableIndex / CSSearchableItem
  / indexSearchableItems / deleteSearchableItems / domainIdentifier
- app-intents-refs.txt — grep of AppIntent / AppShortcut /
  IndexedEntity / EntityQuery / donate / IntentDonationManager
- aasa-references.txt — grep of `apple-app-site-association` /
  `.well-known/apple-app-site-association` / `applinks:` /
  `webcredentials:` / `activitycontinuation:` / `appclips:`

Write all findings to claude.md (in the audit dir you were granted write
access to) using this exact table format:

| ID | Severity | Anchor | Category | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix A (e.g. A001, A002). Every finding MUST include an
Anchor (e.g. Entitlement:com.apple.developer.associated-domains,
Apple:NSUserActivity, Apple:CSSearchableIndex, Plist:CFBundleURLTypes)
and a Category from: AssociatedDomains, AASAFile, UniversalLinkRouting,
CustomURLScheme, NSUserActivity, Handoff, SpotlightSearch, CoreSpotlight,
AppIntentsHandoff, DeepLinkValidation, AppClipBridging, WebCredentials.
Platform: iOS, iPadOS, macOS, MacCatalyst, watchOS, tvOS, visionOS, or
Multi.

DO NOT review runtime URL-scheme handler exploit chains (RCE via
WKWebView.evaluateJavaScript, JS bridge poisoning) in exploit-chain
depth — that belongs in audit-apple-security. DO flag the discipline
issue here (handler validates input, doesn't act on state-changing
paths without re-auth, doesn't pass URL components to evaluateJavaScript)
and let the security audit own the exploit-chain proof. DO NOT review
App Intent donation lifecycle inside Widgets, Live Activities, or App
Shortcuts extensions — that belongs in audit-apple-extensions; this
audit covers the donation call site at the host app and the Spotlight-
indexing side.

Cover these 12 categories (skip if not applicable):

(1) AssociatedDomains — `com.apple.developer.associated-domains`
entitlement lists each domain with appropriate service (`applinks:`,
`webcredentials:`, `activitycontinuation:`, `appclips:`); flag
`?mode=developer` suffix surviving into Release builds (allows
on-device override of the served AASA — useful in dev, dangerous in
Release); domains in the entitlement match the actual production
hostnames the marketing team links to; entitlement consistent across
Debug / Release entitlement files; bundle id in TEAMID.bundleid format
matches the actual app id.

(2) AASAFile — references to `apple-app-site-association` in the repo
indicate the serving strategy. Flag: AASA served from anywhere other
than `https://<domain>/.well-known/apple-app-site-association`; served
with a redirect (Apple's swcutil rejects redirects — Universal Links
silently fail); served with the wrong `Content-Type` (must be
application/json, NOT text/html); `paths` array using the wildcard `*`
to claim every URL on the domain (in-app navigation now diverges from
web behavior for every path); `appIDs` array containing stale
TEAMID.bundleid from a prior team / prior bundle id; deprecated `apps`
top-level array (pre-iOS 9 format) present alongside modern `details`.

(3) UniversalLinkRouting — Universal Links work on iOS / iPadOS /
macOS / Mac Catalyst / visionOS. `application(_:continue:)` (UIKit) /
`scene(_:continue:)` (UIKit scene; iOS-distinctive — depth lives in
audit-apple-ios) / `.onContinueUserActivity(
NSUserActivityTypeBrowsingWeb)` (SwiftUI, cross-platform);
`activity.webpageURL` checked non-nil before use; unknown-path
routing degrades gracefully (opens a default landing screen, or
opens the URL in SFSafariViewController as a fallback) rather than
crashing; cold-launch deep link is handled (handler installed before
first scene activation — not in a child VC's viewDidLoad, where the
activity has already fired by the time the VC loads). On macOS the
equivalent entry is `NSApplicationDelegate` `application(_:continue:)`
plus `NSAppleEventManager` URL handlers — those macOS-distinctive
depths live in audit-apple-macos. Flag handlers that assume the URL
is always non-nil, or that crash on a missing path component.

(4) CustomURLScheme — LSApplicationQueriesSchemes (outgoing) and
CFBundleURLTypes (incoming) declared. Incoming scheme handler
validates `host`, `path`, and query parameters before acting;
state-changing paths (logout, purchase, account deletion, subscription
cancel) require re-authentication or explicit user confirmation in
the handler — flag handlers that act on tap alone. Flag schemes that
overlap with system schemes or popular-app schemes (`facebook://`,
`whatsapp://`, `slack://`, `tel://`, `sms://`, `mailto://`,
`itms-apps://`) — both an App Store rejection risk and a scheme-hijack
risk. OAuth callback URL handlers must validate the `state` parameter
against the value sent in the request to prevent CSRF.

(5) NSUserActivity — activity type declared in Info.plist
NSUserActivityTypes (reverse-DNS string); `becomeCurrent()` called
when the scene becomes active and `resignCurrent()` on background
(or activity ends); `persistentIdentifier` set so the system can
match continuations; `isEligibleForHandoff`, `isEligibleForSearch`,
`isEligibleForPrediction`, `isEligibleForPublicIndexing` set
explicitly — the defaults are rarely what the developer wants for
privacy-sensitive activities.

(6) Handoff — `webpageURL` provided as the fallback URL for users
without the app installed on the destination device (so Handoff opens
Safari); `userInfo` payload size stays under the ~3MB Handoff limit
(activities exceeding this are silently dropped); activity `title`
set for the system Handoff banner; activity continues across
paired-device transitions (Mac ↔ iPhone, iPhone ↔ iPad); contentAttributes
set if the activity should appear in Spotlight.

(7) SpotlightSearch — `CSSearchableIndex.default().indexSearchableItems(_:)`
paired with `deleteSearchableItems(withDomainIdentifiers:)` (or
`deleteSearchableItems(withIdentifiers:)`) for cleanup;
CSSearchableItemAttributeSet populated with title, contentDescription,
thumbnailURL or thumbnailData, and keywords; `domainIdentifier` used
consistently across an item's lifecycle so grouped delete works;
reindex on data changes (not just on first launch); the
`kCSSearchableItemActivityIdentifier` key is handled in
application(_:continue:) when a Spotlight tap launches the app.

(8) CoreSpotlight — privacy-sensitive content (messages, health
records, financial entries, photos, notes content) indexed without
`isEligibleForPublicIndexing = false` is a leak risk — the items can
be syndicated to third-party search surfaces; unique index identifier
per item (don't reuse identifiers across entities); delete on entity
removal — flag indexing call sites that have no corresponding
delete-on-remove paths; CSPersistentTokenURL or stable identifiers for
cross-process item references.

(9) AppIntentsHandoff — App Intent donation via `donate()` on
IntentReference / IntentDonationManager so "Recently used" surfaces
work; `AppShortcutsProvider` declared with fixed App Shortcuts;
`EntityQuery` / `EnumerableEntityQuery` correct for Spotlight
`IndexedEntity` integration; donation called on success (not on
attempt — donating failed actions teaches Siri the wrong thing).

(10) DeepLinkValidation — Every deep-link input (URL parameters,
NSUserActivity.userInfo, scheme query parameters, Spotlight item
userInfo) treated as untrusted; URL parameters NOT concatenated into
NSPredicate / SQL / shell-like commands / `WKWebView.evaluateJavaScript`
without escaping; identifier lookups use UUID or opaque IDs rather
than database row IDs (attacker enumeration); state-changing handlers
require user confirmation, not just a tap.

(11) AppClipBridging — iOS-only. Associated Domain `appclips:`
service declared if the project uses App Clips; App Clip → full
app handoff via `NSUserActivity` with the same persistentIdentifier;
"Get Full App" affordance in the Clip per HIG; Advanced App Clip
Experiences URLs declared in App Store Connect (off-device — flag
in the report as a checklist item rather than a code finding). Skip
this category on macOS / watchOS / visionOS / tvOS projects.

(12) WebCredentials — Associated Domain `webcredentials:` service
paired with AASA `webcredentials.apps` array containing the correct
`TEAMID.bundleid`; ASAuthorizationPasswordProvider flow correctly
handles AutoFill suggestion; password input fields use SecureField
and `.textContentType(.password / .newPassword / .oneTimeCode)` so
the system AutoFill UI knows what to offer.

Rate severity on evidence: impact (what ships broken), reachability
(does Release see it), blast radius (every marketing-link tap vs only
users on hostile Wi-Fi vs only App Clip users), compensating controls
(server-side redirect, in-handler re-auth modal, in-app validation).

Critical anchors:
- Deep-link handler passes user-controlled URL components to
  WKWebView.evaluateJavaScript or shell-like context (RCE via
  tweeted link — flag here; route exploit-chain proof to
  audit-apple-security)
- URL scheme triggers state change (logout, purchase, account
  deletion) without re-auth or confirmation (one-tap account
  compromise)
- AASA missing on the production domain that the entitlement
  declares — every marketing Universal Link silently falls back to
  Safari
- Associated Domains entitlement domain doesn't match production
  hostname (e.g. `applinks:app.foo.com` while marketing links go to
  `foo.com`) — same silent fallback

High anchors:
- Custom URL scheme overlaps with a popular app or system scheme
  (`facebook://`, `whatsapp://`, `slack://`) — App Store rejection
  + scheme-hijack risk
- AASA `paths` wildcard `*` claiming every URL on the domain — in-app
  navigation now diverges from web for every path
- `?mode=developer` suffix in Associated Domains entitlement
  surviving into Release — attacker on shared Wi-Fi can serve an
  attacker-controlled AASA
- Spotlight indexing of authenticated / private content without
  `isEligibleForPublicIndexing = false` — privacy leak
- `webcredentials:` in entitlement but AASA `webcredentials.apps`
  empty or wrong `TEAMID` → AutoFill silently broken

Every finding must include a Verification field. For deep-links this
is almost always runtime — `swcutil dl -d <domain>` on a Developer-mode
iOS device, `curl -I https://<domain>/.well-known/apple-app-site-association`
for AASA reachability, `xcrun simctl openurl booted <url>` for scheme
testing, tap-a-link-in-Notes for a real Universal Link, or Settings
→ Siri & Search for Spotlight. "Manual review" alone is not
sufficient verification for a Critical finding.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to claude.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
