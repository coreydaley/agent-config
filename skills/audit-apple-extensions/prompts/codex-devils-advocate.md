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
- Evidence: file:line citation, NSExtensionPointIdentifier value, App Group identifier, or specific entitlement key
- Confidence: high | medium | low

Cover these challenge categories:

(1) False positives — findings that don't actually apply in context.
Specifically for Apple extensions:
- An "NSE memory budget" finding flagged Critical when the extension
  isn't actually doing the mutation it claims to — e.g. the NSE only
  decorates the notification with a localized title, no attachment
  download, no large-payload buffering. Memory budget concern only
  becomes Critical with evidence of allocation pressure (Data buffers,
  Core Data faulting, image decoding); without that, drop to Medium.
- A "Widget timeline blocks main thread" finding when the body of
  `getTimeline()` is fully async with no synchronous Core Data /
  Keychain fetch — re-read the function for `await` discipline before
  flagging.
- An "App Intent perform() too slow" finding flagged on an intent
  that is `static let openAppWhenRun = true` — when the intent opens
  the app, the perform() runs in the app process (full memory budget)
  not the extension; the 30s extension wallclock budget doesn't apply.
- An "Entitlement drift" finding when the entitlement in question is
  one that App Groups don't propagate (e.g. `keychain-access-groups`
  requires the same access group string on BOTH sides; if both have
  the same group it's not drift, even if the entitlement keys read
  asymmetrically).
- A "ShareExtension activation rule too broad" finding when the rule
  is `NSExtensionActivationSupportsText` only (text-only rules are
  always benign; broad-content rules with `MaxCount=1000` are the
  Critical pattern).
- An "App Group declared but unused" finding when the consumer is in
  a target the audit didn't scan (CI / preview-only target / test
  target). Re-grep the full project tree for `suiteName:` /
  `containerURL` references.

(2) Severity miscalibrations — findings rated too high (the misconfig
exists only in a Debug build of the extension; the extension target
isn't shipped in the Release archive — check the `.pbxproj` for
`SKIP_INSTALL`; the extension is only used by an internal-tools
flavor) or too low (the NSE silently reverting push is a *Critical*
ship-affecting bug, not High, because every affected push for every
user is wrong; an App Intent that opens to the wrong screen is a
*Critical* trust break with Siri, not Medium).

(3) Missing findings — Apple-extensions issues both reviewers may
have missed:
- **NSE attachment download retry storms**: NSE downloads an
  attachment that fails (network 5xx); without explicit backoff, the
  next push for the same payload retries; APNs delivers up to 10
  pushes per identifier; each one re-attempts the download → 24MB cap
  blown on memory pressure from the failed retries.
- **WidgetKit `relevance` set to constant value**: every entry has
  the same TimelineEntryRelevance → Smart Stack ordering is random;
  widget never surfaces to the user even when relevant.
- **Live Activity `activityState` desync**: server pushes update with
  a state value that the client's `ActivityAttributes.ContentState`
  decoder can't handle (Codable mismatch) → activity silently freezes
  on the old state; no error surfaced to user.
- **App Intent EntityQuery returning paginated results that break
  type-ahead**: Spotlight expects EntityStringQuery to return ALL
  matches in one call (pagination on entity query is not supported);
  reviewers may have missed this if the query looks "correct" by
  general Swift standards.
- **Share Extension main-thread blocking on inputItem.loadItem**:
  `loadItem(forTypeIdentifier:)` returns a completion handler on an
  arbitrary queue; if the extension calls it synchronously and waits
  on a semaphore, it deadlocks for ~5s before being killed.
- **AutoFill extension `serviceIdentifiers` mismatch**: domain
  `example.com` declared in service identifiers but the credential
  is saved with `https://login.example.com` → AutoFill never offers
  the credential because the host comparison is strict.
- **FileProvider working-set memory growth**: working set is unbounded
  by default; without explicit eviction, the provider's memory grows
  with every enumerated item until jetsam.
- **watchOS complication migration**: project still using ClockKit
  CLKComplicationDataSource alongside WidgetKit on watchOS 10+;
  ClockKit was deprecated for new complications; both reviewers may
  have missed this if the project only updated the widget side.
- **Safari Web Extension manifest_version**: manifest still declares
  `manifest_version: 2`; Safari 17+ requires MV3.

(4) Missing compound paths — separate findings in the synthesis that
combine into a worse outcome than any single finding represents:
- **"Silent push fail" chain** (NSE memory near cap + payload requires
  content mutation + serviceExtensionTimeWillExpire doesn't call
  contentHandler(bestAttemptContent)) — already covered, but check
  whether the expirationHandler actually preserves the user-visible
  fallback path.
- **"Spotlight crash" chain** (App Intent perform() doing main-thread
  Core Data + EntityQuery returning >100 entities + perform() declared
  `throws` but error path is `fatalError`).
- **"Drained battery" chain** (Widget timeline refresh <5min +
  getTimeline doing network or Core Data + no relevance scoring).
- **"Capability drift" chain** (Push enabled on host but not extension
  + extension target referenced in podspec / SPM target conditions
  that bypass the Xcode capability check).
- **"Activation overreach"** (Share Extension `MaxCount=1000` rule +
  extension can only meaningfully handle one host + synchronous
  inputItem processing on main thread).

(5) Impractical / incomplete / wrong remediations — e.g.:
- "Reduce NSE memory" without specifying what to stream rather than
  buffer (a generic remediation that doesn't name the URL / data
  source is impractical for a developer to action).
- "Add expiration handler" without specifying that the handler MUST
  call contentHandler(bestAttemptContent) — an empty
  serviceExtensionTimeWillExpire is worse than no handler because the
  push is just lost.
- "Fix App Intent perform() latency" without specifying off-main-thread
  data fetch — moving the Core Data work to a background context is
  the actual fix, not a general "optimize".
- "Match entitlements between host and extension" without specifying
  that the entitlements file MUST be referenced from the target's
  build settings (`CODE_SIGN_ENTITLEMENTS`); adding the file to the
  project isn't enough.
- "Switch to AppIntentTimelineProvider" without naming the migration
  path from TimelineProvider — the Intent-driven version has a
  different lifecycle that the developer needs to understand before
  switching.

(6) Verification steps that don't actually prove the fix works — e.g.:
- "Manual code review" for an NSE memory finding — only Instruments
  (Allocations) on the running extension process proves the cap fix.
- "Build and run in Xcode" for a widget timeline finding — Xcode's
  widget preview does NOT enforce the 30MB cap or the getTimeline
  latency budget; only "Add to Home Screen" + Console.app does.
- "Test in Simulator" for an App Intent — Simulator Siri behavior is
  notoriously divergent from device; only a real device with Siri
  enabled proves the perform() time budget.
- "Send a test push" for an NSE finding without specifying that the
  push payload must include `mutable-content: 1` AND a representative
  attachment / loc-key payload (the trivial test push won't trigger
  the memory pressure).
- "Verify the entitlements file" for a capability-drift finding
  without running `codesign --display --entitlements -` against the
  built `.appex` — the file on disk and the signed bundle's
  entitlements can diverge.

Be specific. Every challenge must cite the finding ID and reference
the file path / NSExtension key / extension target name where
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
