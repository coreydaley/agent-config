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
- Evidence: file:line citation, entitlement key, Info.plist key, or
  grep match in tooling-raw/
- Confidence: high | medium | low

Cover these challenge categories:

(1) False positives — findings that don't actually apply in context.
Specifically for Apple deep-links / continuity:
- A `?mode=developer` Associated Domains suffix is only present in the
  Debug-variant entitlement file, never in Release — re-read
  associated-domains.txt and split by entitlement filename before
  flagging Critical.
- A custom URL scheme that looks like it overlaps with `facebook://`
  is actually a Facebook SDK callback handler installed by the SDK
  itself — the project doesn't claim the scheme, the SDK does.
- A Spotlight indexing call site flagged for missing
  `isEligibleForPublicIndexing = false` is actually wrapped in a
  guard that only indexes already-public content (e.g. a public
  recipe library), not user-private data.
- An `application(_:continue:)` handler that looks under-validated
  is actually called only via a tightly-scoped NSUserActivity type
  declared in Info.plist NSUserActivityTypes — the surface area is
  smaller than it appears.
- A wildcard `paths: ["*"]` in AASA is intentional for a project
  where the entire site is in-app navigable (e.g. a wiki / reader
  app); flag as a hygiene note rather than a Critical.

(2) Severity miscalibrations — findings rated too high (the URL scheme
is only acted on after the user re-authenticates in a follow-up modal;
the entitlement domain mismatch is for a staging domain not yet
public; the AASA wildcard is documented and intentional) or too low
(the URL scheme handler calls evaluateJavaScript on a user-controlled
URL parameter — that's RCE-class, not Medium; the Associated Domains
entitlement is missing the production hostname entirely — that breaks
every marketing link, not a hygiene issue).

(3) Missing findings — Apple-deep-link issues both reviewers may have
missed:
- Universal Link cold-launch lost: handler installed in `viewDidLoad`
  of root VC instead of `scene(_:continueUserActivity:)` at the scene
  delegate level — re-read continue-useractivity.txt for the call
  site's file and class context.
- SwiftUI scene-lifecycle mismatch: `.onContinueUserActivity` placed
  inside a View that isn't part of the initial scene → activity fires
  before the View is in the hierarchy, link lost.
- App Clip without `appclips:` service in Associated Domains
  entitlement: App Clip target present in the project (look for
  `*.appclip` or `.appclips` references) but the parent app
  entitlement doesn't declare `appclips:<domain>` → Advanced App Clip
  Experience URLs won't route.
- SiriKit / Communication notification donation gap: app declares
  Communication capability + sends messages but doesn't donate
  INSendMessageIntent → notifications render without avatar / per-
  person UI.
- Spotlight cross-device sync gap: `CSSearchableIndex` items indexed
  but no CloudKit-backed reindex on a different device → user signs
  in on a new device and Spotlight is empty until a manual rebuild.
- Cross-platform deep-link split: Universal Link routing only handled
  on iOS; macOS / Mac Catalyst target also receives the activity but
  the handler is `#if os(iOS)`'d → Mac users can't deep-link.
- watchOS Handoff drop: NSUserActivity created on iPhone with
  `isEligibleForHandoff = true` but the paired watch app's
  WCSession-side handler doesn't activate the matching scene.

(4) Missing compound paths — separate findings in the synthesis that
combine into a worse outcome than any single finding represents:
- "RCE via deep link" chain (custom URL scheme handler + WKWebView
  with JS bridge + handler passes URL components to evaluateJavaScript).
- "Universal Links silently broken on production" chain (Associated
  Domains entitlement domain mismatch + AASA missing/redirected at the
  production domain + stale TEAMID in `appIDs`).
- "AutoFill broken" chain (`webcredentials:` in entitlement + AASA
  `webcredentials.apps` empty or wrong TEAMID + login flow doesn't
  use `.textContentType(.password)`).
- "Spotlight privacy leak" chain (CSSearchableIndex on private
  content + `isEligibleForPublicIndexing` defaulted true + no
  delete-on-signout).
- "Cold-launch deep link lost" chain (handler in viewDidLoad +
  scene_continueUserActivity_ not implemented + first cold-launch
  link is dropped).
- "?mode=developer MITM" chain (entitlement suffix + Release config +
  hostile-Wi-Fi attacker serving fake AASA).

(5) Impractical / incomplete / wrong remediations — e.g.:
- "Switch from custom URL scheme to Universal Links" without
  acknowledging that the project needs to actually serve an AASA at
  the destination domain — the remediation isn't just an entitlement
  change.
- "Add `isEligibleForPublicIndexing = false`" without specifying which
  NSUserActivity / CSSearchableItem call sites — the change has to be
  applied at every indexing call, not just one.
- "Validate the URL before acting" without specifying the validation
  shape (allowlist of paths, query-param schema, identifier format) —
  "validate" without a definition is uncheckable.
- "Move the handler from AppDelegate to SceneDelegate" without
  noting that for SwiftUI lifecycle apps, the handler is
  `.onContinueUserActivity` on the root scene's `WindowGroup`, not a
  SceneDelegate method — the SwiftUI vs UIKit lifecycle distinction
  matters.

(6) Verification steps that don't actually prove the fix works — e.g.
"verify by inspecting the entitlement file" for a finding whose effect
only shows up after `swcutil dl -d <domain>` on the device + an
on-device tap from Notes; "verify by reading the AASA" without
actually curling the production URL to confirm it's reachable and
has the right Content-Type; "manual code review" for a Universal
Link routing finding whose effect is "first cold-launch link is
dropped" (only reproducible by a cold-launch tap-from-Notes test).

Be specific. Every challenge must cite the finding ID and reference
the entitlement key / Info.plist key / file path / grep match where
applicable.

Do not read or reference any other review file beyond synthesis.md and
the tooling-raw/ directory.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type
  "no_challenges" and Confidence "high" stating that you attempted but
  found nothing worth surfacing.
- No emojis.
