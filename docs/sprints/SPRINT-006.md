# Sprint 006: `audit-architecture` Command

## Overview

SPRINT-004 established the `audit-*` command family with `audit-security`. SPRINT-005
extended it with `audit-design` and `audit-accessibility`. This sprint delivers the
fourth member: `audit-architecture`.

`audit-architecture` applies the proven 5-phase dual-agent workflow to architectural
review: examining structural decisions, module boundaries, coupling patterns, separation
of concerns, naming conventions, data flow, and extensibility trade-offs. It produces
an executable sprint of architecture improvement tasks, each anchored to a named
principle or observable trade-off — not architectural opinion. For agent-config repos,
it explicitly inspects `commands/`, `skills/`, `agents/`, `prompts/`, and `scripts/`
structure and invocation patterns.

The key design challenge is that architecture is more subjective than security or
WCAG compliance. The finding schema addresses this by requiring every finding to cite
a named principle or observable trade-off AND propose a specific alternative approach.
Findings without a named anchor are skipped.

**Inherent limitations**: LLM architectural review cannot replace domain knowledge
about runtime behavior, team conventions, or organizational constraints. The output is
a structured starting point for team discussion, not a mandate to refactor.
Architecture is uniquely susceptible to LLM overconfidence: unlike security (external
anchors: CVEs, exploitability) or accessibility (external anchors: WCAG criteria),
architectural "correctness" is context-dependent. Treat every finding as a hypothesis
requiring team validation before execution. The evidence discipline (named principle +
concrete alternative) reduces noise but cannot eliminate it.

## Guiding Principles

- Reuse the established `audit-*` 5-phase workflow rather than inventing
  architecture-specific orchestration
- Keep findings anchored to named patterns, principles, trade-offs, and observable
  repository structure — not taste
- Make the command useful for both ordinary application repos and agent-config repos
- Preserve the `/sprint-work` output contract
- Favor the smallest viable scope: author the command file well before expanding

## Use Cases

1. **New-repo architecture review**: surface structural decisions worth revisiting
   before they become load-bearing
2. **Pre-refactor analysis**: scope to a directory; surface hidden coupling before
   a planned refactor
3. **Agent-config self-audit**: review how commands, skills, and agents are structured
   and interact; identify over-coupling, redundant patterns, or missing abstractions
4. **Periodic architecture health check**: run on a growing codebase to surface drift
   from original design intent

## Out of Scope

- Modifying existing `audit-security`, `audit-design`, or `audit-accessibility`
- Introducing ADR workflows, architecture scoring, or a separate remediation command
- Changing `/sprint-work`, the ledger model, or sprint document format
- Architecture-specific automation, linters, or repository analysis scripts
- README updates beyond discovery documentation (P1)

## Architecture

```
audit-architecture [$ARGUMENTS = optional path(s)]

Phase 1: Orient
  → Validate scope ($ARGUMENTS or cwd; supports multiple paths)
  → Survey structure: entry points, module boundaries, dependency flow
  → Explicit exclusions: build/, dist/, lockfiles, vendored/3rd-party code
  → Warn and continue if no recognizable formal structure (do not stop)
  → Determine next SPRINT-NNN number
  → Create docs/architecture/ if needed

Phase 2: Independent Reviews (parallel)
  → Codex: write docs/architecture/NNN-CODEX.md  (background)
  → Claude: write docs/architecture/NNN-CLAUDE.md (simultaneously)
  → Both use the full architecture finding schema

Phase 3: Synthesis
  → Verify both files non-empty; single-agent warning if one missing
  → Deduplicate; calibrate severity on evidence
  → Write docs/architecture/NNN-SYNTHESIS.md

Phase 4: Devil's Advocate (Codex)
  → Codex attacks synthesis → docs/architecture/NNN-DEVILS-ADVOCATE.md
  → Claude incorporates valid challenges; documents every rejection

Phase 5: Sprint Output
  → Produce docs/sprints/SPRINT-NNN.md
  → Severity → priority: Critical/High=P0, Medium=P1, Low=Deferred
  → /ledger add NNN "Architecture: [scope]"
  → User reviews ordering and migration costs, then /sprint-work NNN
```

## Finding Schema

`audit-architecture` extends the `audit-*` base schema with architecture-specific
extension columns. Core columns are preserved; extension columns are added after
`Location`:

```
| ID | Severity | Title | Location | Pattern/Principle | Why It Matters | Alternative | Migration Cost | Recommended Fix | Evidence/Notes |
|----|----------|-------|----------|-------------------|----------------|-------------|----------------|-----------------|----------------|
| C001 | High | Command phase logic mixed with output formatting | commands/sprint-plan.md:112 | Separation of Concerns | Changes to phase logic require editing formatting code and vice versa | Extract phase-transition logic to return structured data; let a separate formatting layer render it | Medium | Define a phase result type; update 3 call sites in sprint-plan.md | Phase 3 inline formatting at lines 112-140 conflates state management with display |
```

**Core columns** (from `audit-*` base): `ID`, `Severity`, `Title`, `Location`,
`Why It Matters`, `Recommended Fix`, `Evidence/Notes`

**Architecture extension columns**: `Pattern/Principle`, `Alternative`,
`Migration Cost`

- **Pattern/Principle**: the named architectural rule or observable trade-off in
  tension. Examples: `SOLID:SRP`, `DRY`, `Separation of Concerns`, `Low Coupling`,
  `High Cohesion`, `YAGNI`, `Explicit over Implicit`. For agent-config: `Command/Skill
  Boundary`, `Agent Scope Creep`, `Prompt Composability`. When no formal principle
  applies, describe the trade-off explicitly (e.g., "Coupling: invocation config
  embedded in output template").
- **Alternative**: the better structural design to move toward — not "refactor this"
  but a specific alternative approach. When no clear alternative exists, document
  "Investigate options for [issue]" as the alternative — this is preferable to forcing
  an overconfident redesign proposal
- **Migration Cost**: `Low`, `Medium`, or `High` — effort to change, including
  coordination risk and touching shared boundaries
- **Recommended Fix**: the concrete implementation step (may be different from the
  Alternative, which describes the target design)

**Evidence discipline**: a finding without a named `Pattern/Principle` (or explicit
trade-off description) and a concrete `Alternative` is **not a valid finding** and
must be skipped. When principle labels feel redundant, prefer concrete trade-off
language. Reviewer agreement raises confidence, not severity.

**ID prefix convention**: Claude = `A001, A002...`; Codex = `C001, C002...`;
Synthesis = `S001, S002...`

**Severity anchors**:
- Critical: prevents correct behavior or creates an unmaintainable trajectory
- High: significantly impedes extensibility, causes repeated defects, or creates
  systematic blind spots
- Medium: notable friction, inconsistency, or a pattern that degrades over time
- Low: minor improvement backed by a named principle

## Implementation Plan

### P0: Must Ship

#### P0-A: Author `commands/audit-architecture.md`

**Files:**
- `commands/audit-architecture.md` — NEW

**Frontmatter:**
```yaml
---
description: >-
  Dual-agent architecture audit — Claude and Codex review structural decisions
  independently, synthesize, devil's advocate pass, output as executable sprint
---
```

**Phase 1 — Orient requirements:**
- Validate scope from `$ARGUMENTS` (supports multiple space-separated paths) or
  default to cwd; store resolved paths — never interpolate raw `$ARGUMENTS` into
  shell strings
- **Scope exclusions**: exclude `build/`, `dist/`, `.next/`, lockfiles
  (`package-lock.json`, `yarn.lock`, `Pipfile.lock`), `vendor/`, `node_modules/`,
  generated files, and binary assets unless explicitly included in `$ARGUMENTS`
- **Minimum discovery before findings**:
  - Identify owned entry points and major module boundaries
  - Survey `git log --oneline -10` for recent structural changes
  - Identify dependency direction or import hotspots where visible
  - For agent-config repos: survey `commands/`, `skills/`, `agents/`, `prompts/`,
    `scripts/` — these define the agent system architecture
  - Read at least 5 representative files before generalizing a pattern — do not
    generalize from top-level directory structure alone
- **Pre-existing artifact check**: if `docs/architecture/AUDIT_NNN-*.md` files
  already exist for the chosen sprint number, warn the user and stop — do not
  silently overwrite a previous audit run
- **Unusual/flat repos**: if no recognizable formal structure is found, warn
  ("No formal structure detected in [scope] — findings may be limited") and continue;
  do not stop
- Determine next SPRINT-NNN; create `docs/architecture/` if needed
- Store `AUDIT_NNN` as the literal sprint number for all subsequent file references

**Phase 2 — Independent Review requirements:**

Launch Codex in background (substitute resolved scope and AUDIT_NNN):
```bash
codex exec "Perform a thorough architecture review of [RESOLVED_SCOPE]. \
  Write all findings to docs/architecture/AUDIT_NNN-CODEX.md using this exact \
  table format: \
  | ID | Severity | Title | Location | Pattern/Principle | Why It Matters | \
  Alternative | Migration Cost | Recommended Fix | Evidence/Notes | \
  where ID uses prefix C (e.g. C001, C002). \
  Review these categories: \
  (1) Module boundaries and separation of concerns — are responsibilities \
  clearly separated? Is business logic mixed with infrastructure or output? \
  (2) Coupling and cohesion — are components tightly coupled where they should \
  be independent? Do related things live together? \
  (3) Naming and conventions — are names consistent, intention-revealing, and \
  following a documented convention? \
  (4) Data flow and state management — is data flow easy to trace? Is state \
  centralized or scattered? \
  (5) Extensibility and DRY — is there unnecessary duplication? Are extension \
  points well-defined or does new behavior require copy-paste? \
  (6) YAGNI and over-engineering — is there abstraction without current use? \
  Configurability no one needs? \
  (7) For agent-config repos (commands/, skills/, agents/, prompts/, scripts/): \
  how are commands and skills structured? Is the boundary between commands \
  (user-facing workflows) and skills (reusable components) clear? Are agents \
  scoped appropriately? Is the invocation chain traceable? Is there prompt \
  duplication or inconsistent phase structure across command files? \
  Every finding MUST include a named Pattern/Principle (or explicit trade-off \
  description) and a concrete Alternative. Skip any observation that is purely \
  aesthetic preference without a named architectural principle or observable \
  structural tension. Rate severity on: does this prevent correct behavior, \
  impede extensibility, or create systematic debt? \
  Exclude from scope: build/, dist/, lockfiles, vendored/third-party code, \
  generated files, binary assets. \
  Do not read or reference any other review file."
```

Claude writes its own independent review to `docs/architecture/AUDIT_NNN-CLAUDE.md`
simultaneously, covering the same 7 categories with the same schema (ID prefix `A`).
Extra scrutiny for agent-config repos: command/skill/agent boundaries, invocation
chain legibility, prompt composability, repeated phase structures across command files.

Wait for Codex to finish before proceeding to Phase 3.

**Tasks:**
- [ ] Write `commands/audit-architecture.md` with complete 5-phase workflow
- [ ] Verify all Codex exec prompts are self-contained (AUDIT_NNN literal,
      no `--model`/`--full-auto`, no raw `$ARGUMENTS` interpolation)
- [ ] Verify finding schema includes `Pattern/Principle`, `Alternative`,
      `Migration Cost` extension columns with evidence discipline instruction
      in the Phase 2 prompt body
- [ ] Verify scope exclusions for generated/vendored code are in Phase 1
- [ ] Verify warn-and-continue (not stop) for unusual/flat repos
- [ ] Verify multi-path scope is carried through: prompts, sprint title, ledger entry

**Acceptance:**
- `commands/audit-architecture.md` exists with valid single-line `description:`
  frontmatter (Gemini TOML compatible)
- Phase 2 runs Claude and Codex in parallel
- Finding schema includes the architecture extension columns
- Evidence discipline instruction is in the Phase 2 prompt, not just the principles
- Phase 1 warns (does not stop) for unusual scope

#### P0-B: Synthesis and Devil's Advocate Behavior

*(Embedded in `commands/audit-architecture.md` Phase 3 and Phase 4 sections)*

**Phase 3 — Synthesis requirements:**
- Verify both files non-empty (single-agent warning if one missing — note prominently
  in synthesis: "⚠️ Single-agent synthesis — [agent] review was unavailable.")
- Deduplicate: same structural issue in both = higher confidence, not higher severity;
  when merging, preserve the most specific `Alternative` and `Evidence/Notes`
- For multi-path scopes: merge findings across paths; when path context is material
  to a finding, preserve it in `Location`
- When the same pattern-violation appears across many locations, create one finding
  and document extent in Evidence/Notes
- Calibrate severity on evidence: impact on maintainability, extensibility, defect
  rate — not on reviewer agreement

Write `docs/architecture/AUDIT_NNN-SYNTHESIS.md`:

```markdown
# Architecture Audit Synthesis — AUDIT_NNN

## Scope
[Resolved scope path(s)]

## Summary
- Total findings: N (Critical: X, High: X, Medium: X, Low: X)
- Reviewers: Claude (A-prefix), Codex (C-prefix)
- [Single-agent warning if applicable]

## Unified Findings

| ID | Severity | Title | Location | Pattern/Principle | Why It Matters | Alternative | Migration Cost | Recommended Fix | Evidence/Notes | Sources |
...

## Findings Present in Only One Review
[Note findings not corroborated by the other reviewer and why retained or dropped]

## Rejected Devil's Advocate Challenges
[Added after Phase 4]
| Finding/Claim | Reason Rejected |
|---|---|
```

**Phase 4 — Devil's Advocate requirements:**
```bash
codex exec "Read docs/architecture/AUDIT_NNN-SYNTHESIS.md. Attack it. Write to \
  docs/architecture/AUDIT_NNN-DEVILS-ADVOCATE.md covering: \
  (1) False positives — 'violations' that are intentional design decisions \
  appropriate for this project's scale or constraints, or principles cited \
  without observed evidence. \
  (2) Severity miscalibrations — findings rated too high or too low. \
  (3) Missing findings — structural issues both reviewers missed. \
  (4) Alternatives that are impractical, create worse problems, or have \
  misestimated migration cost. \
  Cite finding ID for every challenge."
```

Claude reads the devil's advocate output and:
- Removes confirmed false positives
- Recalibrates severity where challenge is valid and evidence supports it
- Adds genuinely missed findings with new synthesis IDs
- Documents every rejected challenge with explicit reasoning in the
  "Rejected Devil's Advocate Challenges" section of `AUDIT_NNN-SYNTHESIS.md`

**Tasks:**
- [ ] Verify synthesis template structure is in the command (Scope, Summary, Unified
      Findings, Findings in Only One Review, Rejected Challenges)
- [ ] Verify single-reviewer warning path is documented
- [ ] Verify Codex devil's advocate prompt covers: false positives (intentional
      design choices), severity miscalibrations, missing findings, impractical
      alternatives
- [ ] Verify rejected challenges require explicit reasoning

#### P0-C: Sprint Output Contract

*(Embedded in `commands/audit-architecture.md` Phase 5 section)*

**Sprint mapping:**

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

**Migration Cost nuance**: High findings with Migration Cost=High should be in P0,
but the task description must note: "Requires team alignment and design discussion
before execution — do not begin implementation without broader agreement." These are
not self-contained refactors.

Each sprint task must include:
- Finding ID (from synthesis)
- Location (file and line where applicable)
- Pattern/Principle in tension
- Issue description
- Specific alternative approach
- Migration cost
- Concrete remediation step
- Verification: how to confirm the fix is correct

**No-findings case**: if synthesis contains zero findings after Phase 4:
- Create a single P0 task: "Verify no findings — [scope], [date]"
- Task must document: scope covered, categories reviewed (list all 7), date,
  reviewer agents, approximate number of files read, and specific areas that
  received the most scrutiny
- Do not produce an empty sprint

**Multi-path scope in title**: when multiple paths were audited, sprint title is:
`Architecture Audit: [path1], [path2] ([YYYY-MM-DD])`; ledger entry uses the same
comma-separated scope string.

**Register and hand off**:
1. Register: `/ledger add AUDIT_NNN "Architecture: [scope]"`
2. Inform the user:

   > ✅ Architecture audit complete. SPRINT-AUDIT_NNN has been created and added
   > to the ledger.
   >
   > **Important**: architecture findings are LLM hypotheses under shallow discovery —
   > validate each P0/P1 finding against team knowledge before executing tasks.
   >
   > **Before running /sprint-work**: review task ordering in
   > `docs/sprints/SPRINT-AUDIT_NNN.md` — architecture changes often have sequencing
   > dependencies. P0 tasks with Migration Cost=High require team alignment before
   > implementation; do not begin those without broader design discussion.
   >
   > When ready: `/sprint-work AUDIT_NNN`

**Tasks:**
- [ ] Verify Phase 5 follows `docs/sprints/README.md` template
- [ ] Verify severity mapping is documented in the command
- [ ] Verify each task includes finding ID, location, principle, alternative,
      migration cost, remediation, verification
- [ ] Verify no-findings case produces a "Verify no findings" P0 task
- [ ] Verify `/ledger add` uses correct skill syntax
- [ ] Verify multi-path scope convention in title and ledger entry
- [ ] Verify user handoff note mentions migration cost and task ordering

### P1: Ship If Capacity Allows

#### P1-A: `README.md` Update

Add `audit-architecture` to `README.md`:
- Brief description and invocation example
- Relationship to the `audit-*` family and `/sprint-work`
- Note on inherent subjectivity and human judgment requirement

**Acceptance:** users can discover `audit-architecture` without reading the source file

#### P1-B: `docs/architecture/README.md`

Lightweight reference for the `docs/architecture/` directory:
- Purpose and naming convention (NNN matches sprint number)
- Full finding schema with all columns documented
- Note: these files may reveal structural weaknesses; review before committing to
  public repos

### Deferred

- `audit-deps` and other `audit-*` commands — validate the pattern in subjective
  domains first
- Shared `audit-*` workflow template/generator
- ADR workflow as secondary artifact
- Automated architecture graph extraction or code-mapping tools
- Linear/Jira sync for architecture findings

## Files Summary

| File | Action | Purpose |
|------|--------|---------|
| `commands/audit-architecture.md` | Create | 5-phase dual-agent architecture audit command (P0) |
| `README.md` | Modify | Discoverability and invocation examples (P1-A) |
| `docs/architecture/README.md` | Create | Naming convention and finding schema (P1-B) |

## Definition of Done

- [ ] `commands/audit-architecture.md` exists with valid single-line `description:` frontmatter
- [ ] Phase 2: Codex launched in background; Claude reviews simultaneously
- [ ] Finding schema includes `Pattern/Principle`, `Alternative`, `Migration Cost`
      extension columns alongside preserved core columns
- [ ] Schema extension declared explicitly (core + architecture extensions)
- [ ] Evidence discipline: opinion-only findings without named principle/trade-off
      explicitly skipped — instruction is in the Phase 2 prompt body
- [ ] Scope exclusions: generated/vendored/lockfiles/binary excluded by default
- [ ] Phase 1: minimum discovery steps specified before findings are allowed
- [ ] Phase 1: warn-and-continue (not stop) for unusual/flat repos
- [ ] Phase 1: validates `$ARGUMENTS` as path(s); raw argument never interpolated
      into Codex exec shell strings
- [ ] Phase 3: synthesis template structure documented in command
- [ ] Phase 3: verifies both files non-empty; single-agent warning if one missing
- [ ] Phase 4: Codex devil's advocate prompt covers: false positives (intentional
      design), severity miscalibrations, missing findings, impractical alternatives
- [ ] Phase 4: every rejected challenge documented with explicit reasoning
- [ ] Phase 5: follows `docs/sprints/README.md` template
- [ ] Phase 5: severity mapping documented (Critical/High=P0, Medium=P1, Low=Deferred)
- [ ] Phase 5: no-findings produces "Verify no findings" P0 task (not empty sprint)
- [ ] Phase 5: `/ledger add AUDIT_NNN` completed (or user instructed manually)
- [ ] Phase 5: user handoff notes task ordering and Migration Cost before `/sprint-work`
- [ ] Multi-path scope carried through: Phase 2 prompts, sprint title, ledger entry
- [ ] No `--model`/`--full-auto` flags in any Codex exec call
- [ ] No raw `$ARGUMENTS` interpolation in any Codex exec prompt
- [ ] Phase 1 checks for pre-existing `docs/architecture/AUDIT_NNN-*.md` files and
      warns/stops before overwriting a previous run
- [ ] Phase 1 validates each path in `$ARGUMENTS` confirms it exists (via filesystem
      check) before storing as resolved scope (SR-001)
- [ ] Phase 2 and Phase 4 Codex exec prompts explicitly restrict writes to
      `docs/architecture/` and prohibit shell command execution (SR-003)
- [ ] Phase 5 tasks are scoped to specific, enumerable changes; no task broadly
      modifies a directory without listing the affected files; High + Migration
      Cost=High tasks include "requires team alignment" note (SR-005)
- [ ] Manual read-through: each phase produces what the next phase consumes
- [ ] Edge-case read-through: (1) no scope arg, (2) path-scoped audit, (3) multi-path
      audit, (4) overlapping findings, (5) no findings, (6) flat/unusual repo,
      (7) pre-existing AUDIT_NNN artifacts

## Verification Plan

1. Compare `commands/audit-architecture.md` against `commands/audit-security.md` —
   confirm same phase ordering and execution contract
2. Inspect finding schema: confirm core audit columns are preserved and extension
   columns are explicitly labeled as architecture extensions
3. Read every `codex exec` prompt and confirm: no `--model`/`--full-auto`, no raw
   `$ARGUMENTS`, resolved scope and AUDIT_NNN embedded literally
4. Phase-to-phase read-through: each phase produces what the next consumes
5. Edge-case coverage check against the 6 edge cases listed in DoD

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Findings become subjective style critique | High | High | Evidence discipline: named principle/trade-off + concrete alternative required; no principle = not a finding |
| Intentional design choices flagged as violations | Medium | Medium | Phase 4 devil's advocate specifically asks for false positives caused by intentional design |
| Migration recommendations too expensive for sprint scope | High | Medium | Migration Cost column surfaced in tasks; high-cost items noted in user handoff |
| Agent-config architecture concerns overlooked | Medium | High | Phase 2 prompt explicitly covers commands/, skills/, agents/, prompts/, scripts/ |
| Schema drift from audit-* family | Low | High | Schema declared as "core + architecture extensions" in command; Verification Plan step 2 checks this |

## Security Considerations

- `$ARGUMENTS` validated as path(s) in Phase 1 before use in any Codex exec prompt
- Codex exec prompts must not instruct Codex to run shell commands beyond reading
  files and writing to `docs/architecture/`
- Command file flows into agent system prompts — review for unintended scope expansion
- Sprint tasks will be executed by agents — task descriptions must be specific enough
  to be safe; no "refactor everything in X" broad tasks
- `docs/architecture/` artifacts may reveal structural weaknesses; P1-B README should
  note to review before committing to public repos

## Observability & Rollback

- Verification: invoke `/audit-architecture` on this repo; confirm
  `docs/architecture/NNN-*.md` files and `docs/sprints/SPRINT-NNN.md` are produced;
  verify sprint is consumable by `/sprint-work`; verify finding schema is consistent
  across all phases
- Rollback: text files only; `git restore` or `git revert` as appropriate

## Documentation

- [ ] P1-A: Add `audit-architecture` to `README.md` with invocation example
- [ ] P1-B: Create `docs/architecture/README.md` with naming convention and schema

## Dependencies

- SPRINT-001 (completed) — commands/ architecture
- SPRINT-002 (completed) — docs/ conventions, sprint template
- SPRINT-003 (completed) — ledger skill integration
- SPRINT-004 (completed) — `audit-security` as pattern template
- SPRINT-005 (planned) — schema extension pattern declaration

## Open Questions

None — all design questions resolved during planning and interview.

## Devil's Advocate & Security Review: Critiques Addressed

### Incorporated

| Source | Finding | Action |
|---|---|---|
| Devil's Advocate | Inherent-limitations language too weak for architecture's unique subjectivity risk | Strengthened Overview: explicit note that findings are hypotheses, not implementation-ready tasks |
| Devil's Advocate | Phase 1 discovery too shallow before findings allowed | Added minimum: "read at least 5 representative files before generalizing a pattern" |
| Devil's Advocate | Pre-existing artifact collision not handled | Added Phase 1 check: if AUDIT_NNN artifacts exist, warn and stop |
| Devil's Advocate | High + Migration Cost=High tasks create premature work orders | Added note: "requires team alignment" for these tasks; user handoff updated |
| Devil's Advocate | No-findings task masks review depth | No-findings task now requires: approximate files read, areas of most scrutiny |
| Devil's Advocate | "Investigate [issue]" not documented as valid Alternative | Added to Alternative column description |
| Devil's Advocate | Sprint manufacturing unjustified certainty | User handoff now explicitly says "validate findings against team knowledge before executing" |
| Security Review (SR-001) | `$ARGUMENTS` path validation not specific enough | DoD: validate each path confirms it exists via filesystem check |
| Security Review (SR-003) | Codex exec prompts need explicit write-scope restriction | DoD: Phase 2 and Phase 4 prompts must restrict writes to `docs/architecture/` |
| Security Review (SR-005) | Sprint tasks could be too broad for safe agent execution | DoD: tasks scoped to specific enumerable changes |

### Rejected

| Source | Critique | Reason Rejected |
|---|---|---|
| Devil's Advocate | "Reject this sprint plan" | Overreach; `audit-security` faces identical subjectivity challenges. Evidence discipline + devil's advocate pass is the correct mitigation |
| Devil's Advocate | Unusual/flat repos should fail closed (not warn) | Explicitly rejected by user in Phase 4 interview — every repo has architecture |
| Devil's Advocate | "Independence mechanism brittle" | Known shared limitation across all audit commands; not new or blocking |
| Devil's Advocate | "Sprint output too eager; ADRs needed first" | Deliberate family design decision; sprint output contract is the audit-* value proposition |
| Devil's Advocate | DoD needs quality gates (false-positive rate, end-to-end quality) | Structural DoD is the correct level; quality gates on subjective content are unverifiable |
| Devil's Advocate | Multi-path audits should be removed | A convenience feature; scope risks are mitigated by the compact convention and simple merging rule |

## Assumptions

- `audit-security` remains the canonical base template for the `audit-*` family
- Agent-config architecture review is built into default prompts (not a separate mode)
- README documentation is P1; sprint success is not blocked by its absence
