Read synthesis.md, prd-source.md, and tooling-raw/section-map.md in the
directory you've been granted access to. Your job is to ATTACK the synthesis,
not improve it. Do not edit prd-source.md.

Write your challenge to devils-advocate.md (in the same directory) using this
table format:

| ID | Challenge Type | Target Finding | Claim | Evidence | Confidence |

where:
- ID uses prefix D (D001, D002, ...).
- Challenge Type: false_positive | severity_miscalibrated | missing_finding |
  missing_contradiction | weak_revision | not_actionable
- Target Finding: the S### ID from synthesis.md being challenged (or "N/A"
  for missing_finding / missing_contradiction).
- Claim: 1-2 sentence challenge.
- Evidence: a quote or section reference from prd-source.md, or the specific
  logic of the contradiction.
- Confidence: high | medium | low.

Cover these challenge categories:

(1) False positives — findings that aren't real defects in this PRD:
- The "missing" section actually exists elsewhere in the document.
- The requirement IS testable as written; the finding misread it.
- A deliberate, stated non-goal being flagged as a gap.
- An intentional v2 deferral flagged as scope creep.

(2) Severity miscalibrations — Nits inflated to Major/Blocker, or genuine
Blockers (un-buildable, contradictory, no success criteria) understated. Be
especially alert to severity inflation: an audit that marks everything a
Blocker is useless. Push back hard on Blockers that are really Minors.

(3) Missing findings — defects both reviewers missed:
- A goal and a non-goal that contradict each other.
- A success metric with no requirement that would move it.
- A requirement that silently violates a stated constraint.
- A happy-path-only requirement with an obvious unspecified failure mode.
- An undefined term load-bearing for an acceptance criterion.
- A privacy/security gap on personal or sensitive data.

(4) Missing contradiction clusters — separate findings that combine into a
worse problem than any one alone (e.g. premature-scale requirement stacked on
an unvalidated assumption; a metric, a goal, and a requirement that form an
impossible triangle). Be explicit about the chain and combined severity.

(5) Weak revisions — Suggested Revisions that are vague, would not actually
fix the problem, or merely restate the complaint ("make it clearer"). A
revision that isn't a concrete, applyable rewrite is a defect in the finding.

(6) Not actionable — findings a follow-up "update the PRD" agent could not act
on without more information than the finding provides.

Be specific. Every challenge must cite the finding ID (or section) it targets.

Do not read or reference any other review file beyond synthesis.md,
prd-source.md, and tooling-raw/section-map.md.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type "no_challenges"
  and Confidence "high" stating that you attempted but found nothing worth
  surfacing.
- No emojis.
