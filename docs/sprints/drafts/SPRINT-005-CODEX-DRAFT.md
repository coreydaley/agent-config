# Sprint 005 Codex Draft: `audit-design` + `audit-accessibility` Commands

## Sprint Objective
Add `commands/audit-design.md` and `commands/audit-accessibility.md` as the next two commands in the `audit-*` family, each following the proven 5-phase dual-agent workflow from `commands/audit-security.md` and producing a standard `docs/sprints/SPRINT-NNN.md` remediation sprint.

## Problem Statement
SPRINT-004 established the repo's first audit command, `audit-security`, and in doing so proved a reusable workflow shape: orient on scope, run independent Claude and Codex reviews, synthesize findings, pressure-test the synthesis with a Codex devil's advocate pass, and emit an executable sprint instead of a bespoke report.

The next gap is coverage outside security. This repository now needs the same planning-grade audit workflow for two adjacent concerns:
- design quality and UX coherence
- accessibility compliance and inclusive interaction quality

The intent is explicit that both commands should remain part of the same family, keep the same output contract, and avoid sharing artifact directories with security work. That means this sprint is primarily command authoring and workflow adaptation, not infrastructure invention.

## Guiding Principles
- Reuse the `audit-security` workflow shape rather than inventing a second audit architecture.
- Keep both commands self-contained, readable top-to-bottom, and deterministic for the executing agent.
- Preserve the standard sprint output contract so `/sprint-work` can consume the final artifact unchanged.
- Separate artifact storage by audit domain so working files stay semantically accurate and easy to scan.
- Let domain standards drive the review criteria: recognized UI/UX heuristics for design and WCAG 2.1/2.2 for accessibility.

## Scope

### In Scope
1. Add `commands/audit-design.md` with a complete 5-phase audit workflow parallel to `audit-security`.
2. Add `commands/audit-accessibility.md` with a complete 5-phase workflow and explicit WCAG-driven review criteria.
3. Define purpose-specific artifact directories for the new commands.
4. Reuse a common findings table shape so synthesis and final sprint generation remain consistent across the `audit-*` family.
5. Update `README.md` so the new commands are discoverable across Claude, Codex, and Gemini invocation styles.

### Out of Scope
1. Modifying `commands/audit-security.md` beyond what is needed as a reference.
2. Creating a shared audit orchestration script or new command runtime.
3. Building automated UI testing, accessibility scanning, or design linting tooling.
4. Changing `/sprint-work` or the sprint ledger model.
5. Adding more `audit-*` commands beyond design and accessibility.

## Key Decisions
1. **Two new commands, same workflow contract**: both commands should mirror the 5-phase structure already used by `audit-security`.
2. **Separate artifact directories by domain**: `audit-design` writes to `docs/design/`; `audit-accessibility` writes to `docs/accessibility/`.
3. **Standard sprint output remains the final product**: each command emits `docs/sprints/SPRINT-NNN.md`, not a domain-specific remediation format.
4. **Shared finding schema, domain-specific metadata**: both commands keep the same core table columns as `audit-security`, with explicit room for heuristic or WCAG references in notes or a source-mapping column.
5. **README updates are P1, not blocking command authoring**: match the `audit-security` rollout pattern and keep shipping priority on the command files themselves.

## Implementation Plan

### P0-A: Author `commands/audit-design.md`
**Goal**: Create a design audit command that evaluates UI/UX quality using the same collaborative workflow as `audit-security`, but with design-focused review categories and artifact paths.

**Files:**
- `commands/audit-design.md`
- `commands/audit-security.md`
- `docs/sprints/README.md`

**Tasks:**
- [ ] Add `commands/audit-design.md` with valid single-line `description:` frontmatter compatible with Gemini conversion.
- [ ] Mirror the same five phases used in `audit-security`: Orient, Independent Reviews, Synthesis, Devil's Advocate, Sprint Output.
- [ ] Define scope expectations for UI-bearing projects and explicit behavior for no-UI or minimal-UI scopes.
- [ ] Instruct both reviewers to evaluate layout, typography, spacing, hierarchy, consistency, state design, component reuse, navigation clarity, and design-system adherence.
- [ ] Anchor the command to recognized design heuristics and guidelines such as Nielsen Norman heuristics, Material Design, and Apple HIG without turning the command into a standards dump.
- [ ] Write intermediate artifacts to `docs/design/AUDIT_NNN-*.md`.

**Acceptance:**
- `commands/audit-design.md` exists and is structurally parallel to `commands/audit-security.md`.
- The command clearly distinguishes design review from security review while preserving the same orchestration model.
- Artifact paths are fully specified and live under `docs/design/`.

### P0-B: Author `commands/audit-accessibility.md`
**Goal**: Create an accessibility audit command that evaluates projects against WCAG-driven expectations while preserving the same audit family workflow.

**Files:**
- `commands/audit-accessibility.md`
- `commands/audit-security.md`
- `docs/sprints/README.md`

**Tasks:**
- [ ] Add `commands/audit-accessibility.md` with valid single-line `description:` frontmatter.
- [ ] Reuse the same five-phase audit structure and same final sprint output contract.
- [ ] Instruct both reviewers to assess semantic structure, keyboard navigation, focus order, focus visibility, ARIA use, screen reader support, color contrast, form labeling, error messaging, motion sensitivity, and cognitive load.
- [ ] Treat WCAG 2.1 and 2.2 as the normative references for accessibility findings.
- [ ] Require each accessibility finding to cite the relevant WCAG criterion or principle in the output.
- [ ] Write intermediate artifacts to `docs/accessibility/AUDIT_NNN-*.md`.

**Acceptance:**
- `commands/audit-accessibility.md` exists and is structurally parallel to `commands/audit-security.md`.
- The command makes WCAG reference mandatory and explicit enough for actionable remediation.
- Artifact paths are fully specified and live under `docs/accessibility/`.

### P0-C: Standardize Cross-Command Audit Behavior
**Goal**: Keep the new commands consistent with `audit-security` so the `audit-*` family feels intentional rather than loosely related.

**Files:**
- `commands/audit-design.md`
- `commands/audit-accessibility.md`
- `commands/audit-security.md`
- `docs/sprints/README.md`

**Tasks:**
- [ ] Reuse the same core findings table shape across both commands so synthesis behavior is familiar and deterministic.
- [ ] Define domain-specific severity guidance:
  - design: prioritize issues by user impact, breadth, task interruption, and consistency cost
  - accessibility: prioritize issues by exclusion severity, task blockage, assistive-tech impact, and breadth of affected users
- [ ] Ensure both commands handle scoped audits, multi-path audits, and no-findings results explicitly.
- [ ] Ensure both commands map findings into standard sprint tasks rather than leaving the output as prose-only audit notes.
- [ ] Ensure all `codex exec` examples follow repo constraints: no `--model`, no `--full-auto`, and no raw unvalidated `$ARGUMENTS` interpolation in shell strings.

**Acceptance:**
- Both commands share a recognizable `audit-*` family structure.
- Edge-case behavior is documented instead of implied.
- Final sprint output remains compatible with `/sprint-work`.

### P1: Document the New Commands
**Goal**: Make the new commands discoverable without requiring users to inspect command source files.

**Files:**
- `README.md`

**Tasks:**
- [ ] Add `audit-design` and `audit-accessibility` to the commands overview.
- [ ] Add invocation examples for Claude, Codex, and Gemini.
- [ ] Describe their relationship to `/sprint-work` and the broader `audit-*` family.
- [ ] Keep wording consistent with the existing capability matrix and command examples.

**Acceptance:**
- README users can discover both commands and invoke them correctly.
- The docs present the commands as extensions of the existing audit workflow, not one-off additions.

### Deferred
- Automated browser-based accessibility testing or screenshot-driven design review
- Refactoring `audit-security` and the new commands into a shared template generator
- Additional audit domains such as performance, dependency hygiene, or content quality

## Files Summary

| File | Action | Purpose |
|---|---|---|
| `commands/audit-design.md` | Create | Define the dual-agent design audit workflow |
| `commands/audit-accessibility.md` | Create | Define the dual-agent accessibility audit workflow |
| `README.md` | Modify | Document the new commands and invocation examples |
| `commands/audit-security.md` | Reference only | Canonical workflow template for the `audit-*` family |
| `docs/sprints/README.md` | Reference only | Canonical sprint output format |

## Acceptance Criteria
- [ ] `commands/audit-design.md` exists with valid frontmatter and a complete 5-phase workflow.
- [ ] `commands/audit-accessibility.md` exists with valid frontmatter and a complete 5-phase workflow.
- [ ] Both commands produce a standard `docs/sprints/SPRINT-NNN.md` sprint document.
- [ ] Both commands use artifact directories separate from `docs/security/`.
- [ ] Both commands reuse the same core findings schema as `audit-security`.
- [ ] `audit-accessibility` requires WCAG 2.1/2.2-based references in findings.
- [ ] Edge cases are explicitly handled: scoped audit, multi-path audit, no-UI/no-findings scenarios.
- [ ] README documentation includes both commands and correct agent-specific invocation patterns.

## Verification Plan
1. Structural comparison: read `commands/audit-design.md` and `commands/audit-accessibility.md` against `commands/audit-security.md` and confirm the same phase ordering and output contract.
2. Standards verification:
   - design command references recognized design heuristics and review areas
   - accessibility command references WCAG 2.1/2.2 explicitly
3. Prompt verification: inspect every `codex exec` invocation for forbidden flags, missing context, or raw unvalidated argument interpolation.
4. Artifact-path verification:
   - `audit-design` writes only to `docs/design/`
   - `audit-accessibility` writes only to `docs/accessibility/`
   - final sprint writes to `docs/sprints/SPRINT-NNN.md`
5. Edge-case read-through:
   - repo with no frontend or UI assets
   - scoped path audit
   - multiple scope paths
   - no findings discovered
   - overlapping findings between reviewers
6. Sprint-output verification: confirm both commands require a final sprint shape compatible with `docs/sprints/README.md` and `/sprint-work`.

## Risks and Mitigations
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| The new commands drift from `audit-security` and become inconsistent to maintain | Medium | High | Treat `commands/audit-security.md` as the canonical workflow template and preserve the same five phases |
| Design findings become too subjective to convert into actionable sprint work | Medium | Medium | Require concrete user impact, affected area, and remediation guidance for every finding |
| Accessibility findings cite principles loosely without actionable standards mapping | Medium | High | Require WCAG criterion references in accessibility findings and remediation notes |
| Artifact sprawl across multiple audit types becomes confusing | Low | Medium | Keep one purpose-specific directory per audit type with consistent `AUDIT_NNN-*` naming |
| No-UI repos produce noisy or misleading output | Medium | Medium | Define explicit no-UI behavior during orientation and produce a bounded sprint or scoped no-findings result |

## Definition of Done
- [ ] `commands/audit-design.md` is authored and internally consistent.
- [ ] `commands/audit-accessibility.md` is authored and internally consistent.
- [ ] Both commands preserve the established dual-agent audit workflow shape.
- [ ] Both commands use purpose-specific artifact directories instead of `docs/security/`.
- [ ] Both commands emit a standard sprint document consumable by `/sprint-work`.
- [ ] README documentation is updated for discoverability.
- [ ] Manual read-through passes for full-repo, scoped, and no-findings scenarios.

## Assumptions
- The project-level context requested via `CLAUDE.md` is represented here by the generated [agents/claude/CLAUDE.md](/Users/corey/Code/github.com/coreydaley/agent-config/agents/claude/CLAUDE.md), since no root-level `CLAUDE.md` exists in this repository.
- `commands/audit-security.md` remains the primary structural reference and is not itself part of this sprint's edit scope unless a follow-up sprint chooses to normalize the whole `audit-*` family.
