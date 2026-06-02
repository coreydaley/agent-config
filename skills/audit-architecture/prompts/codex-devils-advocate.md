Read synthesis.md in the audit dir you've been granted access to. Your
job is to attack the synthesis, not improve it.

Write your challenge to devils-advocate.md (in the same audit dir)
using this table format:

| ID | Challenge Type | Target Finding | Claim | Evidence | Confidence |

where:
- ID uses prefix D (D001, D002, ...)
- Challenge Type: false_positive | severity_miscalibrated |
  missing_finding | missing_compound | impractical_alternative |
  misestimated_migration_cost
- Target Finding: the S### ID from synthesis.md being challenged (or
  "N/A" for missing_finding / missing_compound)
- Claim: 1-2 sentence challenge
- Evidence: file:line citation, alternative explanation, or specific
  code reference
- Confidence: high | medium | low

Architecture is uniquely susceptible to LLM overconfidence — your
adversarial role is critical. Many "violations" called out by the
synthesis will be intentional design decisions appropriate for this
project's scale or constraints. Push back hard.

Cover these challenge categories:

(1) False positives — "violations" that are intentional design
decisions appropriate for this project's scale or constraints.
Specifically for architecture:
- A "tight coupling" finding between two modules that are genuinely
  one concept and should live together (Low Cohesion finding is
  actually a correct High Cohesion grouping).
- A "duplication" finding where the apparent duplicates are unrelated
  by domain and would couple via shared abstraction (the Rule of Three
  hasn't been hit; YAGNI says wait).
- A "missing abstraction" finding where the indirection would cost
  more than the duplication.
- A "convention inconsistency" finding where the inconsistency reflects
  a deliberate distinction (e.g. test helpers named differently from
  production helpers).
- An "over-engineering" finding where the abstraction is load-bearing
  for a planned near-term extension, not speculative.
- For agent-config repos: a "command/skill boundary" finding where the
  boundary is actually documented or intentional per the project's
  conventions.

(2) Severity miscalibrations — findings rated too high (LLM
overconfidence on architectural matters; reach is smaller than claimed;
trajectory is fine because the team has the discipline to keep it
contained) or too low (under-counting reach; under-counting trajectory
in a fast-growing area; missing that a single defect class will
multiply).

(3) Missing findings — structural issues both reviewers missed.
Architecture-specific blind spots:
- Hidden temporal coupling (module A must be initialized before module
  B but nothing enforces it).
- Implicit ordering assumptions in collection iteration.
- "Convenience" helpers that bypass the public API of a module.
- Test-only code paths that leak into production.
- Configuration that's actually code (long if/else chains keyed on a
  config string).
- Logging used as a control-flow side channel.
- For agent-config repos: prompt-injection-style coupling between
  command files (one command's prose dictates another's behavior
  implicitly).

(4) Missing compound paths — separate findings in the synthesis that
combine into a worse architectural problem than any single finding
represents. Be explicit about the chain and the combined severity.

(5) Impractical alternatives — proposed target designs that are
worse than the status quo, or that have misestimated migration cost.
E.g.:
- "Extract to interface" that adds indirection without testability
  benefit because there's only ever one implementation.
- "Move to a separate module" that creates a new circular dependency.
- "Apply Strategy pattern" when a function pointer or first-class
  function would do.
- Migration Cost rated Low when the change touches a shared boundary
  that requires team alignment.

(6) Misestimated migration cost — Migration Cost ratings that don't
account for coordination risk, downstream consumer breakage, or the
realistic risk of partial-migration limbo.

Be specific. Every challenge must cite the finding ID and reference
the named Pattern/Principle where applicable.

Do not read or reference any other review file beyond synthesis.md.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type "no_challenges"
  and Confidence "high" stating that you attempted but found nothing
  worth surfacing. (For architecture, this should be rare — push hard.)
- No emojis.
