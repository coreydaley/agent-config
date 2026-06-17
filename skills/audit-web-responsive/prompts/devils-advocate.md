Read synthesis.md in the audit dir you've been granted access to. Your
job is to attack the synthesis, not improve it.

Write your challenge to devils-advocate.md (in the same audit dir)
using this table format:

| ID | Challenge Type | Target Finding | Claim | Evidence | Confidence |

where:
- ID uses prefix D (D001, D002, ...)
- Challenge Type: false_positive | severity_miscalibrated | missing_finding | missing_compound | impractical_remediation | insufficient_verification
- Target Finding: the S### ID from synthesis.md being challenged (or "N/A" for missing_finding / missing_compound)
- Claim: 1-2 sentence challenge
- Evidence: file:line citation, compensating control identification, or specific code reference
- Confidence: high | medium | low

Cover these challenge categories:

(1) False positives — findings that are actually correct responsive
behavior. Specifically for web responsive design:
- An intentional fixed-width component (e.g. a print-only stylesheet,
  an admin-only desktop dashboard, a third-party embed with its own
  responsive contract).
- A desktop-only admin panel that legitimately doesn't need mobile
  support (verify the project's stated browser/device matrix).
- A pattern that degrades gracefully on mobile via a different layout
  the reviewer missed (e.g. a separate mobile component selected by
  media query at the React-component level).
- A "missing" breakpoint that's already handled by the framework's
  default (Tailwind, Bootstrap) or a parent container query.
- A hover-only pattern paired with an existing :focus-visible or
  click-toggle fallback the reviewer missed.

(2) Severity miscalibrations — findings rated too high (the affected
breakpoint is uncommon in this product's actual user base; the broken
component is on a low-traffic page; there's a working alternative
path) or too low (the issue blocks the primary conversion flow on
mobile; mobile is the dominant traffic source per the product's stated
analytics; the affected component is site-wide).

(3) Missing findings — responsive issues the review missed:
- Viewport meta tag misconfiguration (initial-scale wrong, maximum-
  scale capped, user-scalable=no)
- iOS Safe Area / notch handling (env(safe-area-inset-*))
- Sticky element stacking issues on iOS (-webkit-overflow-scrolling)
- :focus-visible missing on interactive elements (keyboard nav fails
  on tablet keyboards)
- Container-query opportunities missed (component-level responsiveness)
- prefers-reduced-motion not respected on responsive animations
- text-size-adjust missing causing iOS auto-zoom on form focus
- aspect-ratio missing on responsive image/video containers (layout
  shift on slow connections)
- print stylesheet responsiveness regressions

(4) Missing compound paths — separate findings in the synthesis that
combine into a worse exploit than any single finding represents (e.g.
horizontal overflow + below-fold CTA + no mobile nav = primary CTA
effectively unreachable on mobile). Be explicit about the chain and
the combined severity.

(5) Impractical/incomplete/wrong remediations — e.g. setting
width:auto without setting max-width and breaking the desktop layout;
adding viewport meta but with user-scalable=no; switching to flexbox
but with fixed-height children that overflow; adding a hamburger menu
that itself doesn't meet the 44px touch target.

(6) Verification steps that don't actually prove the fix works —
"manual review" is insufficient for runtime-verification findings;
"test at 375px" is incomplete (also need 768px, 1024px, and ideally
a physical device). Negative-test verification (load the page at the
broken viewport, confirm content is reachable and interactive) is
preferred.

Be specific. Every challenge must cite the finding ID and reference
the breakpoint/category where applicable.

Do not read or reference any other review file beyond synthesis.md.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type "no_challenges"
  and Confidence "high" stating that you attempted but found nothing
  worth surfacing.
- No emojis.
