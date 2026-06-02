Perform a thorough Apple App Store Review Guidelines audit of the scope
at the project root you've been pointed at. Tooling has already been
run; raw output is in the audit dir's tooling-raw/ subdirectory. Read
those files first: info-plist-full.txt (capability claims),
privacy-manifests.txt (Privacy Manifest), storekit-usage.txt (IAP /
subscription detection), auth-and-push.txt (push / Sign in with Apple /
third-party sign-in detection), placeholder-content.txt (placeholder /
"coming soon" text).

Goal: preempt the most common App Review rejection causes before
submission. Walk the five sections of the App Store Review Guidelines.

This audit covers BOTH the iOS App Store and the Mac App Store. Most
guideline subsections apply to both, but several diverge: App Sandbox
is required for Mac App Store only; ATT (App Tracking Transparency)
applies to iOS / iPadOS / tvOS / visionOS only; IAP rules differ
slightly for non-consumable Mac software (3.1.x). The project's
target platforms have been recorded in walker state by orient. In each
finding's Evidence/Notes column, tag the platform(s) the finding
applies to (e.g. "iOS only", "Mac App Store only", "iOS + Mac App
Store"). If the guideline subsection itself differs between iOS and
Mac App Store versions, note that explicitly.

Write all findings to codex.md (in the audit dir you were granted write
access to) using this exact table format:

| ID | Severity | Guideline | Section | Rejection Likelihood | Title | Location | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix C (e.g. C001, C002).

Guideline column: the most-specific subsection (e.g. 2.1, 2.3.7, 3.1.1,
4.0, 5.1.1).
Section: "1. Safety", "2. Performance", "3. Business", "4. Design",
"5. Legal".
Rejection Likelihood: "Will Reject" (clear violation), "Likely Reject"
(judgment call, unfavorable), "Risk" (gray area), "Best Practice" (not
enforced).
Verification: code or runtime (where runtime means App Store Connect /
TestFlight / device review).

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
- 4.5 Apple Sites and Services (use of Apple marks; APIs used as
  documented)
- 4.5.4 Push notifications (not for promotion without explicit
  opt-in; not for sensitive PII)
- 4.7 Mini apps / mini games / streaming games / chatbots / plug-ins
  / extensions (special category rules)
- 4.8 Sign in with Apple — required as equivalent option when
  primary login is third-party SSO (Facebook/Google/Twitter/etc.);
  not required when SSO is one of several options alongside a
  native account system

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

Do not read or reference the other agent's in-flight review files in
this audit ($AUDIT_DIR/claude.md, $AUDIT_DIR/codex.md). However, if a
prior /audit-apple-privacy run has finished on this scope (its
$AUDIT_DIR/REPORT.md is on disk under ~/Reports/.../audits/), you MAY
read that completed report and reference its findings for Section
5.1.1 depth — do not duplicate privacy findings here.

Every finding must include a Verification field. For App Store Review,
runtime verification means: a TestFlight build, an App Store Connect
metadata review, or a device test on the shipping build configuration.

Output requirements:
- Write to codex.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
