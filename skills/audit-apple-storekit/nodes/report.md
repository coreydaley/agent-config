# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` with StoreKit-specific tier mapping (**Immediate Action** above P0 for Critical findings — these are revenue-impacting bugs or App-Review-rejection blockers).

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`, `codex_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Apple-StoreKit sprint mapping override

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | **Immediate Action — fix before next App Review submission** |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

"Immediate Action" here means: do not submit a build to App Review with this finding outstanding, and (for revenue-impacting findings like `.unverified` consumption or missing `Transaction.updates` observer) do not let the current production build sit live — these bleed money or accept forged purchases every day they're in users' hands. Common Critical examples: consuming `.unverified` transactions, no `Transaction.updates` observer, no Restore Purchases button, paywall traps the user on launch.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Category** — one of the 12 StoreKit categories
- **Location** — `path/to/file:line` (e.g. `StoreManager.swift:42`, `PaywallView.swift:84`), never just "the paywall"
- **Anchor** — required (`StoreKit2:Transaction`, `StoreKit2:VerificationResult`, `Apple:AppStore.sync`, `Apple:Guideline_3.1.2`, etc.)
- **Platform** — `iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`, `visionOS`, or `Multi`
- **Issue** — clear description
- **Remediation** — concrete, specific (e.g. `In StoreManager.handle(_ result:) at line 42, replace the .unverified case to return early rather than fall through to grantEntitlement(transaction); add a logger.warning() and surface to MetricKit so unverified deliveries are observable in production.`)
- **Verification** — for StoreKit this is usually a sandbox or .storekit test: `Run the IAP flow against a .storekit test session with the SubscriptionRenewableProduct configured; assert grantEntitlement is not called for any .unverified result`; for restore-flow: `Install the app on a second device signed in to the same Apple ID; verify Transaction.currentEntitlements returns the prior purchase without prompting purchase()`; for promo offers: `Use App Store Server API to generate a signed JWS server-side and pass it to Product.PurchaseOption.promotionalOffer; verify purchase() succeeds`.

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — apple-storekit — <scope>, <date>`
- Task description: scope covered, 12 categories reviewed, tooling that ran, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Apple StoreKit Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, tooling summary, total findings by severity, top
3 issues, reminder of audit's inherent limitations — StoreKit findings
often require sandbox purchase / .storekit test session / App Store
Server API to confirm; the audit catches the misuse pattern but only an
actual sandbox transaction confirms the fix.>

<If Critical findings exist:>
> ⚠️ **Critical findings present.** Apple-StoreKit Critical = revenue-
> impacting bug live in production OR App Review rejection on next
> submission. Do not submit a new build, and audit current production
> for the same defect against existing-user receipts. See section below.

## Audit Summary

| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Total | N |

| Category | Count |
|---|---|
<non-zero categories only>

Intermediate audit artifacts:
- $AUDIT_DIR/tooling-raw/ (storekit-configs, storekit1/2-usage, transaction-updates, verificationresult-usage, appstore-sync-usage, paywall-views)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/codex.md           <or "MISSING — single-agent run" if codex_status=failed>
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### Immediate Action — fix before next App Review submission

<one block per Critical finding>

**Task: S### — <Category> — <Title>**
- Location: `path/to/file:line`
- Anchor: <anchor>
- Platform: <platform>
- Verification: <code | runtime>
- Issue: <description>
- Remediation: <specific fix>
- Verification step: <sandbox purchase / .storekit test session / App Store Server API call>
- Operational note: <e.g. "revenue-leaking bug — every existing install with this code path can be exploited until a forced update", "App Review rejection guaranteed">

### P0 — Must Ship

<one block per High finding, same format>

### P1 — Ship If Capacity Allows

<one block per Medium finding>

### Deferred

<one-line per Low finding>

## Compound Findings

<reproduce from synthesis.md if any>

## Definition of Done

- [ ] All Immediate Action and P0 tasks completed and verified
- [ ] Each task's verification step executed (sandbox or .storekit session, NOT "build succeeds")
- [ ] No new Critical/High findings introduced by the remediations
- [ ] If any task involved `VerificationResult` handling: re-tested with a deliberately-malformed JWS via SKTestSession to confirm `.unverified` path no longer grants entitlement
- [ ] If any task involved `Transaction.updates`: verified the observer is started before any UI and survives a backgrounded-then-foregrounded app, AND that `transaction.finish()` is called for every delivered transaction
- [ ] If any task involved AppStore.sync / restore flow: tested on a second device signed in to the same Apple ID and verified entitlements restore without re-purchase
- [ ] If any task involved promotional offers: end-to-end-tested via App Store Server API server-signed JWS (not client-signed)
- [ ] If any task involved refund handling: simulated a refund via SKTestSession and verified entitlements are revoked within one app-lifecycle
- [ ] If any task involved paywall UX: re-tested against App Store Review Guideline 3.1.2 disclosure requirements

## Sensitive-content warning

This report may reference your bundle identifier, in-app purchase product
IDs, App Store Connect SKU naming, subscription group identifiers, and
potentially the promotional offer signing key ID. The promotional offer
*private key* itself must never appear in this report — if you find it,
that's a security incident, redact immediately. Treat the rest as
confidential.

## Dependencies

- Tooling output: `$AUDIT_DIR/tooling-raw/`
- Intermediate files: `$AUDIT_DIR/{claude,codex,synthesis,devils-advocate}.md`
```

## Outputs

- `$AUDIT_DIR/REPORT.md` exists, non-empty, contains the Implementation Plan with appropriate tiers populated

## Outgoing edges

- → `verify` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from report --to verify
```

## Failure modes

- Synthesis has zero findings → produce the single-task no-findings report; still transition to `verify`.
- Critical finding without a concrete remediation → write what's known and flag `**REMEDIATION INCOMPLETE**` in the task body.
