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
- Evidence: file:line citation, StoreKit 2 API reference, or App Store Connect concept
- Confidence: high | medium | low

Cover these challenge categories:

(1) False positives — findings that don't actually apply in context.
Specifically for Apple StoreKit:
- A `.unverified` consumption flagged as Critical is actually inside a
  test target or `#if DEBUG` block — only the production path matters.
- "No Transaction.updates observer" flagged but the project uses
  SwiftUI `.subscriptionStatusTask` / `.currentEntitlementTask` modifiers
  which subscribe to the same updates under the hood — re-read for
  these before flagging.
- "No Restore Purchases button" flagged but the project uses
  `SubscriptionStoreView` / `StoreView` with the default
  `.storeButton(.visible, for: .restorePurchases)` — Apple's stock
  views provide the button for free.
- "StoreKit 1 in use" flagged on a target with iOS 14 minimum
  deployment — StoreKit 2 requires iOS 15+, so legacy code there is
  required, not a finding.
- "Server-side validation missing" flagged on a fully client-side
  consumer app with no server backend at all — there's nothing to
  validate against. Note the project shape before flagging this as
  Critical / High.
- "Promotional offer signed client-side" flagged on code that's
  generating a *test* signature for SKTestSession, not production.

(2) Severity miscalibrations — findings rated too high (the
`.unverified` branch is followed by an immediate `return` / `continue`
rather than entitlement grant; the missing observer is in a
companion-only watch app where iPhone handles all StoreKit; the
"no restore button" is only on the in-app paywall but the App
Settings has a working Restore that Apple Review will accept) or too
low (a Medium "subscription state stale" finding is actually Critical
because the cached entitlement is consulted instead of
`Transaction.currentEntitlements` on every paywall paint — refunded
users keep features forever).

(3) Missing findings — StoreKit issues the review may have missed:
- **Consumables**: consumable IAP doesn't `transaction.finish()` after
  server-side delivery confirmation → queue keeps redelivering
  forever, eventually duplicating the entitlement N times.
- **Subscription offer codes**: project ships subscription offer codes
  via App Store Connect but doesn't handle the
  `AppStore.presentOfferCodeRedeemSheet(in:)` / `.offerCodeRedemption`
  scene action → user with a valid code can't redeem in-app.
- **Apple-managed receipts on macOS**: macOS-only paid app uses
  `AppStore.requestReview()` correctly but never reads receipt → if
  Apple Silicon user buys on Mac App Store, the entitlement check
  fails because the project assumed iOS-style purchase().
- **Visibility into refunds**: project handles `revocationDate` in
  `Transaction.updates` but doesn't surface revocation to the user
  ("Your purchase was refunded; access revoked") → user is confused
  why features disappeared.
- **Family Sharing UI**: product is `isFamilyShareable=true` in App
  Store Connect, but the paywall doesn't mention Family Sharing →
  prospective buyer underestimates value vs competitors who advertise
  family sharing.
- **Transaction.unfinished on launch**: `Transaction.unfinished` not
  drained at app launch → pending Ask-to-Buy approvals from prior
  sessions never get processed, even with `Transaction.updates`
  observer running (updates only delivers *new* transactions).
- **Promo offer eligibility race**: `isEligibleForIntroOffer` checked
  but result stored at app launch and never refreshed → user becomes
  eligible (e.g. subscription expires + cooling period passes) but UI
  still shows them as ineligible.
- **Sandbox vs production detection**: code branches on
  `Bundle.main.appStoreReceiptURL` containing `sandboxReceipt` to
  differentiate environments — this is a StoreKit 1 receipt path
  and doesn't work for StoreKit 2; use `Transaction.environment`
  instead.

(4) Missing compound paths — separate findings in the synthesis that
combine into a worse outcome than any single finding represents:
- "Forgery accepted" chain (`.unverified` consumed + permanent
  entitlement granted on a `UserDefaults` boolean) — already covered,
  but check whether *both* legs are actually present in production
  code paths.
- "Sub state stale" chain (no `Transaction.updates` observer +
  entitlements cached in UserDefaults + no startup re-check via
  `Transaction.currentEntitlements`).
- "Promo offer reject" chain (client-side signing + signing key
  bundled into app + no server flow).
- "Ask-to-Buy black hole" chain (treating `.success(.pending)` as
  failure + no `Transaction.updates` observer + no
  `Transaction.unfinished` drain at launch).

(5) Impractical / incomplete / wrong remediations — e.g.:
- "Move to server-side validation" without specifying that the
  remediation requires a server first (a fully on-device app has
  nothing to validate against).
- "Use SubscriptionStoreView" recommended for an iOS 16 minimum-
  deployment project — `SubscriptionStoreView` is iOS 17+; the
  recommendation needs the deployment-target context.
- "Add Transaction.updates observer" without specifying that it must
  be in a Task that survives the view tree (started from App init or
  a Scene-level Task, not from a view's `.task`).
- "Verify with sandbox" without noting that Sandbox testers must be
  created in App Store Connect first and the device signed in to the
  Sandbox tester via Settings → App Store → Sandbox Account, NOT the
  user's real Apple ID.

(6) Verification steps that don't actually prove the fix works — e.g.
"verify by running the app" when the code path is only reachable
under Ask-to-Buy approval (parent device required); "manual code
review" verification for `.unverified` handling when the actual proof
needs a deliberately-malformed JWS via SKTestSession to confirm the
fix; "check that AppStore.sync() is called" verification when the
real proof requires a second device signed in to the same Apple ID
to confirm cross-device restore.

Be specific. Every challenge must cite the finding ID and reference
the StoreKit 2 API / file path / line number where applicable.

Do not read or reference any other review file beyond synthesis.md and
the tooling-raw/ directory.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type
  "no_challenges" and Confidence "high" stating that you attempted but
  found nothing worth surfacing.
- No emojis.
