---
name: audit-apple-app-store-review
description: Dual-agent App Store Review Guidelines audit — full walk of Safety, Performance, Business, Design, Legal sections. Preempts the most common App Review rejection reasons before submission: metadata accuracy, completeness, IAP rules, private API usage, demo content, screenshots match shipping app, push notification compliance, ATT, privacy policy alignment, age rating.
---

# Apple App Store Review Audit

You are orchestrating a dual-agent audit anchored to Apple's App
Store Review Guidelines. Goal: preempt rejection reasons before
submission.

**Required reading**: Before starting, read [`lib/audit-framework.md`](../lib/audit-framework.md).
This file specifies only the audit-specific deltas.

**Audit identifier**: `apple-app-store-review` — `$AUDIT_DIR` is
`~/Reports/<org>/<repo>/audits/<TS>-apple-app-store-review/`

**Scope**: Swift source files for native Apple apps + Info.plist +
Privacy Manifest + asset catalog + (where available) App Store
Connect metadata. For privacy compliance specifically use
`audit-apple-privacy` — this audit covers the full Review Guidelines,
of which privacy is one section.

**Inherent limitations**: App Review enforcement varies in practice.
Static review against the Guidelines surfaces likely rejection
causes, but reviewers exercise judgment, and Apple updates the
Guidelines frequently. Treat findings as "high likelihood of
rejection" rather than "Apple will definitely reject" — and as a
checklist to clear before submitting.

The guidelines themselves are the source of truth and may change.
This audit reflects the structure as of late 2025. When in doubt,
read the current Guidelines.

---

## Schema extensions

Beyond the framework baseline, add:

| Column | Description |
|---|---|
| `Guideline` | The App Store Review Guideline section the finding maps to (e.g. `2.1`, `2.3.7`, `3.1.1`, `4.0`, `5.1.1`). Use the most-specific subsection. |
| `Section` | One of: `1. Safety`, `2. Performance`, `3. Business`, `4. Design`, `5. Legal` |
| `Rejection Likelihood` | `Will Reject` (clear violation), `Likely Reject` (judgment call but unfavorable), `Risk` (gray area), or `Best Practice` (not enforced but recommended) |
| `Verification` | `code` (inspectable) or `runtime` (requires App Store Connect / TestFlight / device review) |

Full schema:
```
| ID | Severity | Guideline | Section | Rejection Likelihood | Title | Location | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

---

## Categories

The audit walks the five Guidelines sections. Each section covers
multiple subsections — reviewers are expected to spot-check the most
common rejection patterns rather than exhaustively walk every
subsection.

### Section 1 — Safety

| # | Subsection | Most-common rejection patterns |
|---|---|---|
| 1.1 | Objectionable Content | UGC apps without moderation; offensive default content |
| 1.2 | User-Generated Content | No reporting mechanism; no block-user; no moderation |
| 1.3 | Kids Category | Inappropriate content; analytics / ads in kids apps |
| 1.4 | Physical Harm | Medical / driving / firearms apps without disclaimers |
| 1.5 | Developer Information | Contact info present; complete; reachable |

### Section 2 — Performance

| # | Subsection | Most-common rejection patterns |
|---|---|---|
| 2.1 | App Completeness | Crashes; placeholder content ("Lorem ipsum"); features that don't work; broken links; "coming soon"; demo account credentials wrong |
| 2.2 | Beta Testing | Don't submit beta builds to App Store |
| 2.3 | Accurate Metadata | Screenshots don't match shipping app; description over-promises; keywords irrelevant; subtitle / promotional text accurate; preview videos current; price tier mentioned in screenshots |
| 2.4 | Hardware Compatibility | App claims iPad support but iPad layout is broken; tvOS / watchOS / visionOS targets that don't actually run on those platforms |
| 2.5 | Software Requirements | Private API usage; deprecated framework usage; hidden / undocumented features; non-public APIs accessed via runtime reflection |

### Section 3 — Business

| # | Subsection | Most-common rejection patterns |
|---|---|---|
| 3.1.1 | In-App Purchase | Digital goods sold outside StoreKit; external links to web payment (rules softened — but still scoped); subscriptions without clear terms |
| 3.1.2 | Subscriptions | Auto-renewal not clearly disclosed; subscription terms not in app + on web; restore mechanism missing |
| 3.1.3(a-f) | External payment exceptions | Reader-app rules; multi-platform services rules; physical goods (not IAP) |
| 3.1.5(a) | Goods and Services Outside the App | Physical goods clearly outside IAP scope |
| 3.2 | Other Business Model Issues | Crypto / NFTs; fundraising; charity |

### Section 4 — Design

| # | Subsection | Most-common rejection patterns |
|---|---|---|
| 4.0 | Design overview | Low-quality / clone apps; minimum-effort apps; spam |
| 4.1 | Copycats | UI copies a known app |
| 4.2 | Minimum Functionality | App is "just a website"; trivial functionality |
| 4.5 | Extensions / SiriKit / Push notifications | Push notifications used for promotion without opt-in; Siri queries not handled; widgets that don't add value |
| 4.7 | HTML5 games, bots, etc. | Special category rules |
| 4.8 | Sign in with Apple | Required when other third-party sign-in offered |

### Section 5 — Legal

| # | Subsection | Most-common rejection patterns |
|---|---|---|
| 5.1.1 | Data Collection and Storage | Privacy policy missing or inaccurate; collecting more data than disclosed; ATT not implemented when IDFA accessed |
| 5.1.2 | Data Use and Sharing | Third-party data sharing not disclosed |
| 5.1.3 | Health and HealthKit | HealthKit data used without consent / appropriately |
| 5.1.4 | Kids and the Children's Category | COPPA compliance; parental gates |
| 5.1.5 | Location Services | Continuous location use without justification |
| 5.2 | Intellectual Property | Using others' IP; brand impersonation |
| 5.6 | Code of Conduct | Review manipulation; misleading content |

---

## Severity calibration

Severity is driven by **Rejection Likelihood**:

| Rejection Likelihood | Default Severity |
|---|---|
| Will Reject | Critical (Submission Blocker) |
| Likely Reject | High |
| Risk | Medium |
| Best Practice | Low |

Override based on the actual evidence: an explicit Guidelines
violation on a primary surface is Critical regardless; a "Will
Reject" on a gray area that App Review has historically allowed
might drop to High.

---

## Phase 1: Audit-specific orient

### Tooling

```bash
mkdir -p "$AUDIT_DIR/tooling-raw"

# Snapshot Info.plist (full)
find "$PROJECT_CWD" -name "Info.plist" -not -path '*/.*' -not -path '*/Pods/*' \
  -exec sh -c 'echo "=== $1 ==="; /usr/libexec/PlistBuddy -c "Print" "$1" 2>/dev/null' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/info-plist-full.txt" 2>&1

# Privacy Manifest snapshot
find "$PROJECT_CWD" -name "PrivacyInfo.xcprivacy" -not -path '*/.*' \
  -exec sh -c 'echo "=== $1 ==="; cat "$1"' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/privacy-manifests.txt" 2>&1

# Detect IAP / StoreKit
{
  echo "=== StoreKit usage ===";
  grep -rn "StoreKit\|SKProduct\|SKPaymentQueue\|Product.products\|Transaction\." \
    --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50;
  echo;
  echo "=== Subscription terminology ===";
  grep -rn -i "subscription\|auto-renew\|free trial\|introductory" \
    --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -30;
} > "$AUDIT_DIR/tooling-raw/storekit-usage.txt"

# Detect SiriKit / Push / Widget
{
  echo "=== Push notifications ===";
  grep -rn "UNUserNotificationCenter\|registerForRemoteNotifications" \
    --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -30;
  echo;
  echo "=== Sign in with Apple ===";
  grep -rn "ASAuthorizationAppleID\|AuthenticationServices" \
    --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -20;
  echo;
  echo "=== Third-party sign-in ===";
  grep -rn -i "GoogleSignIn\|FacebookLogin\|TwitterKit\|FBSDKLoginManager" \
    --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -20;
} > "$AUDIT_DIR/tooling-raw/auth-and-push.txt"

# Detect placeholder content
{
  echo "=== Placeholder text ===";
  grep -rn -i "lorem ipsum\|todo:\|fixme:\|placeholder\|coming soon\|test123\|example.com" \
    --include="*.swift" --include="*.json" "$PROJECT_CWD" 2>/dev/null | head -50;
} > "$AUDIT_DIR/tooling-raw/placeholder-content.txt"
```

### Emergency exit

None — but note that any Critical findings (`Submission Blocker`) are
sprint-blockers for the next submission.

### Survey

Beyond the framework baseline:

- Read `tooling-raw/` outputs to detect: IAP usage, push usage,
  Sign in with Apple presence, third-party sign-in presence,
  placeholder content
- Detect category-specific concerns: medical app? kids category?
  HealthKit? location-based? UGC?
- Note any App Store Connect metadata that's checked into the repo
  (Fastlane metadata, descriptions, screenshots) — if present, audit
  it for accuracy
- Determine the app's category and audience (kids? regulated?
  consumer? B2B?) — many guidelines are category-specific
- **If no Swift/Apple source found**: notify and stop

---

## Phase 2: Codex prompt body

Substitute into the canonical invocation (framework Phase 2 Step 1):

```text
Perform a thorough Apple App Store Review Guidelines audit of
[RESOLVED_SCOPE]. Tooling output is in $AUDIT_DIR/tooling-raw/.

Goal: preempt the most common App Review rejection causes before
submission. Walk the five sections of the App Store Review
Guidelines.

Write all findings to $AUDIT_DIR/codex.md using this exact table
format:
| ID | Severity | Guideline | Section | Rejection Likelihood | Title | Location | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
where ID uses prefix C (e.g. C001, C002).

Guideline column: the most-specific subsection (e.g. 2.1, 2.3.7,
3.1.1, 4.0, 5.1.1).
Section: "1. Safety", "2. Performance", "3. Business", "4. Design",
"5. Legal".
Rejection Likelihood: "Will Reject" (clear violation), "Likely
Reject" (judgment call, unfavorable), "Risk" (gray area), "Best
Practice" (not enforced).
Verification: code or runtime (where runtime means App Store
Connect / TestFlight / device review).

Cover all five sections (skip subsections that don't apply):

SECTION 1 — Safety:
- 1.1 Objectionable Content
- 1.2 User-Generated Content (moderation, reporting, blocking)
- 1.3 Kids Category
- 1.4 Physical Harm (medical, driving, firearms, etc.)
- 1.5 Developer Information

SECTION 2 — Performance:
- 2.1 App Completeness (crashes, placeholder content, broken
  features, "coming soon", broken demo accounts)
- 2.2 Beta Testing (don't submit beta builds to App Store)
- 2.3 Accurate Metadata (screenshots match shipping app, description
  accurate, keywords relevant, preview videos current, no price tier
  in screenshots)
- 2.4 Hardware Compatibility (iPad layout works on iPad-supporting
  apps, watchOS / tvOS / visionOS targets actually run)
- 2.5 Software Requirements (private API usage, deprecated frameworks,
  hidden features, runtime reflection)

SECTION 3 — Business:
- 3.1.1 In-App Purchase (digital goods via StoreKit; external
  payment scope rules)
- 3.1.2 Subscriptions (auto-renewal disclosed, terms in-app + on
  web, restore mechanism)
- 3.1.3(a-f) External payment exceptions
- 3.1.5(a) Physical goods outside IAP scope
- 3.2 Other Business Model Issues (crypto, fundraising)

SECTION 4 — Design:
- 4.0 Design overview (low-quality, clone apps, minimum-effort)
- 4.1 Copycats
- 4.2 Minimum Functionality (not "just a website")
- 4.5 Extensions / SiriKit / Push (push not for promotion without
  opt-in; Siri queries handled; widgets add value)
- 4.7 HTML5 games, bots
- 4.8 Sign in with Apple (required when third-party sign-in offered)

SECTION 5 — Legal:
- 5.1.1 Data Collection and Storage (privacy policy URL accurate,
  ATT when IDFA, Privacy Manifest accurate — refers to
  audit-apple-privacy for depth)
- 5.1.2 Data Use and Sharing
- 5.1.3 Health and HealthKit
- 5.1.4 Kids and Children's Category (COPPA, parental gates)
- 5.1.5 Location Services (continuous use justified)
- 5.2 Intellectual Property
- 5.6 Code of Conduct (no review manipulation)

Rejection Likelihood drives severity. Will Reject → Critical. Likely
Reject → High. Risk → Medium. Best Practice → Low.

Do not read or reference any other review file.
```

## Phase 2: Claude review checklist

Same five sections. Read `tooling-raw/` first — IAP / push / Sign in
with Apple / placeholder-content detection is in there. Note the
app's category and audience from Info.plist / asset catalog
patterns — many guidelines are category-specific.

If `audit-apple-privacy` has been run on this scope and produced
findings, reference them rather than duplicating (Section 5.1.1
overlap).

---

## Phase 4: Devil's advocate prompt body

```text
Read $AUDIT_DIR/synthesis.md and the tooling output in
$AUDIT_DIR/tooling-raw/. Your job is to attack the synthesis, not
improve it. Write your challenge to $AUDIT_DIR/devils-advocate.md
covering:
(1) False positives — findings flagged as Guidelines violations that
aren't (e.g. "Sign in with Apple required" doesn't apply when no
third-party sign-in is offered; "metadata mismatch" findings on
metadata that hasn't been generated yet; placeholder content in
test fixtures not shipping in app target).
(2) Rejection Likelihood miscalibrations — flagged as "Will Reject"
when App Review historically gives latitude on this point; flagged
as "Risk" when it's actually a clear rejection.
(3) Missing findings — Guidelines issues both reviewers missed,
especially: App Tracking Transparency edge cases (analytics SDK
that probes IDFA without ATT); subscription auto-renewal disclosure
gaps; Sign in with Apple ordering / visual treatment;
push-notification content that promotes; widget extension content
that doesn't justify its existence; Live Activity / Dynamic Island
that displays sensitive info publicly; In-App Events not following
the new guidelines.
(4) Remediation steps that miss the actual Guidelines requirement
(e.g. "add Sign in with Apple button" when the issue is button
ORDERING within the auth options).
Be specific. Every challenge must cite the finding ID and the
Guideline subsection.
```

---

## Phase 5: Sprint mapping override

Critical findings (Will Reject) → **Submission Blocker** section
above P0. These prevent App Store submission:

| Finding Severity | Sprint Priority |
|---|---|
| **Critical (Will Reject)** | **Submission Blocker — fix before next App Store submission** |
| High (Likely Reject) | P0 — Must Ship |
| Medium (Risk) | P1 — Ship If Capacity Allows |
| Low (Best Practice) | Deferred |

Each task includes its Rejection Likelihood + Guideline citation in
the task description.

---

## Output checklist additions

Beyond framework baseline:

- [ ] Each task has: finding ID, Guideline subsection, Section,
      Rejection Likelihood, Verification mode, location, issue,
      remediation, verification
- [ ] Submission Blocker findings broken out into separate section
      above P0
- [ ] Hand-off note flags App Store rejection risk explicitly with
      blocker count
- [ ] Category-specific Guidelines (Kids, Health, HealthKit,
      Location, Subscriptions) reviewed only where applicable
- [ ] If `audit-apple-privacy` has been run, reference it for Section
      5.1.1 depth rather than duplicating

---

## Reference

- Audit reference doc: [`docs/apple-app-store-review/README.md`](../docs/apple-app-store-review/README.md)
- Framework: [`lib/audit-framework.md`](../lib/audit-framework.md)
- App Store Review Guidelines (current): https://developer.apple.com/app-store/review/guidelines/
- App Store metadata best practices: https://developer.apple.com/app-store/product-page/
- App Tracking Transparency: https://developer.apple.com/documentation/apptrackingtransparency
- Sign in with Apple: https://developer.apple.com/sign-in-with-apple/
- StoreKit: https://developer.apple.com/documentation/storekit
- Push Notification Guidelines: https://developer.apple.com/notifications/
