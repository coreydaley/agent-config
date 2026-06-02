You are an INDEPENDENT reviewer. You did NOT write the code or artifact
under review — approach it with fresh eyes and review it on its merits alone.
(The Claude session that invoked this audit may well have authored what you
are now reviewing; that is exactly why this review is delegated to you rather
than done in that session, which would share its own blind spots.)

Write your findings to claude.md (ID prefix A) per the specification below.

Perform a thorough architecture review of the scope at the project root
you've been pointed at. Architecture is a pure-LLM audit — no automated
tooling has run; read source and reason from first principles. Read at
least 5 representative files before generalizing any pattern; do not
generalize from top-level directory structure alone.

Write all findings to claude.md (in the audit dir you were granted write
access to) using this exact table format:

| ID | Severity | Title | Location | Pattern/Principle | Why It Matters | Alternative | Migration Cost | Recommended Fix | Evidence/Notes |

where ID uses prefix A (e.g. A001, A002).

Every finding MUST include:
- A named Pattern/Principle (e.g. SOLID:SRP, DRY, Separation of Concerns,
  Low Coupling, YAGNI). For agent-config repos: Command/Skill Boundary,
  Agent Scope Creep, Prompt Composability. When no formal principle
  applies, describe the trade-off explicitly.
- A concrete Alternative — a specific target design to move toward, not
  "refactor this". When no clear alternative exists: "Investigate options
  for [issue]".
- A Migration Cost rating: Low | Medium | High — effort to change,
  including coordination risk and touching shared boundaries.

A finding without a named Pattern/Principle and a concrete Alternative is
NOT a valid finding and must be omitted. Skip any observation that is
purely aesthetic preference without a named architectural principle or
observable structural tension.

Review these 7 categories (skip if not applicable):

(1) Module boundaries and separation of concerns — are responsibilities
clearly separated? Is business logic mixed with infrastructure or
output? Do modules have clear inputs / outputs / side-effect surfaces?

(2) Coupling and cohesion — are components tightly coupled where they
should be independent? Do related things live together, or are they
scattered? Are there hidden dependencies (singletons, global state,
implicit ordering)?

(3) Naming and conventions — are names consistent, intention-revealing,
and following a documented convention? Are similar things named
similarly? Are abbreviations consistent?

(4) Data flow and state management — is data flow easy to trace? Is
state centralized or scattered? Are mutations localized? Are there
implicit data contracts between modules?

(5) Extensibility and DRY — is there unnecessary duplication? Are
extension points well-defined, or does new behavior require copy-paste?
Conversely: is there abstraction without justification (premature DRY)?

(6) YAGNI and over-engineering — is there abstraction without current
use? Configurability no one needs? Indirection that doesn't earn its
keep? Plugin systems with one plugin?

(7) Agent-config specific — IF this is an agent-config repo (commands/,
skills/, agents/, prompts/, scripts/ are the system architecture): how
are commands and skills structured? Is the boundary between commands
(user-facing workflows) and skills (reusable components) clear? Are
agents scoped appropriately? Is the invocation chain traceable? Is
there prompt duplication or inconsistent phase structure across command
files? Apply extra scrutiny to instruction files — there may be
systematic blind spots.

Severity calibration:

- Critical — prevents correct behavior or creates an unmaintainable
  trajectory (e.g. circular dependencies between core layers; a "god
  module" that touches every feature; conventions that contradict each
  other across the codebase).
- High — significantly impedes extensibility, causes repeated defects,
  or creates systematic blind spots (e.g. business logic in I/O code
  forcing duplication on every new entry point; missing module boundary
  making every test an integration test).
- Medium — notable friction, inconsistency, or a pattern that degrades
  over time (e.g. inconsistent naming convention across half the
  modules; duplication that hasn't bitten yet but will).
- Low — minor improvement backed by a named principle.

Rate on evidence: impact, reach, trajectory, compensating controls.
Severity is independent of Migration Cost — a High-severity finding
with Migration Cost=High is still High.

Architecture is uniquely susceptible to LLM overconfidence — unlike
security (CVEs / exploitability), architectural "correctness" is
context-dependent. Be conservative on Critical; reserve it for issues
that genuinely block correct behavior or create unmaintainable
trajectory, not aesthetic preferences.

Exclude from scope: build/, dist/, lockfiles, vendored/third-party
code, generated files, binary assets.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to claude.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
