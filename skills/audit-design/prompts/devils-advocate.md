Read synthesis.md in the audit dir you've been granted access to. Your
job is to attack the synthesis, not improve it.

Write your challenge to devils-advocate.md (in the same audit dir) using
this table format:

| ID | Challenge Type | Target Finding | Claim | Evidence | Confidence |

where:
- ID uses prefix D (D001, D002, ...)
- Challenge Type: false_positive | severity_miscalibrated | missing_finding | missing_compound | impractical_remediation | insufficient_verification
- Target Finding: the S### ID from synthesis.md being challenged (or "N/A" for missing_finding / missing_compound)
- Claim: 1-2 sentence challenge
- Evidence: file:line citation, compensating control identification, or specific code reference
- Confidence: high | medium | low

Cover these challenge categories:

(1) False positives — findings that reflect intentional design choices
rather than actual problems. Specifically for design:
- A pattern flagged as "inconsistent" is actually two different
  components serving two different use cases.
- A color/spacing/typography value flagged as ad-hoc is actually a
  documented exception in the design system.
- A touch-target flagged as too small is on a non-interactive
  decorative element.
- A "missing affordance" finding ignores a clear textual cue or an
  established convention used elsewhere in the project.
- A "missing loading state" is on a synchronous operation where no
  loading state is appropriate.
- A platform-guideline-anchored finding contradicts the project's own
  design system (which should win — note the priority inversion).

(2) Severity miscalibrations — findings rated too high (low actual user
impact: only affects rarely-visited admin surfaces; behind a feature
flag; aesthetic preference dressed up as a usability issue) or too low
(under-counting breadth: pattern is broken across every primary screen;
under-counting task interruption: missing error state on a payment
flow).

(3) Missing findings — design issues the review missed:
- Inconsistent error-message tone across surfaces
- Empty-state design absent on lists / search / filtered views
- Loading-state design absent on async operations
- Focus-state visibility for keyboard navigation
- Reduced-motion / prefers-reduced-motion support
- Right-to-left layout breakage
- Dark-mode color drift / hardcoded light-mode colors
- Internationalization breakage (text overflow, truncation)
- Disabled-state contrast / affordance
- Hover-only interactions on touch devices
- Form-validation timing (eager vs. on-submit) inconsistencies
- Skeleton-loader vs. spinner inconsistency
- Iconography style mismatch (filled vs. outlined mixed)

(4) Missing compound paths — separate findings in the synthesis that
combine into a worse UX than any single finding represents. Be explicit
about the chain and the combined severity. Example: weak affordance +
no loading feedback + no error state on the same control = users believe
the app is broken.

(5) Impractical / incomplete / wrong remediations — e.g. "use design
system tokens" when no design system exists; "make consistent with
existing pattern" when there are two competing existing patterns and the
finding doesn't pick one; component refactors that would introduce new
inconsistencies elsewhere; remediations that contradict the heuristic
the finding was anchored to.

(6) Verification steps that don't actually prove the fix works — design
verification typically requires a built UI + visual comparison.
"Manual review" verification is insufficient for visual-rendering
claims. For accessibility findings, named tooling (axe, VoiceOver,
Accessibility Inspector) is the floor.

Be specific. Every challenge must cite the finding ID and reference the
heuristic anchor (project design system / cross-pattern / Nielsen N#X /
Apple HIG / Material Design) where applicable.

Do not read or reference any other review file beyond synthesis.md.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type "no_challenges"
  and Confidence "high" stating that you attempted but found nothing
  worth surfacing.
- No emojis.
