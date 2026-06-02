You are an INDEPENDENT reviewer. You did NOT write the code or artifact
under review — approach it with fresh eyes and review it on its merits alone.
(The Claude session that invoked this audit may well have authored what you
are now reviewing; that is exactly why this review is delegated to you rather
than done in that session, which would share its own blind spots.)

Write your findings to claude.md (ID prefix A) per the specification below.

Perform a thorough Apple StoreKit 2 implementation review of the scope
at the project root you've been pointed at. Tooling has already been
run; raw output is in the audit dir's tooling-raw/ subdirectory. Read
those files first:

- storekit-configs.txt — every *.storekit configuration file found
- storekit2-usage.txt — call sites for the StoreKit 2 API surface
  (Transaction.currentEntitlements, Transaction.updates, Transaction.all,
  Product.products, Product.SubscriptionInfo, .purchase()) — **reading
  these line-by-line is the highest-yield activity for this audit**
- storekit1-usage.txt — call sites for the legacy StoreKit 1 surface
  (SKPaymentQueue, SKProduct, SKReceiptRefreshRequest, etc.)
- verificationresult-usage.txt — every site where VerificationResult,
  .verified, .unverified, .payloadValue, jwsRepresentation appear
- transaction-updates.txt — Transaction.updates observer sites
- appstore-sync-usage.txt — AppStore.sync() call sites
- paywall-views.txt — paths of likely paywall view files

Write all findings to claude.md (in the audit dir you were granted write
access to) using this exact table format:

| ID | Severity | Anchor | Category | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix A (e.g. A001, A002). Every finding MUST include an
Anchor (e.g. StoreKit2:Transaction, StoreKit2:VerificationResult,
StoreKit2:Product.SubscriptionInfo.RenewalState, Apple:AppStore.sync,
Apple:Guideline_3.1.1, Apple:Guideline_3.1.2,
Apple:AppStoreServerAPI) and a Category from: StoreKit2Transactions,
Verification, Entitlements, RestoreFlow, AskToBuy, PromoOffers,
RefundHandling, SubscriptionStateObserver, ServerSideValidation,
StoreKitTesting, PaywallUX, FamilySharing. Platform: iOS, iPadOS,
macOS, MacCatalyst, watchOS, tvOS, visionOS, or Multi.

DO NOT review IAP business-rule compliance (paywall metadata wording,
restore-button label text, subscription terms disclosure copy) — that
belongs in audit-apple-app-store-review. DO NOT review JWS signature
crypto or Keychain receipt storage at the runtime-security level —
that belongs in audit-apple-security. This audit covers the broader
implementation-correctness surface on top of both.

Cover these 12 categories (skip if not applicable):

(1) StoreKit2Transactions — Use of StoreKit 2 (Product, Transaction,
VerificationResult) for any new code; flag StoreKit 1 (SKPaymentQueue,
SKProduct, SKReceiptRefreshRequest) as deprecated for projects targeting
iOS 15+; `Transaction.updates` observer started at app launch and never
cancelled (long-lived async sequence — should be in a top-level Task
that survives view-tree churn, NOT in an arbitrary view's `.task`);
`transaction.finish()` called for every transaction (consumables
especially — unfinished consumable transactions get redelivered by the
queue indefinitely).

(2) Verification — Every Transaction or RenewalInfo value wrapped in
`VerificationResult` — discard `.unverified` results, only act on
`.verified`; flag any path that consumes the `.unverified` value via
`.payloadValue` or pattern-matches `case .unverified(let t, _):` and
then proceeds to grant entitlements. The single most dangerous pattern:
`for await result in Transaction.updates { let transaction = try?
result.payloadValue; grantEntitlement(transaction) }` — `.payloadValue`
returns the unwrapped Transaction regardless of verification, so a
forged JWS is treated as a paid purchase.

(3) Entitlements — `Transaction.currentEntitlements` consumed at app
launch to bootstrap UI (`for await result in Transaction.currentEntitlements
{ ... }`). Flag reliance on the `purchase()` return value alone — that
misses cross-device restore (user buys on iPhone, opens on iPad fresh
install, currentEntitlements has the transaction but the app never
reads it). Subscription group state observed via
`Product.SubscriptionInfo.RenewalState` rather than inferring from
expirationDate alone.

(4) RestoreFlow — `AppStore.sync()` available as a "Restore Purchases"
affordance reachable from outside the paywall (App Store Review
Guideline 3.1.1 requires this for paid-features apps). Flag manual
restore that re-prompts password (not needed in StoreKit 2 — sync()
handles auth). Flag the Restore button being absent entirely, or
buried deep in a Settings submenu where users won't find it, or only
shown after `purchase()` failure.

(5) AskToBuy — Pending purchases (`Transaction.unfinished`,
`pendingTransactions`) handled — Ask-to-Buy can return a parent-approved
transaction days later. Flag UI that locks up waiting for `purchase()`
to return; flag any path that treats `Product.PurchaseResult.success(.pending)`
or the pending verification variant as failure rather than as a deferred
state. The `Transaction.updates` observer is the only path that
delivers an Ask-to-Buy approval after the app has been restarted — if
the observer is missing, the approval is silently dropped.

(6) PromoOffers — `Product.SubscriptionOffer` (introductory and
promotional offers): eligibility checked via
`SubscriptionInfo.isEligibleForIntroOffer` before showing intro
pricing; signed promotional offers correctly via JWS, with the signing
private key kept server-side (env var, secrets manager, Keychain on
the signing server). Flag any path that signs offers in-app — the key
is then in the App Store binary and trivially extractable.

(7) RefundHandling — `Transaction.revocationDate` and
`Transaction.revocationReason` observed via `Transaction.updates`;
entitlements re-evaluated when revocation happens; UI gracefully
degrades rather than crashing mid-action when the entitlement
disappears.

(8) SubscriptionStateObserver — `Product.SubscriptionInfo.RenewalState`
observation (`subscribed`, `expired`, `inBillingRetryPeriod`,
`inGracePeriod`, `revoked`); `expirationDate`,
`gracePeriodExpirationDate`, `autoRenewStatus` surfaced to the user
("Your subscription is in grace period — update payment method by
2026-06-12"). Flag silent expiration with no in-app indication.

(9) ServerSideValidation — Recommended for non-consumables and
subscriptions: server validates JWS via Apple's public keys
(`Transaction.jwsRepresentation` sent to server; server verifies via
`apple/app-store-server-library` or equivalent). App Store Server API
used for transaction history (`/inApps/v1/history/{transactionId}`) and
refund webhooks (`REFUND` notification). Server-side state of record
(not just client trust). Flag client-only trust where the app has a
server backend — a tampered client can fake purchase confirmations.

(10) StoreKitTesting — `.storekit` configuration file present in
Xcode; test plan attaching `.storekit` config; XCTest using
`SKTestSession` for IAP flows (purchase, refund, askToBuy,
clearTransactions); `SKTestSession.clearTransactions()` /
`Transaction.deleteCurrentEntitlement()` in test teardown. Flag projects
shipping IAP with zero automated tests of the purchase flow.

(11) PaywallUX — Paywall conforms to App Store Review Guideline 3.1.2:
must show subscription details (duration, price, renewal terms link,
privacy link), restore-purchases button present, cancel flow that
doesn't trap user, loading states for slow networks. Flag the
classic "paywall on launch with no X / Continue with Free affordance"
trap. If using SwiftUI `SubscriptionStoreView` / `StoreView` /
`ProductView` (iOS 17+), check they're configured with the right
product / subscription group identifiers and `.storeButton` modifiers
(restore / redeem / policies).

(12) FamilySharing — `Transaction.isUpgraded`,
`Transaction.ownershipType` (`.purchased` vs `.familyShared`),
`Product.isFamilyShareable` for IAPs that support it; restoration flow
re-checks `ownershipType` so family members get the entitlement even
though they didn't originate the purchase. Flag any path that filters
out `.familyShared` transactions and only honors `.purchased` ones.

Rate severity on evidence:
- impact (forged purchases accepted? subscriptions silently lapse?
  every promo offer purchase rejected? App Review rejection? UI traps
  the user?)
- reachability (paywall views are on every fresh-install path; an
  obscure debug-only restore button isn't)
- blast radius (every user, every family-shared user, every refund
  recipient, every Ask-to-Buy minor, every promo recipient)
- compensating controls (does the server already revalidate JWS? Does
  the app re-bootstrap from currentEntitlements on cold launch? Is
  there a working out-of-band restore path?)

Critical anchors:
- Consuming `.unverified` Transaction values via `.payloadValue` or a
  case match (forged purchases accepted as paid)
- No `Transaction.updates` observer started at app launch (subscription
  renewals + Ask-to-Buy approvals never delivered; subs silently lapse)
- No "Restore Purchases" affordance reachable from outside the paywall
  (App Store Review 3.1.1 rejection)
- Subscription state cached forever in `UserDefaults` without re-checking
  against `Transaction.currentEntitlements` (refunds and cancellations
  honored only on next purchase, sometimes never)
- Paywall traps the user on launch with no "X" / "Continue with Free"
  affordance (App Review rejection guaranteed; review rating tanks)

High anchors:
- Bootstrap UI relies only on `purchase()` return value (cross-device
  restore misses entitlements; new device install shows "purchase
  again" to paying users)
- Promotional offer signature generated client-side (every promo offer
  purchase rejected by Apple AND the signing key is extractable)
- No `.storekit` configuration → no automated testing of IAP
- Transaction not `finish()`ed (queue redelivers indefinitely)
- JWS not server-validated for an app that has a server backend

Every finding must include a Verification field — for StoreKit this
is usually a sandbox purchase or `.storekit` test session (e.g.
"Configure SKTestSession with the auto-renewable subscription product;
call buyProduct then simulate a refund; assert revocation handler
fired and entitlement was revoked"), an App Store Server API call, or
a `Transaction.all` introspection in lldb. "Manual review" alone is
not sufficient verification for a Critical finding.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to claude.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
