# Sprint 005: `audit-design` and `audit-accessibility` Commands

## Overview

SPRINT-004 established `audit-security` as the first command in the
`audit-*` family and deferred additional commands pending validation
of the pattern. That pattern has shipped and is working. This sprint
delivers the next two: `audit-design` and `audit-accessibility`.

`audit-design` applies the dual-agent review pattern to UI/UX quality:
does the project's frontend follow established design best practices —
layout, typography, color, component consistency, information hierarchy,
design system adherence? Output is an executable sprint of design
remediation tasks.

`audit-accessibility` applies the same pattern with WCAG 2.1/2.2 as
the normative reference: semantic HTML, ARIA roles, keyboard navigation,
focus management, color contrast ratios, screen reader support, motion
sensitivity, and cognitive load. Output is an executable sprint of
accessibility remediation tasks, each tied to a WCAG success criterion.

Both commands are structurally identical to `audit-security` at the
workflow level: 5-phase, dual-agent (Claude + Codex parallel), finding
schema table, intermediate artifacts in a command-specific directory,
sprint document as final output. The customization is in the finding
categories each phase covers, the normative references each uses, and
the metadata columns in the finding schema.

## Use Cases

1. **Pre-launch design review**: run `audit-design` on a new product
   before release; findings become a sprint of polish tasks.
2. **Accessibility compliance gate**: run `audit-accessibility` before
   a public release or compliance audit; Critical/High WCAG failures
   become P0 sprint tasks.
3. **Component library audit**: scope either command to a specific
   component directory to audit incrementally.
4. **Cross-audit correlation**: run all three `audit-*` commands on
   the same project; each produces its own sprint; execute in
   priority order.

## Architecture

```
audit-design / audit-accessibility [$ARGUMENTS = optional path/scope]

Phase 1: Orient
  → Validate scope ($ARGUMENTS or cwd)
  → Identify frontend files, design tokens, component files
  → Determine next SPRINT-NNN number
  → Create docs/design/ or docs/accessibility/ as needed

Phase 2: Independent Reviews (parallel)
  → Codex: write docs/design/NNN-CODEX.md  (or accessibility/NNN-CODEX.md)
  → Claude: write docs/design/NNN-CLAUDE.md (simultaneously)

Phase 3: Synthesis
  → Read both reviews; deduplicate; calibrate severity
  → Write docs/design/NNN-SYNTHESIS.md

Phase 4: Devil's Advocate (Codex)
  → Codex attacks synthesis → NNN-DEVILS-ADVOCATE.md
  → Claude incorporates valid challenges

Phase 5: Sprint Output
  → Produce docs/sprints/SPRINT-NNN.md
  → Map findings → tasks (Critical/High=P0, Medium=P1, Low=Deferred)
  → /ledger add NNN "Design: [scope]"  (or "Accessibility: [scope]")
  → User runs /sprint-work NNN
```

## Finding Schema

### audit-design finding schema

All intermediate files use:

```
| ID | Severity | Title | Location | Heuristic | Why It Matters | Recommended Fix | Evidence/Notes |
|----|----------|-------|----------|-----------|----------------|-----------------|----------------|
| A001 | High | Short title | path/to/file:line | Nielsen #4 | Impact | Fix | Evidence |
```

**Heuristic** maps findings to a named design principle:
- Nielsen's 10 Usability Heuristics (N#1–N#10)
- Material Design / Apple HIG / platform-specific when relevant
- "Custom" for project-specific design system violations

**ID prefix convention**: Claude = `A`, Codex = `C`, Synthesis = `S`

**Severity levels:** Critical, High, Medium, Low

Severity is assessed on user impact, frequency of encounter, breadth
of affected surface, and severity of degraded experience. A broken
primary navigation is Critical; inconsistent button padding is Low.

### audit-accessibility finding schema

All intermediate files use:

```
| ID | Severity | Title | Location | WCAG | Level | Why It Matters | Recommended Fix | Evidence/Notes |
|----|----------|-------|----------|------|-------|----------------|-----------------|----------------|
| A001 | High | Short title | path/to/file:line | 1.4.3 | AA | Impact | Fix | Evidence |
```

**WCAG** column: WCAG 2.1/2.2 success criterion number (e.g. `1.4.3`)
or `Best Practice` for items beyond WCAG scope.

**Level** column: A, AA, AAA, or `BP` (Best Practice)

Severity mapping to WCAG conformance level:
- Level A violations → Critical (blocking for assistive technology)
- Level AA violations → High (standard compliance requirement)
- Level AAA violations → Medium (enhanced accessibility)
- Best Practice → Low

This mapping is a starting point; override where user impact evidence
warrants a different severity rating.

## Implementation Plan

### P0: Must Ship

#### P0-A: `commands/audit-design.md`

**Files:**
- `commands/audit-design.md` — NEW

**Frontmatter:**
```yaml
---
description: >-
  Dual-agent design audit — Claude and Codex review UI/UX independently,
  synthesize findings, devil's advocate pass, output as executable sprint
---
```

**Phase 1 — Orient:**
- Validate scope from `$ARGUMENTS` or default to cwd
- Identify frontend files: HTML, CSS, JSX/TSX, Vue/Svelte components,
  design tokens, style sheets, Storybook stories
- If no frontend files found in scope: note this prominently in the
  orientation and proceed (the reviewers will note limited scope)
- Determine next SPRINT-NNN; create `docs/design/` if needed

**Phase 2 — Independent Reviews (parallel):**

Codex (background):
```bash
codex exec "Perform a thorough design audit of [RESOLVED_SCOPE]. \
  Write all findings to docs/design/NNN-CODEX.md using this table \
  format: \
  | ID | Severity | Title | Location | Heuristic | Why It Matters | Recommended Fix | Evidence/Notes | \
  where ID uses prefix C (e.g. C001). \
  Cover: (1) Layout and visual hierarchy — spacing, alignment, grid, \
  information density. (2) Typography — font sizes, line height, \
  contrast for readability, hierarchy. (3) Color and visual design — \
  palette consistency, contrast ratios for design purposes (not WCAG \
  — that is a separate audit), brand alignment. (4) Component \
  consistency — button styles, form controls, card patterns, \
  icon usage. (5) Navigation and interaction patterns — clarity of \
  affordances, feedback on actions, error states. (6) Design system \
  adherence — are project conventions followed consistently? \
  (7) Mobile/responsive design — layout at different breakpoints. \
  Rate severity on user impact and frequency of encounter. \
  Heuristic column: map to Nielsen's 10 heuristics (N#1-N#10) or \
  named design principle. Do not read or reference any other review file."
```

Claude writes independent review to `docs/design/NNN-CLAUDE.md`
simultaneously (same format, ID prefix `A`).

**Phase 3 — Synthesis:**
- Verify both files exist and are non-empty (single-agent warning if not)
- Deduplicate; note confidence from agreement; calibrate severity on
  user impact evidence
- Write `docs/design/NNN-SYNTHESIS.md` with canonical S-prefix IDs

**Phase 4 — Devil's Advocate:**
```bash
codex exec "Read docs/design/NNN-SYNTHESIS.md. Attack it, not improve \
  it. Write to docs/design/NNN-DEVILS-ADVOCATE.md: (1) false positives \
  — design choices that are intentional or context-appropriate, \
  (2) severity miscalibrations, (3) missed findings, \
  (4) impractical remediation suggestions. Cite finding ID for each."
```

**Phase 5 — Sprint Output:**
- Sprint title: `Design Audit: [scope] ([YYYY-MM-DD])`
- Critical/High → P0, Medium → P1, Low → Deferred
- Each task: finding ID, location, issue, remediation, verification
- No-findings: single P0 "Verify no findings" task
- Register: `/ledger add NNN "Design: [scope]"`
- Instruct user: review task ordering, then `/sprint-work NNN`

**Tasks:**
- [ ] Write `commands/audit-design.md` with complete 5-phase workflow
- [ ] Verify all Codex exec prompts are self-contained (NNN literal)
- [ ] Verify finding schema matches the design schema defined above
- [ ] Verify sprint output follows `docs/sprints/README.md` template
- [ ] Verify `/ledger add` uses correct syntax

**Acceptance:**
- `commands/audit-design.md` exists with valid single-line `description:` frontmatter
- Phase 2 runs Claude and Codex in parallel
- Finding schema includes `Heuristic` column
- Phase 5 output is a valid sprint document consumable by `/sprint-work`
- Severity rated on user impact, not just design opinion
- No `--model`/`--full-auto` flags in Codex exec calls

#### P0-B: `commands/audit-accessibility.md`

**Files:**
- `commands/audit-accessibility.md` — NEW

**Frontmatter:**
```yaml
---
description: >-
  Dual-agent accessibility audit — Claude and Codex review against WCAG
  2.1/2.2 independently, synthesize, devil's advocate pass, output as
  executable sprint
---
```

**Phase 1 — Orient:**
- Validate scope from `$ARGUMENTS` or default to cwd
- Identify relevant files: HTML templates, React/Vue/Svelte components,
  CSS (for contrast, focus styles), JS (for dynamic ARIA, keyboard
  handling), image assets (for alt text review)
- Note any automated accessibility tooling already in use (axe, Lighthouse,
  pa11y) — manual review complements, not replaces, these
- Determine next SPRINT-NNN; create `docs/accessibility/` if needed

**Phase 2 — Independent Reviews (parallel):**

Codex (background):
```bash
codex exec "Perform a thorough accessibility audit of [RESOLVED_SCOPE] \
  against WCAG 2.1/2.2 guidelines. \
  Write findings to docs/accessibility/NNN-CODEX.md using this table: \
  | ID | Severity | Title | Location | WCAG | Level | Why It Matters | Recommended Fix | Evidence/Notes | \
  where ID uses prefix C (e.g. C001). \
  WCAG column: success criterion number (e.g. 1.4.3) or 'Best Practice'. \
  Level column: A, AA, AAA, or BP. \
  Cover: (1) Semantic structure — heading hierarchy, landmark regions, \
  list markup, table structure. (2) Images and non-text content — \
  alt text quality, decorative images, complex images. (3) Color and \
  contrast — WCAG 1.4.3 (AA: 4.5:1 normal text, 3:1 large text), \
  1.4.11 (non-text contrast 3:1). (4) Keyboard navigation — all \
  interactive elements reachable via keyboard, logical tab order, \
  no keyboard traps. (5) Focus management — visible focus indicators, \
  focus restoration after modal/dialog, skip links. \
  (6) ARIA usage — roles, states, properties used correctly; \
  no redundant or conflicting ARIA. (7) Forms — labels associated \
  with controls, error messages programmatically associated, \
  required fields indicated. (8) Dynamic content — screen reader \
  announcements for live regions, status messages, alerts. \
  (9) Motion and animation — respects prefers-reduced-motion. \
  (10) Cognitive accessibility — clear error messages, consistent \
  navigation, timeout warnings. \
  Rate severity: Level A violations = Critical, AA = High, AAA = \
  Medium, Best Practice = Low (adjust based on user impact evidence). \
  Do not read or reference any other review file."
```

Claude writes independent review to `docs/accessibility/NNN-CLAUDE.md`
simultaneously (same format, ID prefix `A`). Cover the same 10
categories. Note: when auditing via static code review, focus on
markup patterns, ARIA usage, and CSS rather than runtime behavior
that requires browser testing.

**Phase 3 — Synthesis:**
- Same process as `audit-security` Phase 3
- Note WCAG criterion overlaps (a single element may fail multiple
  criteria — preserve each as a separate finding if remediation differs)
- Write `docs/accessibility/NNN-SYNTHESIS.md`

**Phase 4 — Devil's Advocate:**
```bash
codex exec "Read docs/accessibility/NNN-SYNTHESIS.md. Attack it, not \
  improve it. Write to docs/accessibility/NNN-DEVILS-ADVOCATE.md: \
  (1) false positives — findings that are actually accessible in \
  context, (2) severity miscalibrations — findings rated too high or \
  low relative to WCAG conformance level and user impact, \
  (3) missed findings — what did both reviewers miss? \
  (4) remediation steps that are incorrect or would introduce new \
  accessibility issues. Cite WCAG criterion and finding ID."
```

**Phase 5 — Sprint Output:**
- Sprint title: `Accessibility Audit: [scope] ([YYYY-MM-DD])`
- WCAG Level A failures → Critical → P0
- WCAG Level AA failures → High → P0
- WCAG Level AAA / Best Practice → Medium/Low → P1/Deferred
- Each task must include: finding ID, WCAG criterion, location, issue,
  remediation, verification (including how to test the fix)
- Note: some accessibility fixes require browser/screen reader testing
  beyond static review — include testing guidance in task descriptions
- No-findings: single P0 "Verify no findings" task with scope,
  date, reviewer agents, and WCAG version audited
- Register: `/ledger add NNN "Accessibility: [scope]"`
- Instruct user: review task ordering, then `/sprint-work NNN`

**Tasks:**
- [ ] Write `commands/audit-accessibility.md` with complete 5-phase workflow
- [ ] Verify all Codex exec prompts are self-contained (NNN literal)
- [ ] Verify finding schema includes `WCAG` and `Level` columns
- [ ] Verify severity mapping to WCAG conformance levels is documented
- [ ] Verify sprint output follows `docs/sprints/README.md` template
- [ ] Verify `/ledger add` uses correct syntax

**Acceptance:**
- `commands/audit-accessibility.md` exists with valid single-line `description:` frontmatter
- Phase 2 runs Claude and Codex in parallel
- Finding schema includes `WCAG` and `Level` columns
- WCAG 2.1/2.2 is cited as the normative reference
- Severity mapping to WCAG conformance levels is explicit
- Phase 5 output is valid sprint document consumable by `/sprint-work`
- No `--model`/`--full-auto` flags in Codex exec calls

### P1: Ship If Capacity Allows

#### P1-A: `README.md` updates

Add `audit-design` and `audit-accessibility` to the commands section
of `README.md`:
- Brief description of each command
- Invocation examples
- Note on relationship to `/sprint-work`
- Note on how the three `audit-*` commands relate to each other

#### P1-B: `docs/design/README.md` and `docs/accessibility/README.md`

Lightweight reference files for each new artifact directory:
- Purpose and naming convention (NNN matches sprint number)
- Finding schema for that command type
- Note: may contain sensitive findings about UI/UX or compliance gaps;
  review before committing to public repos

### Deferred

- `audit-deps` and other `audit-*` commands — establish design and
  accessibility patterns first
- Automated WCAG tooling integration (axe, Lighthouse CLI) — out of
  scope for command files; these are workflow aids for human-reviewed
  work
- Linear/Jira sync for audit findings — reuse sprint-plan's tool sync
  when needed
- Combining `audit-accessibility` and `audit-design` into a single
  command — kept separate by intent (different audiences, different
  remediation owners, different normative references)

## Files Summary

| File | Action | Purpose |
|------|--------|---------|
| `commands/audit-design.md` | Create | 5-phase dual-agent design audit command (P0-A) |
| `commands/audit-accessibility.md` | Create | 5-phase dual-agent accessibility audit command (P0-B) |
| `README.md` | Modify | Document new commands for discoverability (P1-A) |
| `docs/design/README.md` | Create | Naming conventions and finding schema (P1-B) |
| `docs/accessibility/README.md` | Create | Naming conventions and finding schema (P1-B) |

## Definition of Done

- [ ] `commands/audit-design.md` exists with valid single-line `description:` frontmatter
- [ ] `commands/audit-accessibility.md` exists with valid single-line `description:` frontmatter
- [ ] Both commands follow the 5-phase `audit-security` pattern (Orient → Reviews → Synthesis → Devil's Advocate → Sprint Output)
- [ ] Phase 2 in each command: Codex launched in background; Claude reviews simultaneously
- [ ] `audit-design` finding schema includes `Heuristic` column referencing Nielsen's heuristics or named design principles
- [ ] `audit-accessibility` finding schema includes `WCAG` and `Level` columns
- [ ] WCAG 2.1/2.2 cited as normative reference in `audit-accessibility`
- [ ] Severity mapping to WCAG conformance levels explicitly documented in `audit-accessibility`
- [ ] Phase 3 synthesis in each: deduplicates findings; notes confidence from agreement; severity rated on evidence
- [ ] Phase 4 devil's advocate in each: Codex attacks synthesis; valid challenges incorporated; rejections documented
- [ ] Phase 5 sprint output in each: follows `docs/sprints/README.md` template; P0/P1/Deferred tiering; each task has finding ID + location + issue + remediation + verification
- [ ] No-findings case handled in each (produces "Verify no findings" P0 task)
- [ ] `/ledger add NNN` included in Phase 5 of each command
- [ ] User instructed to run `/sprint-work NNN` (correct syntax) in each
- [ ] No `--model`/`--full-auto` flags in any Codex exec call
- [ ] `$ARGUMENTS` validated as path in Phase 1 of each command before any use in Codex prompts
- [ ] Both commands use separate artifact directories (`docs/design/`, `docs/accessibility/`)
- [ ] Manual read-through: each phase of each command produces what the next phase consumes
- [ ] Edge-case read-through for each: (1) no scope arg, (2) path-scoped audit, (3) overlapping findings, (4) no findings, (5) no frontend files in scope

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Design audit produces overly subjective findings | Medium | Medium | Phase 1 Codex prompt anchors severity to user impact + named heuristics, not aesthetic opinion |
| Accessibility static review misses runtime issues | High | Medium | Phase 5 task descriptions include testing guidance; inherent-limitations note in command overview |
| WCAG version ambiguity (2.1 vs 2.2) | Low | Low | Command explicitly covers 2.1/2.2; finding schema records the criterion number |
| NNN collision if multiple audits run on same day | Low | Medium | Orient phase always checks the current max sprint number; each audit increments |
| Command files too long for Gemini TOML | Low | Low | `audit-security` already long; note if limit is hit |
| Codex exec prompt references NNN as unresolved variable | Medium | Medium | Orient phase resolves NNN first; prompts use the literal number |

## Security Considerations

- Command files flow into agent system prompts — review for unintended
  scope expansion or privilege escalation
- `$ARGUMENTS` must be validated as a path in Phase 1 before use in
  any Codex exec prompt (same constraint as `audit-security`)
- `docs/design/` and `docs/accessibility/` artifacts may reveal
  sensitive UX or compliance gaps — P1-B READMEs should note review
  before committing to public repos
- Codex exec prompts must not instruct Codex to execute shell commands
  beyond reading files and writing to the artifact directory
- Sprint tasks will be executed by agents via `/sprint-work` — task
  descriptions must be specific enough to be safe

## Observability & Rollback

- Verification: invoke each command on a project with known UI/UX or
  accessibility issues; confirm artifact files are produced and the
  sprint document is consumable by `/sprint-work`
- Rollback: text files only; `git restore` or `git revert` as appropriate

## Documentation

- [ ] P1-A: Add `audit-design` and `audit-accessibility` to `README.md`
- [ ] P1-B: Create `docs/design/README.md` with naming convention and schema
- [ ] P1-B: Create `docs/accessibility/README.md` with naming convention and schema

## Dependencies

- SPRINT-001 (completed) — commands/ architecture
- SPRINT-002 (completed) — docs/ conventions, sprint template
- SPRINT-003 (completed) — ledger skill integration, `/ledger add` syntax
- SPRINT-004 (completed) — `audit-security` as pattern template

## Open Questions

1. Should the `audit-design` heuristic column use Nielsen numbering
   strictly, or allow free-form principle names? → Propose: allow
   free-form; Nielsen numbers are a shorthand, not a requirement.
2. Should `audit-accessibility` note known limitations of static review
   vs. browser/assistive technology testing in the command overview?
   → Propose: yes — same as `audit-security`'s inherent-limitations note.
3. In `audit-accessibility` Phase 5, should WCAG Level A failures
   always be P0 regardless of actual user impact? → Propose: use
   WCAG level as a starting point; the command allows severity override
   based on evidence.
