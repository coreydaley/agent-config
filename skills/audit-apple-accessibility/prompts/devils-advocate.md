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

(1) False positives — findings that are actually accessible in
context. Specifically for Apple accessibility:
- A parent .accessibilityElement(children: .combine) already provides
  the label, so the child element's "missing label" finding is wrong.
- A SwiftUI Label view supplies the label implicitly from its content;
  the explicit .accessibilityLabel finding is a duplicate.
- A system control already has appropriate default traits (Button,
  Toggle, Picker) — the "missing trait" finding is wrong.
- A decorative element is already inside an accessibilityElement
  combine block, so the "missing accessibilityHidden(true)" finding
  has no impact.

(2) Severity miscalibrations — findings rated too high or too low
given the actual VoiceOver / Switch Control / Voice Control / Full
Keyboard Access impact and user exclusion severity. Consider:
- Compensating controls (parent labels, system defaults, sibling
  affordances).
- Reachability — is the affected view on the critical task path or
  edge-case settings?
- Blast radius — one button vs. a pattern repeated across the app.

(3) Missing findings — Apple accessibility issues the review
missed, especially:
- Focus traps in sheets / modals (focus stays behind the modal).
- Missing announcements on async state changes (network result,
  save complete, error appears).
- Dynamic Type breakage at AX sizes — clipped text, broken layouts,
  hardcoded frame sizes.
- Mac Catalyst keyboard navigation gaps — missing keyboard shortcuts,
  no focus ring, unreachable controls.
- watchOS Digital Crown focus and rotational input handling.
- visionOS-specific accessibility (eye tracking, hand interaction
  alternatives).
- App Intents accessibility (parameter prompts, result presentation).
- Widget / Live Activity accessibility (labels on Lock Screen,
  Dynamic Island compact / expanded states).
- Custom drawing (Canvas, drawingGroup) with no accessibilityElement
  override.
- Image / SF Symbol with no decorative-vs-meaningful classification.

(4) Missing compound paths — separate findings in the synthesis that
combine into a worse exclusion than any single finding represents
(e.g. modal trap + missing announcement = AT user loses both context
and the recovery signal). Be explicit about the chain and the
combined severity.

(5) Impractical / incomplete / wrong remediations — e.g. adding a
.accessibilityLabel that duplicates the trait suffix ("Submit
button button"), over-using .accessibilityHidden(true) and breaking
rotor navigation, adding @AccessibilityFocusState without restoring
focus on dismissal, switching to system font without verifying AX5.

(6) Verification steps that don't actually prove the fix works —
Apple-accessibility runtime verification often requires VoiceOver
phrasing checks, Switch Control scan-order checks, Dynamic Type AX5
checks, Full Keyboard Access focus-ring checks. "Manual review"
verification is insufficient for runtime-mode findings.

Be specific. Every challenge must cite the finding ID and the Apple
API or HIG principle if applicable.

Do not read or reference any other review file beyond synthesis.md.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type
  "no_challenges" and Confidence "high" stating that you attempted but
  found nothing worth surfacing.
- No emojis.
