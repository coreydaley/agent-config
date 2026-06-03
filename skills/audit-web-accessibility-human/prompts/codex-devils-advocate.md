Read synthesis.md and the raw tooling output in tooling-raw/ in the
audit dir you've been granted access to. Your job is to attack the
synthesis, not improve it.

Write your challenge to devils-advocate.md (in the same audit dir)
using this table format:

| ID | Challenge Type | Target Finding | Claim | Evidence | Confidence |

where:
- ID uses prefix D (D001, D002, ...)
- Challenge Type: false_positive | severity_miscalibrated |
  missing_finding | missing_compound | impractical_remediation |
  insufficient_verification
- Target Finding: the S### ID from synthesis.md being challenged
  (or "N/A" for missing_finding / missing_compound)
- Claim: 1-2 sentence challenge
- Evidence: file:line citation, compensating control identification,
  or specific code reference; cite the WCAG criterion where
  applicable.
- Confidence: high | medium | low

Cover these challenge categories:

(1) False positives — findings that are actually accessible in
context. Specifically for web a11y:
- An element flagged as unlabeled actually has an accessible name
  computed from a parent <label>, aria-labelledby chain, or
  associated <legend>.
- A "missing alt" finding on a decorative image that already has
  alt="" (or role="presentation") in the rendered DOM, even if the
  source looks ambiguous.
- An ARIA pattern flagged as wrong is actually correct for its role
  per the ARIA Authoring Practices Guide (e.g. role="tab" with
  aria-selected and tabindex="-1" / "0" pattern).
- A contrast finding measured against the wrong background (the
  element's effective background is a darker overlay, not the page
  body).
- A "no visible focus" finding on a component that defers to
  :focus-visible via a global rule the reviewer didn't see.
- A "live region missing" finding on content that's already
  announced via a sibling role="status" / role="alert".

(2) Severity miscalibrations — findings rated too high (low actual
exclusion: behind a feature flag, admin-only surface, debug-only
route, alternative path exists) or too low (under-counting blast
radius across a design system, or AA violation on a primary user
flow that should be Critical not High).

(3) Missing findings — web-a11y issues both reviewers missed:
- Focus indicator obscured by sticky header/footer (WCAG 2.4.11)
- Drag-and-drop without a keyboard-accessible alternative
  (WCAG 2.5.7)
- Target size below 24x24 CSS pixels on interactive elements
  (WCAG 2.5.8)
- Inaccessible authentication via cognitive function tests
  (WCAG 3.3.8)
- Page <title> missing or non-descriptive (WCAG 2.4.2)
- Language attribute missing on <html> or on inline language
  changes (WCAG 3.1.1, 3.1.2)
- Skip link missing or non-functional (WCAG 2.4.1)
- Autocomplete attributes missing on identity form fields
  (WCAG 1.3.5)
- Reflow at 320 CSS pixels (WCAG 1.4.10)
- Text spacing overrides break layout (WCAG 1.4.12)
- Content not visible on focus / hover (WCAG 1.4.13)

(4) Missing compound paths — separate findings in the synthesis that
combine into a worse exploit than any single finding represents.
Example: keyboard trap + missing visible focus + no Escape handler =
permanent stranding. Be explicit about the chain and the combined
severity.

(5) Impractical / incomplete / wrong remediations — e.g. adding
aria-label on a <div role="button"> instead of switching to
<button>; adding aria-live="assertive" to everything that updates;
recommending tabindex="0" on non-interactive elements; "use a
contrast checker" without specifying the required ratio;
remediations that themselves introduce new accessibility issues.

(6) Verification steps that don't actually prove the fix works —
"manual review" is insufficient for runtime findings; focus
management, live regions, and accessible name computation require
at-minimum a screen reader walkthrough (VoiceOver / NVDA / JAWS /
TalkBack). Static jest-axe / cypress-axe tests catch a subset; they
don't validate announcement order or focus restoration.

Be specific. Every challenge must cite the finding ID and reference
the WCAG criterion where applicable.

Do not read or reference any other review file beyond synthesis.md
and the tooling-raw/ directory.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type
  "no_challenges" and Confidence "high" stating that you attempted
  but found nothing worth surfacing.
- No emojis.
