# Sprint 005: `audit-design` and `audit-accessibility` Commands

## Overview

SPRINT-004 shipped `commands/audit-security.md` — the first command in
the `audit-*` family — and explicitly deferred additional commands
until the pattern was validated. That sprint is complete. This sprint
delivers the next two: `audit-design` and `audit-accessibility`.

`audit-design` applies the proven 5-phase dual-agent workflow to UI/UX
quality: layout, typography, color, component consistency, information
hierarchy, and design system adherence. Output is an executable sprint
of design remediation tasks.

`audit-accessibility` applies the same workflow with WCAG 2.1/2.2 as
the normative reference: semantic HTML, ARIA, keyboard navigation, focus
management, color contrast, screen reader support, motion sensitivity,
and cognitive load. Output is an executable sprint of accessibility
tasks, each tied to a WCAG success criterion.

Both commands extend the `audit-security` base finding schema with
domain-specific metadata columns. This is a declared family design
decision: the `audit-*` family uses the `audit-security` core schema as
a base; domain commands may add extension columns that anchor findings
to normative standards (heuristics for design, WCAG criteria for
accessibility). This improves actionability without breaking the
family's output contract with `/sprint-work`.

**Inherent limitations** (both commands): These are workflow aids for
human-reviewed work, not automated scanners. For `audit-accessibility`
in particular, static code review can identify likely issues but cannot
fully validate dynamic behavior, screen reader output, or focus
management without browser and assistive technology testing. Task
descriptions in the output sprint will indicate which findings require
runtime verification.

## Key Decisions

1. **Two commands, same 5-phase workflow**: both mirror `audit-security`
2. **Separate artifact directories**: `docs/design/` and `docs/accessibility/`
3. **Schema extension declared**: core columns preserved; extension
   columns (`Heuristic` for design; `WCAG`, `Level` for accessibility)
   are named additions, not schema replacements
4. **No-UI behavior**: warn and stop — if Phase 1 finds no frontend
   files in scope, the command notifies the user and stops
5. **README updates are P1**: consistent with the `audit-security` rollout
6. **Codex exec prompt constraints**: no `--model`, no `--full-auto`,
   `$ARGUMENTS` validated before use in any shell string

## Use Cases

1. **Pre-launch design review**: scope `audit-design` to a component
   library or full frontend; findings become a polish sprint.
2. **Accessibility pre-launch review**: run `audit-accessibility` before
   public launch or a compliance preparation phase; Level A/AA findings
   become P0 sprint tasks (note: this is a structured review starting
   point, not a conformance certification — runtime testing is still
   required for full WCAG validation).
3. **Incremental component audit**: scope either command to a specific
   directory for focused review.
4. **Cross-audit workflow**: run all three `audit-*` commands; each
   produces its own sprint; execute in priority order.

## Architecture

```
audit-design / audit-accessibility [$ARGUMENTS = optional path(s)]

Phase 1: Orient
  → Validate scope ($ARGUMENTS or cwd; supports multiple paths)
  → Identify frontend/UI files
  → Warn and stop if no UI files found
  → Determine next SPRINT-NNN number
  → Create docs/design/ or docs/accessibility/ if needed

Phase 2: Independent Reviews (parallel)
  → Codex: write NNN-CODEX.md  (background)
  → Claude: write NNN-CLAUDE.md (simultaneously)

Phase 3: Synthesis
  → Verify both files non-empty; calibrate severity; deduplicate
  → Write NNN-SYNTHESIS.md

Phase 4: Devil's Advocate (Codex)
  → Codex attacks synthesis → NNN-DEVILS-ADVOCATE.md
  → Claude incorporates valid challenges; documents rejections

Phase 5: Sprint Output
  → Produce docs/sprints/SPRINT-NNN.md
  → Severity → priority: Critical/High=P0, Medium=P1, Low=Deferred
  → /ledger add NNN "Design: [scope]"  (or "Accessibility: [scope]")
  → User runs /sprint-work NNN
```

## Finding Schemas

### `audit-design` finding schema

```
| ID | Severity | Title | Location | Heuristic | Why It Matters | Recommended Fix | Evidence/Notes |
```

- **Heuristic**: maps to the design standard this violates — priority
  order: (1) project design system if present, (2) cross-pattern
  consistency, (3) Nielsen's heuristics (N#1–N#10), (4) platform
  guidelines (Material Design, Apple HIG) as tiebreaker. When standards
  conflict, the finding should note the disagreement explicitly rather
  than resolve it silently by priority — e.g., "Adheres to Nielsen #4
  but conflicts with project design system token usage."
- **ID prefix**: Claude = `A`, Codex = `C`, Synthesis = `S`
- **Severity anchors**: user impact, breadth of affected surface, task
  interruption severity, cost of inconsistency

### `audit-accessibility` finding schema

```
| ID | Severity | Title | Location | WCAG | Level | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

- **WCAG**: success criterion number (e.g., `1.4.3`) or `Best Practice`
- **Level**: A, AA, AAA, or `BP`
- **Verification**: `code` (inspectable from source) or `runtime`
  (requires browser/AT testing)
- **Severity mapping** (starting point; override based on user impact
  evidence):
  - Level A → Critical (blocking for assistive technology users)
  - Level AA → High (standard compliance requirement)
  - Level AAA → Medium (enhanced accessibility)
  - Best Practice → Low
- **Severity anchors**: exclusion severity, task blockage, assistive
  technology impact, breadth of affected users

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

**Phase 1 — Orient requirements:**
- Validate scope from `$ARGUMENTS` (supports multiple space-separated
  paths) or default to cwd; store resolved paths — do not interpolate
  raw `$ARGUMENTS` into shell strings
- Identify frontend files: HTML, CSS, JSX/TSX, Vue/Svelte/Angular
  components, design tokens, Storybook stories; exclude generated
  files (`build/`, `dist/`, `.next/`, etc.), vendored/third-party UI
  code, and binary assets unless explicitly included in `$ARGUMENTS`
- **No UI files found**: notify user ("No frontend files found in
  [scope]. Re-scope to a directory containing UI files and re-run."),
  stop without creating a sprint
- Determine next SPRINT-NNN; create `docs/design/` if needed

**Phase 2 — Independent Review requirements:**
- Codex (background): write `docs/design/NNN-CODEX.md`; review these
  categories: (1) layout and visual hierarchy, (2) typography, (3) color
  and visual design, (4) component consistency, (5) navigation and
  interaction patterns, (6) design system adherence, (7)
  mobile/responsive design; use finding schema with `Heuristic` column
- Claude (simultaneous): write `docs/design/NNN-CLAUDE.md`; same
  categories and schema; no cross-contamination with Codex review
- Heuristic column priority: (1) project design system, (2) consistency
  with existing patterns, (3) Nielsen heuristics, (4) platform guidelines

**Phase 3 — Synthesis requirements:**
- Verify both files non-empty (single-agent warning if one missing)
- Deduplicate; overlap = higher confidence, not higher severity
- Calibrate severity on: user impact, breadth, task interruption,
  consistency cost
- Write `docs/design/NNN-SYNTHESIS.md`

**Phase 4 — Devil's Advocate requirements:**
- Codex attacks synthesis: false positives (intentional design choices),
  severity miscalibrations, missed findings, impractical remediation
- Claude incorporates valid challenges; documents every rejected challenge
  with reasoning in "Rejected Challenges" section of synthesis

**Phase 5 — Sprint Output requirements:**
- Title: `Design Audit: [scope] ([YYYY-MM-DD])`
- Each task: finding ID, location, heuristic, issue, remediation,
  verification
- No-findings: single P0 "Verify no findings" task with scope, date,
  categories covered, reviewer agents
- Register: `/ledger add NNN "Design: [scope]"`
- Instruct user: review task ordering, then `/sprint-work NNN`

**Tasks:**
- [ ] Write `commands/audit-design.md` with complete 5-phase workflow
- [ ] Verify all Codex exec prompts are self-contained (NNN literal,
      no `--model`/`--full-auto`, no raw `$ARGUMENTS` interpolation)
- [ ] Verify finding schema includes `Heuristic` column
- [ ] Verify no-UI warn-and-stop behavior is in Phase 1
- [ ] Verify sprint output follows `docs/sprints/README.md` template
- [ ] Verify `/ledger add` uses correct skill syntax
- [ ] Manual read-through: Phase 1 → 2 → 3 → 4 → 5 produces what
      the next phase consumes

**Acceptance:**
- `commands/audit-design.md` exists with valid single-line `description:` frontmatter
- Phase 1 stops with message if no UI files found
- Phase 2 runs Claude and Codex in parallel
- Finding schema includes `Heuristic` column with priority order documented
- Phase 5 output is a valid sprint document consumable by `/sprint-work`
- No `--model`/`--full-auto` flags in any Codex exec call

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

**Phase 1 — Orient requirements:**
- Validate scope from `$ARGUMENTS` (supports multiple paths) or cwd
- Identify relevant files: HTML/JSX/Vue/Svelte, CSS (contrast, focus
  styles), JS (ARIA, keyboard handling), image assets (alt text);
  exclude generated files, vendored code, and binary assets unless
  explicitly in `$ARGUMENTS`
- **No UI files found**: notify user, stop — same behavior as
  `audit-design`
- Note any automated accessibility tooling already in project (axe,
  Lighthouse, pa11y) — these tools complement but do not replace
  manual/LLM review
- Determine next SPRINT-NNN; create `docs/accessibility/` if needed

**Phase 2 — Independent Review requirements:**
- Codex (background): write `docs/accessibility/NNN-CODEX.md`; use
  finding schema with `WCAG`, `Level`, `Verification` columns; cover:
  (1) semantic structure and heading hierarchy, (2) images and non-text
  content, (3) color and contrast (WCAG 1.4.3, 1.4.11), (4) keyboard
  navigation and tab order, (5) focus management and focus visibility,
  (6) ARIA usage, (7) form labels and error messages, (8) dynamic
  content and live regions, (9) motion and animation (prefers-reduced-
  motion), (10) cognitive accessibility (error messages, consistency,
  timeouts); rate verification mode as `code` or `runtime`
- Claude (simultaneous): write `docs/accessibility/NNN-CLAUDE.md`;
  same 10 categories and schema; note: items like live region behavior
  and focus restoration may need `runtime` verification mode
- WCAG 2.1/2.2 is the normative reference; use criterion number in
  the WCAG column (e.g., `1.4.3`); `Best Practice` for items beyond
  WCAG scope

**Phase 3 — Synthesis requirements:**
- Same process as `audit-security` Phase 3
- Note WCAG criterion overlaps: a single element may fail multiple
  criteria — preserve each as a separate finding if remediation differs
- **Grouping rule**: when the same broken pattern appears across many
  components (e.g., missing `aria-label` on all icon buttons), create
  one representative finding and document the extent in Evidence/Notes
  (e.g., "Affects 12 icon buttons across 4 components") rather than
  generating a duplicate finding per instance
- Calibrate severity using WCAG level as starting point; override based
  on exclusion severity, task blockage, AT impact, breadth
- Write `docs/accessibility/NNN-SYNTHESIS.md`

**Phase 4 — Devil's Advocate requirements:**
- Codex attacks synthesis: false positives (accessible in context),
  severity miscalibrations, missed findings, incorrect remediation
  steps (including fixes that would introduce new a11y issues)
- Claude incorporates valid challenges; documents rejections

**Phase 5 — Sprint Output requirements:**
- Title: `Accessibility Audit: [scope] ([YYYY-MM-DD])`
- Each task: finding ID, WCAG criterion, conformance level, verification
  mode, location, issue, remediation, verification (including how to
  test the fix — note if AT/browser testing is required)
- No-findings: single P0 "Verify no findings" task with scope, date,
  categories covered, WCAG version audited, reviewer agents
- Register: `/ledger add NNN "Accessibility: [scope]"`
- Note before `/sprint-work`: "Some findings require browser/AT
  verification — include this in task execution."
- Instruct user: review task ordering, then `/sprint-work NNN`

**Tasks:**
- [ ] Write `commands/audit-accessibility.md` with complete 5-phase workflow
- [ ] Verify all Codex exec prompts are self-contained (NNN literal,
      no flags, no raw `$ARGUMENTS` interpolation)
- [ ] Verify finding schema includes `WCAG`, `Level`, and `Verification`
      columns
- [ ] Verify WCAG severity mapping is documented
- [ ] Verify no-UI warn-and-stop behavior is in Phase 1
- [ ] Verify sprint output follows `docs/sprints/README.md` template
- [ ] Verify `/ledger add` uses correct skill syntax
- [ ] Manual read-through: each phase produces what the next consumes

**Acceptance:**
- `commands/audit-accessibility.md` exists with valid single-line `description:` frontmatter
- Phase 1 stops with message if no UI files found
- Phase 2 runs Claude and Codex in parallel
- Finding schema includes `WCAG`, `Level`, and `Verification` columns
- WCAG 2.1/2.2 cited as normative reference
- WCAG level → severity mapping explicitly documented
- Phase 5 tasks include verification mode and testing guidance
- No `--model`/`--full-auto` flags in any Codex exec call

#### P0-C: Family Consistency Check

Before marking this sprint complete, verify the three `audit-*` commands
are consistent as a family:

- [ ] All three commands use the same 5-phase structure (Orient →
      Independent Reviews → Synthesis → Devil's Advocate → Sprint Output)
- [ ] All three commands validate `$ARGUMENTS` in Phase 1 before use
      in Codex exec prompts
- [ ] All three commands handle: scoped audit, multi-path audit,
      overlapping findings, no-findings, no-applicable-files
- [ ] All three commands produce a `/sprint-work`-consumable sprint doc
- [ ] Finding schemas are explicitly declared: core + domain extensions
- [ ] No `--model`/`--full-auto` in any Codex exec call across all three

### P1: Ship If Capacity Allows

#### P1-A: `README.md` Updates

Add `audit-design` and `audit-accessibility` to `README.md`:
- Brief description of each command
- Invocation examples for Claude (`/audit-design`), Codex
  (`codex exec "..."`), and Gemini — consistent with the existing
  capability matrix
- Relationship to `/sprint-work` and the `audit-*` family
- Note on `audit-accessibility`'s static-review limitations

#### P1-B: Directory READMEs

Create `docs/design/README.md` and `docs/accessibility/README.md`:
- Purpose and naming convention (`NNN` matches sprint number)
- Finding schema for that command type (with extension columns)
- Note: these files may contain project findings; review before
  committing to public repos

### Deferred

- `audit-deps` and other `audit-*` commands — establish design and
  accessibility patterns first
- Automated browser/AT testing integration (axe, Lighthouse CLI) —
  out of scope for command files; these are workflow aids
- Combining design and accessibility into a single command — kept
  separate intentionally (different normative refs, different
  remediation owners, different audiences)
- Linear/Jira sync for audit findings — reuse sprint-plan's tool
  sync pattern when needed

## Files Summary

| File | Action | Purpose |
|------|--------|---------|
| `commands/audit-design.md` | Create | 5-phase dual-agent design audit (P0-A) |
| `commands/audit-accessibility.md` | Create | 5-phase dual-agent accessibility audit (P0-B) |
| `README.md` | Modify | Discoverability and invocation examples (P1-A) |
| `docs/design/README.md` | Create | Naming convention and finding schema (P1-B) |
| `docs/accessibility/README.md` | Create | Naming convention and finding schema (P1-B) |

## Definition of Done

- [ ] `commands/audit-design.md` exists with valid single-line
      `description:` frontmatter
- [ ] `commands/audit-accessibility.md` exists with valid single-line
      `description:` frontmatter
- [ ] Both commands follow the 5-phase `audit-security` pattern
- [ ] Phase 2 in each: Codex launched in background; Claude reviews
      simultaneously
- [ ] `audit-design` finding schema includes `Heuristic` column with
      documented priority order
- [ ] `audit-accessibility` finding schema includes `WCAG`, `Level`,
      and `Verification` columns
- [ ] WCAG 2.1/2.2 cited as normative reference in
      `audit-accessibility`
- [ ] WCAG level → severity mapping explicitly documented
- [ ] Phase 1 of each: no-UI files → warn and stop with message
- [ ] Phase 1 of each: multiple path arguments are supported
- [ ] Phase 1 of each: artifact directory created before Codex is
      launched in Phase 2
- [ ] `$ARGUMENTS` validated as path(s) in Phase 1; raw argument text
      never interpolated into any Codex exec shell string
- [ ] Phase 5 of each: follows `docs/sprints/README.md` template
- [ ] Phase 5 of each: `/ledger add NNN` completed (or user instructed)
- [ ] Phase 5 of each: user instructed to run `/sprint-work NNN`
- [ ] No-findings handled: produces "Verify no findings" P0 task
- [ ] No `--model`/`--full-auto` flags in any Codex exec call
- [ ] P0-C family consistency check passes
- [ ] Manual read-through: each phase of each command produces what
      the next phase consumes
- [ ] Edge-case read-through for each: (1) no scope arg, (2) path-
      scoped audit, (3) multi-path audit, (4) overlapping findings,
      (5) no findings, (6) no UI files in scope

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Design findings become subjective without standards anchor | Medium | Medium | Heuristic column with documented priority order; severity based on user impact, not aesthetic opinion |
| Accessibility static review over-claims certainty | High | Medium | `Verification` column distinguishes code vs. runtime; inherent-limitations note in command overview |
| Schema divergence from `audit-security` confuses future `audit-*` authors | Low | Medium | Sprint doc declares extension as explicit family design decision |
| NNN collision if multiple audits run same day | Low | Medium | Orient phase always checks current max; each audit increments |
| Command file too long for Gemini TOML | Low | Low | `audit-security` already long; note if limit hit |

## Security Considerations

- Command files flow into agent system prompts — review for unintended
  scope expansion or privilege escalation
- `$ARGUMENTS` must be validated as path(s) in Phase 1 before use in
  any Codex exec prompt
- `docs/design/` and `docs/accessibility/` artifacts may reveal
  sensitive UX or compliance gaps — P1-B READMEs should note to review
  before committing to public repos
- Codex exec prompts must not instruct Codex to execute shell commands
  beyond reading files and writing to the artifact directory
- Sprint tasks will be executed by agents — task descriptions must be
  specific enough to be safe

## Observability & Rollback

- Verification: invoke each command on a project with known UI/design
  or accessibility issues; confirm artifact files are produced and the
  sprint document is consumable by `/sprint-work`
- Rollback: text files only; `git restore` or `git revert` as
  appropriate

## Documentation

- [ ] P1-A: Add both commands to `README.md` with invocation examples
- [ ] P1-B: Create `docs/design/README.md` with naming and schema
- [ ] P1-B: Create `docs/accessibility/README.md` with naming and schema

## Dependencies

- SPRINT-001 (completed) — commands/ architecture
- SPRINT-002 (completed) — docs/ conventions, sprint template
- SPRINT-003 (completed) — ledger skill integration
- SPRINT-004 (completed) — `audit-security` as pattern template

## Open Questions

None — all design questions resolved during planning.
