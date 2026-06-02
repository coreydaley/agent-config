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
- Evidence: file:line citation, Guideline subsection, or specific App Store Connect / TestFlight reference
- Confidence: high | medium | low

Cover these challenge categories:

(1) False positives — findings flagged as Guidelines violations that
aren't:
- "Sign in with Apple required" (4.8) doesn't apply when no third-party
  sign-in is offered, OR when SSO is one of several options alongside
  a native account system.
- Metadata-mismatch findings on metadata that hasn't been generated yet
  (no fastlane/metadata, no App Store Connect listing draft).
- Placeholder content in test fixtures / preview providers / debug-only
  code paths that don't ship in the app target.
- Subscription disclosure findings against in-app purchases that are
  one-time consumables, not subscriptions.
- Kids-category findings against apps that aren't in the Kids category.

(2) Severity / Rejection Likelihood miscalibrations:
- Flagged as "Will Reject" when App Review has historically given
  latitude on this point (e.g. minor keyword stuffing, marginally stale
  screenshots).
- Flagged as "Risk" when it's actually a clear rejection (e.g. missing
  restore-purchase mechanism on a subscription is consistently
  rejected, not gray).
- Severity inflated by counting a single Guideline issue across
  multiple surfaces as multiple findings.

(3) Missing findings — Guidelines issues both reviewers missed,
especially:
- ATT edge cases — analytics SDK that probes IDFA via runtime
  reflection without prompting ATT.
- Subscription auto-renewal disclosure gaps in paywall copy.
- Sign in with Apple ordering / visual treatment per the HIG (button
  not at the top of the auth options, smaller than other SSO buttons).
- Push notification content that promotes (vs. transactional).
- Widget extension content that doesn't justify its existence (4.7).
- Live Activity / Dynamic Island that displays sensitive info publicly.
- In-App Events not following the current guidelines.
- App Intents / Shortcuts with parameters that don't validate input.
- 3.1.5(a) physical goods routed through IAP by mistake.
- 1.4 disclaimers missing on medical / driving / firearms apps.
- 5.1.5 continuous-location use without justification copy.

(4) Missing compound paths — separate findings in the synthesis that
combine into a worse rejection risk than any single finding (e.g.
metadata-mismatch + "coming soon" labels + broken demo creds together
read as a deceptive listing).

(5) Impractical/incomplete/wrong remediations:
- "Add Sign in with Apple button" when the issue is button ORDERING
  within the auth options, not button presence.
- "Update screenshots" without specifying which devices / locales /
  marketing channels.
- "Add restore button" without specifying restoreCompletedTransactions
  / Transaction.currentEntitlements wiring.

(6) Verification steps that don't actually prove the fix works:
- "Manual review" verification on a metadata change — should be App
  Store Connect screenshot diff.
- "Build runs" verification on an IAP change — should be StoreKit
  Configuration test + TestFlight purchase flow.

Be specific. Every challenge must cite the finding ID and the Guideline
subsection.

Do not read or reference any other review file beyond synthesis.md and
the tooling-raw/ directory.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type "no_challenges"
  and Confidence "high" stating that you attempted but found nothing
  worth surfacing.
- No emojis.
