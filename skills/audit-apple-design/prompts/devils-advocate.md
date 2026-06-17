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
- Evidence: file:line citation, HIG section reference, or design-system rationale
- Confidence: high | medium | low

Cover these challenge categories:

(1) False positives — findings that reflect intentional design choices
or are platform-appropriate. Specifically for Apple design:
- A tab bar on macOS Catalyst is intentional for cross-platform
  consistency rather than a HIG violation.
- A custom control exists for a deliberate brand reason and the
  project has a documented design system that takes precedence.
- A "non-system" color is a design-token brand color used correctly.
- An animation flagged as gratuitous is actually a documented
  matched-geometry transition that improves task continuity.

(2) Severity miscalibrations — findings rated too high (aesthetic
preferences that HIG explicitly leaves to the designer; deviations
that are documented as intentional in a project style guide) or too
low (broken navigation on the primary flow; whole-surface dark-mode
failure; tab bar on macOS that breaks platform feel across the app).

(3) Missing findings — design issues the review missed,
especially:
- Focus-engine handling on tvOS
- Digital Crown handling on watchOS
- Crown / ornament patterns on visionOS
- Mac Catalyst menu bar gaps
- Window-state restoration on macOS
- App Icon variants (alternate icons, tinted icons, Dynamic Island
  layouts)
- Live Activity / Dynamic Island layouts
- StoreKit upsell sheet vs full-screen cover misuse
- Share sheet vs custom share UI
- Document-based app affordances on iPad / Mac

(4) Missing compound paths — design issues that combine into a worse
experience than any single finding represents (e.g. dark-mode failure
+ missing asset variants + hardcoded foreground on the same surface).

(5) Impractical or wrong remediations — e.g. switching to
NavigationSplitView when the data model doesn't fit; replacing a
custom control with a stock SwiftUI one that doesn't support the
required interaction; introducing inconsistencies by changing one
screen without updating its peers.

(6) Verification steps that don't actually prove the fix works —
animation timing, gesture feel, and material rendering require
Simulator / on-device review. "Manual code review" is insufficient
for runtime-verified findings.

Be specific. Every challenge must cite the finding ID and reference
the HIG section where applicable.

Do not read or reference any other review file beyond synthesis.md.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type "no_challenges"
  and Confidence "high" stating that you attempted but found nothing
  worth surfacing.
- No emojis.
