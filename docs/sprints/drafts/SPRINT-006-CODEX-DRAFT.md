# Sprint 006 Codex Draft: `audit-architecture` Command

## Sprint Objective
Add `commands/audit-architecture.md` as the next `audit-*` family command, reusing the proven 5-phase dual-agent workflow from `audit-security` while adapting the review criteria and finding schema for architectural decisions, tradeoffs, and migration planning.

## Problem Statement
SPRINT-004 established the core `audit-*` workflow with `audit-security`: orient on scope, run independent Claude and Codex reviews, synthesize findings, pressure-test the synthesis with a Codex devil's advocate pass, and emit a standard executable sprint instead of a bespoke report. SPRINT-005 extended that family and made schema extension an explicit pattern.

The next gap is architecture review. This repository needs a command that can inspect both general software architecture and agent-config-specific architecture, surface questionable structural choices, and turn those findings into actionable sprint work rather than abstract commentary. That means the value of this sprint is not inventing a new workflow. It is preserving family consistency while making architecture findings concrete, evidence-based, and migration-aware.

## Guiding Principles
- Reuse the established `audit-*` workflow instead of introducing architecture-specific orchestration.
- Keep architecture findings anchored to named patterns, principles, tradeoffs, and observable repository structure rather than taste.
- Make the command useful in both ordinary application repos and this agent-config repo shape.
- Preserve the `/sprint-work` output contract by producing a standard `docs/sprints/SPRINT-NNN.md`.
- Favor the smallest viable scope: author the command well before expanding documentation or adding related audit variants.

## Scope

### In Scope
1. Add `commands/audit-architecture.md` with the same 5-phase audit workflow used by the rest of the `audit-*` family.
2. Define an architecture-specific finding schema that extends the core audit schema with columns for architectural principle/pattern tension, alternative approach, and migration impact.
3. Direct intermediate artifacts to `docs/architecture/`.
4. Make the command explicitly cover both general software architecture and agent-config architecture when `commands/`, `skills/`, or `agents/` are present.
5. Define edge-case handling for weakly structured repos, single-reviewer synthesis, and opinion-vs-evidence findings.

### Out of Scope
1. Modifying existing `audit-security`, `audit-design`, or `audit-accessibility` behavior beyond using them as references.
2. Introducing an ADR workflow, architecture scoring system, or separate remediation command.
3. Changing `/sprint-work`, the ledger model, or sprint document format.
4. Adding architecture-specific automation, linters, or repository analysis scripts.
5. README updates unless they are clearly needed to unblock command usability.

## Key Decisions
1. **Mirror `audit-security` exactly at the workflow level**: architecture review keeps the same 5-phase structure rather than inventing a bespoke discovery flow.
2. **Use schema extension, not replacement**: preserve the core audit columns and add architecture-specific metadata that makes findings less subjective.
3. **Warn and continue when architecture is weak or unclear**: unlike no-UI design/accessibility audits, every repo has architecture, even if it is ad hoc.
4. **Bake in agent-config awareness**: do not add a special mode; instead, instruct reviewers to examine `commands/*.md`, `skills/*/SKILL.md`, `agents/**/*.md`, and related prompt/data flow when present.
5. **Treat migration impact as first-class**: architecture findings should include effort implications so the final sprint can prioritize refactors realistically.

## Architecture

```text
audit-architecture [$ARGUMENTS = optional path/scope]

Phase 1: Orient
  -> Validate scope from $ARGUMENTS or cwd
  -> Identify architectural boundaries, major modules, repo shape
  -> Determine next SPRINT-NNN
  -> Create docs/architecture/

Phase 2: Independent Reviews (parallel)
  -> Codex: write docs/architecture/AUDIT_NNN-CODEX.md
  -> Claude: write docs/architecture/AUDIT_NNN-CLAUDE.md

Phase 3: Synthesis
  -> Verify review files exist and are non-empty
  -> Deduplicate overlapping findings
  -> Preserve evidence, principles, alternatives, migration impact
  -> Write docs/architecture/AUDIT_NNN-SYNTHESIS.md

Phase 4: Devil's Advocate
  -> Codex attacks synthesis for false positives, bad alternatives,
     migration-cost mistakes, and missed architectural risks
  -> Claude incorporates valid challenges and documents rejections

Phase 5: Sprint Output
  -> Produce docs/sprints/SPRINT-NNN.md
  -> Map findings into P0, P1, Deferred work
  -> /ledger add NNN "Architecture: [scope]"
  -> User reviews ordering and runs /sprint-work NNN
```

## Finding Schema

All intermediate architecture audit artifacts should use this table:

```markdown
| ID | Severity | Title | Location | Pattern/Principle | Why It Matters | Alternative | Migration Impact | Recommended Fix | Evidence/Notes |
|----|----------|-------|----------|-------------------|----------------|-------------|------------------|-----------------|----------------|
| C001 | High | Command workflows duplicated across audit family | commands/ | DRY / consistency tension | Divergent behavior increases maintenance risk | Shared workflow template or stricter family conventions | Medium | Normalize shared sections and tighten command invariants | audit-security/design/accessibility have parallel structure with repeated constraints |
```

- `Pattern/Principle`: the architectural pattern, principle, or named tradeoff in tension.
- `Alternative`: the better approach being proposed, not just a complaint.
- `Migration Impact`: `Low`, `Medium`, or `High` estimate of change cost and coordination risk.
- Core severity still reflects impact, breadth, operational risk, and maintainability consequences, not reviewer agreement.
- Agreement between Claude and Codex raises confidence, not severity.

## Use Cases
1. **General repo architecture audit**: review module boundaries, layering, coupling, data flow, and dependency direction in a normal application codebase.
2. **Agent-config architecture audit**: inspect how commands, skills, agents, prompts, and scripts interact, including prompt flow and duplication across command files.
3. **Targeted subsystem review**: scope the audit to a path such as `commands/` or `scripts/` and produce a sprint for that slice.
4. **Pre-refactor planning**: identify structural problems, concrete alternatives, and migration impact before a broad cleanup effort.

## Implementation Plan

### P0-A: Author `commands/audit-architecture.md`
**Goal**: Create the command file with complete workflow instructions, architecture-specific categories, and a schema that keeps findings actionable.

**Files:**
- `commands/audit-architecture.md`
- `commands/audit-security.md`
- `docs/sprints/README.md`
- `docs/sprints/SPRINT-004.md`
- `docs/sprints/SPRINT-005.md`

**Tasks:**
- [ ] Add `commands/audit-architecture.md` with valid single-line `description:` frontmatter compatible with Gemini conversion.
- [ ] Mirror the same five phases used by `audit-security`: Orient, Independent Reviews, Synthesis, Devil's Advocate, Sprint Output.
- [ ] Validate `$ARGUMENTS` as a path before use in any shell string and ensure every `codex exec` prompt is self-contained with resolved literals.
- [ ] Create `docs/architecture/` as the runtime artifact directory in Phase 1.
- [ ] Define architecture review categories for both reviewers, including:
  - system boundaries and module decomposition
  - dependency direction and layering
  - coupling, cohesion, and shared abstractions
  - configuration and data flow
  - extensibility and change isolation
  - operational complexity and migration constraints
  - agent-config-specific structure across `commands/`, `skills/`, `agents/`, `prompts/`, and `scripts/` when those paths exist
- [ ] Require each finding to cite a named pattern, principle, or architectural tension and propose a concrete alternative.
- [ ] Require `Migration Impact` for every finding so remediation can be prioritized realistically.
- [ ] Specify warn-and-continue behavior when no recognizable formal architecture pattern exists in scope.

**Acceptance:**
- `commands/audit-architecture.md` exists and is structurally parallel to the rest of the `audit-*` family.
- The command is explicit about both general software architecture and agent-config-specific review concerns.
- The finding schema includes `Pattern/Principle`, `Alternative`, and `Migration Impact`.
- The command uses `docs/architecture/` for intermediate artifacts.

### P0-B: Define Reliable Synthesis and Devil's Advocate Behavior
**Goal**: Keep architecture findings disciplined enough that the workflow produces actionable output instead of opinion-heavy prose.

**Files:**
- `commands/audit-architecture.md`
- `commands/audit-security.md`
- `docs/sprints/SPRINT-004.md`
- `docs/sprints/SPRINT-005.md`

**Tasks:**
- [ ] Require synthesis to deduplicate overlapping findings without collapsing distinct tradeoffs or different migration paths.
- [ ] Document single-reviewer fallback behavior if one review file is missing or empty.
- [ ] Require synthesis to retain only findings grounded in observed structure, named principles, or explicit tradeoff reasoning.
- [ ] Instruct Codex devil's advocate to challenge:
  - false positives caused by subjective preference
  - principles cited without evidence
  - impractical or over-engineered alternatives
  - misestimated migration impact
  - missing architecture risks or structural bottlenecks
- [ ] Require explicit reasoning for rejected devil's advocate challenges.

**Acceptance:**
- The command distinguishes architecture evidence from personal preference.
- Single-agent degradation is documented and surfaced prominently.
- Devil's advocate review attacks the quality of the architectural reasoning, not just severity labels.

### P0-C: Define Sprint Output Contract for Architecture Work
**Goal**: Ensure the final output is a standard sprint document that `/sprint-work` can consume without special handling.

**Files:**
- `commands/audit-architecture.md`
- `docs/sprints/README.md`

**Tasks:**
- [ ] Require Phase 5 to produce `docs/sprints/SPRINT-NNN.md` using the standard sprint template structure.
- [ ] Map findings to priorities using architecture-aware judgment:
  - P0 for high-severity structural risks or blockers to safe change
  - P1 for meaningful maintainability and modularity improvements
  - Deferred for lower-value cleanups or high-cost migrations not justified this sprint
- [ ] Require each sprint task to include the finding ID, affected location, principle in tension, recommended change, and verification guidance.
- [ ] Define a no-findings output path with a single verification task documenting scope, date, and review method.
- [ ] Register the sprint with `/ledger add NNN "Architecture: [scope]"`.
- [ ] Instruct the user to review task ordering before running `/sprint-work NNN`, since architecture work often has sequencing dependencies.

**Acceptance:**
- The final output remains compatible with `/sprint-work`.
- Architecture findings become implementation tasks, not essay-style recommendations.
- The no-findings path still produces a verifiable sprint artifact.

### P1: Document the Command in `README.md`
**Goal**: Make the new command discoverable once the workflow itself is complete.

**Files:**
- `README.md`

**Tasks:**
- [ ] Add `audit-architecture` to the command matrix and examples.
- [ ] Describe its relationship to the existing `audit-*` family and `/sprint-work`.
- [ ] Keep examples aligned across Claude, Codex, and Gemini invocation styles.

**Acceptance:**
- A new user can discover and invoke `audit-architecture` from `README.md`.
- Documentation language matches the existing command descriptions.

### Deferred
- Refactoring the full `audit-*` family into a shared command generator or template system
- Adding architecture-specific scoring rubrics or weighted prioritization formulas
- Producing ADRs as a secondary artifact
- Automated architecture graph extraction or code-mapping tools

## Files Summary

| File | Action | Purpose |
|---|---|---|
| `commands/audit-architecture.md` | Create | Define the dual-agent architecture audit workflow |
| `README.md` | Modify (P1) | Document the new command and invocation examples |
| `commands/audit-security.md` | Reference only | Canonical `audit-*` workflow template |
| `docs/sprints/README.md` | Reference only | Canonical sprint output format |
| `docs/sprints/SPRINT-004.md` | Reference only | Original `audit-security` design decisions |
| `docs/sprints/SPRINT-005.md` | Reference only | Schema extension convention for the `audit-*` family |

## Acceptance Criteria
- [ ] `commands/audit-architecture.md` exists with valid frontmatter and a complete 5-phase workflow.
- [ ] Intermediate artifacts are written to `docs/architecture/`.
- [ ] The finding schema extends the core audit schema with `Pattern/Principle`, `Alternative`, and `Migration Impact`.
- [ ] The command supports both general software architecture review and agent-config-specific architecture review.
- [ ] Every `codex exec` invocation avoids `--model` and `--full-auto` flags and uses validated, resolved scope literals.
- [ ] The command documents single-reviewer fallback and warn-and-continue behavior for loosely structured repos.
- [ ] Phase 5 outputs a standard `docs/sprints/SPRINT-NNN.md` consumable by `/sprint-work`.
- [ ] Ledger registration uses `/ledger add NNN "Architecture: [scope]"`.

## Verification Plan
1. Compare `commands/audit-architecture.md` against `commands/audit-security.md` and confirm the same phase ordering and execution contract.
2. Inspect the finding schema and confirm it preserves the core audit columns while adding architecture-specific metadata.
3. Read every `codex exec` prompt and confirm:
   - no `--model` flag
   - no `--full-auto` flag
   - no raw `$ARGUMENTS` interpolation
   - resolved scope and sprint number are embedded literally
4. Run a manual phase-to-phase read-through and verify each phase produces the artifact the next phase consumes.
5. Check edge-case coverage for:
   - flat or scripts-only repos
   - no recognizable formal architecture pattern
   - missing or empty reviewer output from one agent
   - findings that name a principle but lack evidence
   - findings whose proposed alternative is stronger than the current design but too expensive for the sprint
6. Compare the final sprint output requirements against `docs/sprints/README.md` and confirm compatibility.

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Architecture findings become subjective style critiques instead of actionable findings | Medium | High | Require named principles, observed evidence, and concrete alternatives in every finding |
| The command drifts from the rest of the `audit-*` family and becomes harder to maintain | Low | High | Use `audit-security` as the canonical structural reference and keep the same 5-phase flow |
| Migration recommendations are technically sound but too expensive for the sprint | High | Medium | Add `Migration Impact` to the schema and use it in priority mapping |
| Agent-config-specific architecture concerns are overlooked in a repo like this one | Medium | High | Explicitly instruct reviewers to inspect prompt flow and structure across `commands/`, `skills/`, `agents/`, `prompts/`, and `scripts/` |
| Weakly structured repos yield thin or noisy findings | Medium | Medium | Warn and continue, but require findings to be evidence-backed and scoped to concrete structural issues |

## Definition of Done
- [ ] `commands/audit-architecture.md` is authored and internally consistent.
- [ ] The command preserves the established dual-agent `audit-*` workflow.
- [ ] The architecture finding schema is defined and actionable.
- [ ] The command produces `docs/architecture/` artifacts and a standard sprint output.
- [ ] Edge cases and fallback behavior are explicitly documented.
- [ ] Manual verification confirms the workflow remains consumable by `/sprint-work`.
- [ ] Optional README documentation is either completed or intentionally deferred without blocking command usability.

## Assumptions
- The existing `audit-security` command remains the canonical base template for the `audit-*` family.
- Agent-config architecture review should be built into the default prompts rather than introduced as a separate command mode or flag.
- README documentation is useful but not required to consider the sprint successful if the command itself is complete and internally consistent.
