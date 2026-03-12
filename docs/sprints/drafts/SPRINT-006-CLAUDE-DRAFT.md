# Sprint 006: `audit-architecture` Command

## Overview

SPRINT-004 established the `audit-*` command family with `audit-security`. SPRINT-005
extends it with `audit-design` and `audit-accessibility`. This sprint delivers the fourth
member: `audit-architecture`.

`audit-architecture` applies the proven 5-phase dual-agent workflow to architectural
review: examining structural decisions, coupling patterns, separation of concerns, naming
conventions, data flow, and extensibility trade-offs. It produces an executable sprint of
architecture improvement tasks, each anchored to a named principle or observable
trade-off — not architectural opinion.

The key design challenge for this command vs. `audit-security` is that architecture is
inherently more subjective. The finding schema addresses this by requiring every finding
to cite a named principle (SOLID, DRY, separation of concerns, etc.) or a concrete,
observable trade-off — and to propose a specific alternative approach. Findings without
a named anchor are not valid findings.

**Inherent limitations**: LLM architectural review cannot replace domain knowledge
about runtime behavior, team conventions, or organizational constraints. The output is a
structured starting point for team discussion, not a mandate to refactor. Not every
finding will be worth acting on; that judgment belongs to the engineering team.

## Use Cases

1. **New-repo architecture review**: run after initial scaffolding to identify structural
   decisions worth revisiting early, before they become load-bearing.
2. **Pre-refactor analysis**: scope to a specific directory or module before a planned
   refactor; surface hidden coupling or design tensions.
3. **Agent-config self-audit**: review how commands, skills, and agents are structured
   and interact; identify over-coupling, redundant patterns, or missing abstractions.
4. **Periodic architecture health check**: run quarterly on a growing codebase to surface
   drift from original design intent.

## Architecture

```
audit-architecture [$ARGUMENTS = optional path(s)]

Phase 1: Orient
  → Validate scope ($ARGUMENTS or cwd; supports multiple paths)
  → Survey structure: entry points, module boundaries, dependency graph
  → Determine next SPRINT-NNN number
  → Create docs/architecture/ if needed
  → Note: architecture is always present — warn on unusual scope, do not stop

Phase 2: Independent Reviews (parallel)
  → Codex: write docs/architecture/NNN-CODEX.md  (background)
  → Claude: write docs/architecture/NNN-CLAUDE.md (simultaneously)
  → Both use the architecture finding schema (base + Pattern + Alternative + Migration Cost)

Phase 3: Synthesis
  → Verify both files non-empty; deduplicate; calibrate severity
  → Write docs/architecture/NNN-SYNTHESIS.md

Phase 4: Devil's Advocate (Codex)
  → Codex attacks synthesis → docs/architecture/NNN-DEVILS-ADVOCATE.md
  → Claude incorporates valid challenges; documents rejections

Phase 5: Sprint Output
  → Produce docs/sprints/SPRINT-NNN.md
  → Severity → priority: Critical/High=P0, Medium=P1, Low=Deferred
  → /ledger add NNN "Architecture: [scope]"
  → User runs /sprint-work NNN
```

## Finding Schema

The `audit-architecture` finding schema extends the `audit-*` base schema with
architecture-specific columns:

```
| ID | Severity | Title | Location | Pattern/Principle | Alternative | Migration Cost | Why It Matters | Evidence/Notes |
```

- **ID prefix**: Claude = `A`, Codex = `C`, Synthesis = `S`
- **Pattern/Principle**: the named architectural rule or observable trade-off in tension.
  Examples: `SOLID:SRP` (Single Responsibility), `DRY`, `Separation of Concerns`,
  `Low Coupling`, `High Cohesion`, `YAGNI`, `Explicit over Implicit`, or for agent-config:
  `Command/Skill Boundary`, `Agent Scope Creep`, `Prompt Composability`.
  If no named principle applies, describe the trade-off explicitly (e.g., "Coupling:
  phase-transition logic embedded in output formatting").
- **Alternative**: a specific, concrete alternative approach — not "refactor this" but
  "extract the phase-transition logic into a separate step that returns structured data,
  then let the formatting layer consume it."
- **Migration Cost**: `Low` (text change, rename, small extraction), `Medium` (moderate
  restructure, touching multiple files), `High` (significant redesign, breaking changes).
- **Severity anchors**:
  - Critical: prevents correct behavior or makes the system unmaintainable in its current
    trajectory
  - High: significantly impedes extensibility, causes repeated defects, or creates
    systematic blind spots
  - Medium: notable friction, inconsistency, or a pattern that will degrade over time
  - Low: minor improvement, style preference backed by a named principle

**Evidence discipline**: a finding without a named `Pattern/Principle` or without a
concrete `Alternative` is not a valid finding. Both reviewers must be instructed to
skip opinion-only observations.

## Implementation Plan

### P0: Must Ship

#### P0-A: `commands/audit-architecture.md`

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
- Validate scope from `$ARGUMENTS` (supports multiple space-separated paths) or default
  to cwd; store resolved paths — do not interpolate raw `$ARGUMENTS` into shell strings
- Survey the scope:
  - `git log --oneline -10` for recent structural changes
  - Identify module boundaries, entry points, key config files
  - For agent-config repos: identify `commands/*.md`, `skills/`, `agents/` — these
    define the architecture of the agent system
  - For application repos: identify service boundaries, data flow, dependency graph
- Architecture is always present — if scope seems unusual or flat, note it but do not
  stop; warn that findings may be limited
- Determine next SPRINT-NNN; create `docs/architecture/` if needed

**Phase 2 — Independent Review requirements:**

Launch Codex in background:
```bash
codex exec "Perform a thorough architecture review of [RESOLVED_SCOPE]. \
  Write all findings to docs/architecture/NNN-CODEX.md using this \
  exact table format: \
  | ID | Severity | Title | Location | Pattern/Principle | Alternative | \
  Migration Cost | Why It Matters | Evidence/Notes | \
  where ID uses prefix C (e.g. C001, C002). \
  Review these categories: \
  (1) Module boundaries and separation of concerns — are responsibilities \
  clearly separated? Is business logic mixed with infrastructure? \
  (2) Coupling and cohesion — are components tightly coupled where they \
  should be independent? Do related things live together? \
  (3) Naming and conventions — are names consistent, intention-revealing, \
  and following a documented convention? \
  (4) Data flow and state management — is data flow easy to trace? \
  Is state centralized or scattered? \
  (5) Extensibility and DRY — is there unnecessary duplication? \
  Are extension points well-defined or does new behavior require \
  copy-paste? \
  (6) YAGNI and over-engineering — is there abstraction without current \
  use? Configurability no one needs? \
  (7) For agent-config repos: how are commands/skills/agents structured? \
  Is the boundary between commands (user-facing workflows) and skills \
  (reusable components) clear? Are agents scoped appropriately? \
  Is the invocation chain traceable? \
  Every finding MUST include a named Pattern/Principle and a specific \
  Alternative — skip observations that are pure opinion without a \
  named principle. Rate severity on: does this prevent correct behavior, \
  impede extensibility, or create systematic debt? \
  Do not read or reference any other review file."
```

Claude writes its own independent review to `docs/architecture/NNN-CLAUDE.md`
simultaneously, covering the same 7 categories with the same schema (ID prefix `A`).
Extra scrutiny for agent-config repos: the command/skill/agent boundary, invocation
chain legibility, prompt composability.

Wait for Codex to finish before Phase 3.

**Phase 3 — Synthesis requirements:**
- Verify both files non-empty (single-agent warning if one missing)
- Deduplicate: same structural issue appearing in both = higher confidence, not higher
  severity; when merging, preserve the most specific `Alternative` from either reviewer
- When the same pattern-violation appears across many locations, create one finding and
  document extent in Evidence/Notes (e.g., "Applies to all 5 commands/*.md files")
- Calibrate severity on evidence: impact on maintainability, extensibility, defect rate
- Write `docs/architecture/NNN-SYNTHESIS.md`

**Phase 4 — Devil's Advocate requirements:**
```bash
codex exec "Read docs/architecture/NNN-SYNTHESIS.md. Attack it. Write to \
  docs/architecture/NNN-DEVILS-ADVOCATE.md covering: \
  (1) False positives — 'violations' that are intentional design decisions \
  appropriate for this project's scale or constraints. \
  (2) Severity miscalibrations — findings rated too high or too low. \
  (3) Missing findings — structural issues both reviewers missed. \
  (4) Alternatives that are impractical or create worse problems. \
  Cite finding ID for every challenge."
```

Claude incorporates valid challenges; documents every rejected challenge with reasoning
in "Rejected Challenges" section of `NNN-SYNTHESIS.md`.

**Phase 5 — Sprint Output requirements:**
- Title: `Architecture Audit: [scope] ([YYYY-MM-DD])`
- Each task: finding ID, location, pattern/principle, issue description, specific
  alternative approach, migration cost, verification step
- Severity → priority: Critical/High=P0, Medium=P1, Low=Deferred
- No-findings: single P0 "Verify no findings" task documenting scope, date,
  categories reviewed, reviewer agents
- Register: `/ledger add NNN "Architecture: [scope]"`
- Before `/sprint-work`: note that high-migration-cost P0 tasks may need sequencing;
  some architectural changes will touch shared boundaries and should be coordinated
- Instruct user: review task ordering and migration costs, then `/sprint-work NNN`

**Tasks:**
- [ ] Write `commands/audit-architecture.md` with complete 5-phase workflow
- [ ] Verify all Codex exec prompts are self-contained (NNN literal, no `--model`/
      `--full-auto`, no raw `$ARGUMENTS` interpolation)
- [ ] Verify finding schema includes `Pattern/Principle`, `Alternative`,
      `Migration Cost` columns
- [ ] Verify evidence discipline (no findings without named principle + alternative)
      is documented in the Phase 2 prompt to both agents
- [ ] Verify warn-and-continue (not stop) behavior for unusual scope in Phase 1
- [ ] Verify sprint output follows `docs/sprints/README.md` template
- [ ] Verify `/ledger add` uses correct skill syntax
- [ ] Manual read-through: Phase 1 → 2 → 3 → 4 → 5 produces what the next phase
      consumes

**Acceptance:**
- `commands/audit-architecture.md` exists with valid single-line `description:`
  frontmatter
- Phase 2 runs Claude and Codex in parallel
- Finding schema includes `Pattern/Principle`, `Alternative`, `Migration Cost` columns
- Phase 1 warns (does not stop) if scope seems unusual
- Phase 5 output is a valid sprint document consumable by `/sprint-work`
- No `--model`/`--full-auto` flags in any Codex exec call

### P1: Ship If Capacity Allows

#### P1-A: `README.md` Update

Add `audit-architecture` to `README.md`:
- Brief description and invocation example
- Relationship to the `audit-*` family and `/sprint-work`
- Note on inherent subjectivity and human judgment requirement

**Acceptance:**
- Users can discover `audit-architecture` without reading the source file

#### P1-B: `docs/architecture/README.md`

Lightweight reference for the `docs/architecture/` directory:
- Purpose and naming convention (NNN matches sprint number)
- Finding schema with all columns documented
- Note: these files may reveal design decisions; review before committing to
  public repos

### Deferred

- `audit-deps` and other `audit-*` commands — `audit-architecture` establishes
  whether the family pattern scales to subjective domains before adding more
- Linear/Jira sync for architecture findings — reuse `sprint-plan`'s tool sync
  pattern when needed
- Interactive architecture diagram generation — out of scope for command files

## Files Summary

| File | Action | Purpose |
|------|--------|---------|
| `commands/audit-architecture.md` | Create | 5-phase dual-agent architecture audit (P0-A) |
| `README.md` | Modify | Discoverability and invocation examples (P1-A) |
| `docs/architecture/README.md` | Create | Naming convention and finding schema (P1-B) |

## Definition of Done

- [ ] `commands/audit-architecture.md` exists with valid single-line `description:`
      frontmatter
- [ ] Phase 2: Codex launched in background; Claude reviews simultaneously
- [ ] Finding schema includes `Pattern/Principle`, `Alternative`, `Migration Cost`
      columns with documented evidence discipline
- [ ] Phase 1: warn-and-continue (not stop) if scope seems unusual or flat
- [ ] Phase 1: validates `$ARGUMENTS` as path(s); raw argument never interpolated
      into Codex exec shell strings
- [ ] Phase 3: verifies both review files non-empty; single-agent warning if one missing
- [ ] Phase 4: Codex devil's advocate runs; valid challenges incorporated; rejections
      documented with reasoning
- [ ] Phase 5: follows `docs/sprints/README.md` template
- [ ] Phase 5: severity mapping documented (Critical/High=P0, Medium=P1, Low=Deferred)
- [ ] Phase 5: no-findings produces "Verify no findings" P0 task (not empty sprint)
- [ ] Phase 5: `/ledger add NNN` completed (or user instructed to run manually)
- [ ] Phase 5: user instructed to review task ordering + migration costs, then
      `/sprint-work NNN`
- [ ] No `--model`/`--full-auto` flags in any Codex exec call
- [ ] No raw `$ARGUMENTS` interpolation in any Codex exec prompt
- [ ] Manual read-through: each phase produces what the next phase consumes
- [ ] Edge-case read-through: (1) no scope arg, (2) path-scoped audit, (3) overlapping
      findings, (4) no findings, (5) flat/unusual repo structure

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Findings become subjective opinions masquerading as architecture | High | High | Evidence discipline: every finding must cite a named Pattern/Principle and a specific Alternative |
| Both reviewers agree on a "violation" that is actually an intentional design choice | Medium | Medium | Phase 4 devil's advocate specifically asks for intentional-design false positives |
| Architecture audit produces too many findings (scope creep in the audit itself) | Medium | Medium | Phase 5 simplest-viable filter: group pattern-level findings, not instance-level |
| NNN collision if multiple audits run same day | Low | Low | Phase 1 always checks current max and increments |
| Command file too long for Gemini TOML | Low | Low | Monitor; `audit-security` is already long and works |

## Security Considerations

- Command files flow into agent system prompts — review for unintended scope expansion
- `$ARGUMENTS` validated as path(s) in Phase 1 before use in any Codex exec prompt
- Codex exec prompts must not instruct Codex to run shell commands beyond reading files
  and writing to `docs/architecture/`
- Sprint tasks will be executed by agents — task descriptions must be specific enough
  to be safe (no "refactor everything in X" tasks)
- `docs/architecture/` artifacts may reveal structural weaknesses; note this in P1-B
  README

## Observability & Rollback

- Verification: invoke `/audit-architecture` on this repo; confirm
  `docs/architecture/NNN-*.md` files are produced and the sprint document is
  consumable by `/sprint-work`; verify finding schema is consistent across all phases
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

1. **Warn-and-continue vs. stop for unusual scope**: for `audit-design`/
   `audit-accessibility`, no UI files = stop. For `audit-architecture`, any repo
   has architecture — proposal is warn-and-continue. Is this correct?
   → Leaning yes: architecture is always present; even a flat scripts directory
   has architectural decisions worth reviewing.

2. **Evidence discipline strictness**: should the command instruct agents to skip
   opinion-only findings entirely, or include them with a lower severity cap (Low)?
   → Proposal: skip entirely — a finding without a named principle or concrete
   alternative creates noise and dilutes actionable findings.
