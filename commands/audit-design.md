---
description: >-
  Dual-agent design audit — Claude and Codex review UI/UX independently,
  synthesize findings, devil's advocate pass, output as executable sprint
---

# Design Audit: Dual-Agent Review

You are orchestrating a dual-agent design audit that produces an
executable sprint document. Claude and Codex review independently,
findings are synthesized, Codex attacks the synthesis, and the final
output is a standard `SPRINT-NNN.md` sprint worked by `/sprint-work`.

This command is part of the `audit-*` family and follows the same
5-phase workflow as `audit-security`. The `audit-design` finding
schema extends the core schema with a `Heuristic` column that anchors
each finding to a normative design standard.

**Inherent limitations**: This is a workflow aid for human-reviewed
design work, not an automated scanner. LLM review can identify likely
issues but cannot validate visual rendering, user perception, or
dynamic interaction without browser testing. Treat the output as a
structured starting point for human judgment, not a guarantee of full
coverage.

## Arguments

`$ARGUMENTS` is an optional path or scope to audit. Examples:

- `audit-design` — audits the current working directory
- `audit-design src/components` — scopes the audit to `src/components`
- `audit-design src/components src/pages` — scopes to multiple paths

If no argument is provided, the scope is the current working
directory. Scope is validated as a path in Phase 1 before being
used anywhere else — raw user input is never interpolated into
shell strings.

## Workflow Overview

This is a **5-phase workflow**:

1. **Orient** — Determine scope, identify frontend files, next sprint number
2. **Independent Reviews** — Claude and Codex review in parallel (Codex
   in background, Claude simultaneously)
3. **Synthesis** — Deduplicate findings; flag agreements as higher confidence;
   calibrate severity
4. **Devil's Advocate** — Codex attacks the synthesis for false positives,
   severity miscalibrations, and gaps
5. **Sprint Output** — Produce `SPRINT-NNN.md` with findings as tasks;
   register in ledger; hand off to `/sprint-work`

---

## Finding Schema

All intermediate audit files must use this table format so synthesis
and devil's advocate phases operate on consistent data:

```
| ID | Severity | Title | Location | Heuristic | Why It Matters | Recommended Fix | Evidence/Notes |
|----|----------|-------|----------|-----------|----------------|-----------------|----------------|
| A001 | High | Short title | path/to/file:line | Nielsen N#1 | Impact explanation | Concrete fix | Screenshot ref or code quote |
```

**ID prefix convention:**
- Claude's review: `A001`, `A002`... (Audit)
- Codex's review: `C001`, `C002`... (Codex)
- Synthesis: `S001`, `S002`... (Synthesis)

**Severity levels:** Critical, High, Medium, Low

Severity is assessed on: user impact, breadth of affected surface,
task interruption severity, cost of inconsistency. Agreement between
reviewers raises **confidence**, not severity.

**Heuristic column priority order:**
1. Project design system (if present) — always takes precedence
2. Cross-pattern consistency with existing project UI
3. Nielsen's heuristics (N#1–N#10)
4. Platform guidelines (Material Design, Apple HIG) as tiebreaker

When standards conflict, note the disagreement explicitly rather than
resolving silently by priority — e.g., "Adheres to Nielsen #4 but
conflicts with project design system token usage."

---

## Phase 1: Orient

**Goal**: Understand the scope, identify frontend files, and determine
the next sprint number.

### Orient Steps

1. **Validate and resolve scope** from `$ARGUMENTS`:
   - If no argument: scope is the current working directory
   - If an argument is provided: verify the path exists
   - Exclude: `build/`, `dist/`, `.next/`, `.nuxt/`, generated files,
     vendored/third-party UI code, and binary assets — unless explicitly
     included in `$ARGUMENTS`
   - Store the resolved scope path — do not use raw `$ARGUMENTS`
     text in any Codex exec prompt string

2. **Identify frontend files** in the resolved scope:
   - HTML files (`.html`, `.htm`)
   - CSS and style files (`.css`, `.scss`, `.sass`, `.less`)
   - Component files (`.jsx`, `.tsx`, `.vue`, `.svelte`, `.astro`)
   - Angular templates and components (`.component.html`, `.component.ts`)
   - Design tokens and theme files
   - Storybook stories (`.stories.js`, `.stories.ts`, `.stories.mdx`)

3. **No UI files found**: if no frontend files exist in the resolved
   scope, notify the user and stop:
   > No frontend files found in [scope]. Re-scope to a directory
   > containing UI files and re-run: `/audit-design path/to/frontend`
   Do not create a sprint or artifact files.

4. **Determine next sprint number**:
   ```bash
   ls docs/sprints/SPRINT-*.md | tail -1
   ```
   Extract NNN and increment. If no sprint files exist, start at `001`.
   Call this `AUDIT_NNN` — use the literal number in all subsequent
   file references, not a variable.

5. **Create output directory**:
   ```bash
   mkdir -p docs/design
   ```
   Create this before launching Codex in Phase 2.

### Orient Deliverable

A brief orientation note (3-5 bullets) covering:
- Resolved scope and what it includes/excludes
- Frontend file types and count identified
- Any design system or token files found
- The next sprint number (`AUDIT_NNN`)

---

## Phase 2: Independent Reviews (Parallel)

**Goal**: Get two independent design perspectives without cross-
contamination.

### Step 1 — Launch Codex in Background

Run this command, substituting the resolved scope and `AUDIT_NNN`:

```bash
codex exec "Perform a thorough design and UX review of [RESOLVED_SCOPE]. \
  Write all findings to docs/design/AUDIT_NNN-CODEX.md using this \
  exact table format for each finding: \
  | ID | Severity | Title | Location | Heuristic | Why It Matters | Recommended Fix | Evidence/Notes | \
  where ID uses prefix C (e.g. C001, C002). \
  Heuristic column priority: (1) project design system if present, \
  (2) consistency with existing project UI patterns, \
  (3) Nielsen heuristics (N#1-N#10), (4) platform guidelines as tiebreaker. \
  When standards conflict, note the disagreement explicitly. \
  Cover these design categories: \
  (1) Layout and visual hierarchy — spacing, alignment, grid consistency, \
  information priority. \
  (2) Typography — font scale, line height, weight usage, readability. \
  (3) Color and visual design — palette consistency, contrast, use of color \
  to convey meaning. \
  (4) Component consistency — reuse patterns, prop/variant naming, \
  visual coherence across similar components. \
  (5) Navigation and interaction patterns — affordances, feedback, \
  error states, loading states. \
  (6) Design system adherence — token usage, component library compliance, \
  deviations from established patterns. \
  (7) Mobile and responsive design — breakpoint behavior, touch targets, \
  layout reflow. \
  Rate severity on: user impact, breadth of affected surface, \
  task interruption severity, cost of inconsistency. \
  Do not read or reference any other review file."
```

### Step 2 — Claude's Independent Review (Simultaneous)

While Codex runs, write your own independent design review to
`docs/design/AUDIT_NNN-CLAUDE.md` using the same finding schema
(ID prefix `A`). Cover the same seven categories:

1. **Layout and visual hierarchy** — spacing, alignment, grid
   consistency, information priority
2. **Typography** — font scale, line height, weight usage, readability
3. **Color and visual design** — palette consistency, contrast, use
   of color to convey meaning
4. **Component consistency** — reuse patterns, visual coherence
   across similar components
5. **Navigation and interaction patterns** — affordances, feedback,
   error states, loading states
6. **Design system adherence** — token usage, component library
   compliance, deviations from established patterns
7. **Mobile and responsive design** — breakpoint behavior, touch
   targets, layout reflow

Apply the Heuristic column priority order as documented in the
Finding Schema section. When reviewing design system adherence,
look for established token files or component libraries first
before falling back to Nielsen heuristics.

Wait for Codex to finish before proceeding to Phase 3.

---

## Phase 3: Synthesis

**Goal**: Produce a unified, deduplicated finding list with calibrated
severity and confidence.

### Synthesis Steps

1. **Verify both reviews exist and are non-empty**:
   - Check `docs/design/AUDIT_NNN-CLAUDE.md` and
     `docs/design/AUDIT_NNN-CODEX.md` exist and contain at least
     one finding row
   - If one file is missing or empty: proceed with single-agent
     synthesis and add a prominent warning at the top of
     `AUDIT_NNN-SYNTHESIS.md`: "⚠️ Single-agent synthesis — [agent]
     review was unavailable. Coverage may be incomplete."

2. **Deduplicate findings**:
   - Compare both reviews for overlapping findings
   - When the same issue appears in both, merge into one synthesis
     row — note both source IDs (e.g. `A002, C003`)
   - When merging: preserve the most specific `Location` and the
     best `Evidence/Notes` from either reviewer
   - Do not flatten two findings into one if they have different
     affected components or distinct remediation steps
   - Agreement = higher confidence, not higher severity

3. **Calibrate severity**:
   - Re-evaluate severity for each finding based on: user impact,
     breadth of affected surface, task interruption severity, cost
     of inconsistency
   - Do not automatically escalate severity because both reviewers
     flagged the same issue
   - Distinguish between aesthetic opinion and user-impact evidence

4. **Write synthesis**:

   Write `docs/design/AUDIT_NNN-SYNTHESIS.md`:

   ```markdown
   # Design Audit Synthesis — AUDIT_NNN

   ## Scope
   [Resolved scope path(s)]

   ## Summary
   - Total findings: N (Critical: X, High: X, Medium: X, Low: X)
   - Reviewers: Claude (A-prefix), Codex (C-prefix)
   - [Single-agent warning if applicable]

   ## Unified Findings

   | ID | Severity | Title | Location | Heuristic | Why It Matters | Recommended Fix | Evidence/Notes | Sources |
   |----|----------|-------|----------|-----------|----------------|-----------------|----------------|---------|
   | S001 | ... | ... | ... | ... | ... | ... | ... | A001, C002 |

   ## Findings Present in Only One Review
   [Note findings not corroborated by the other reviewer and why
   they are retained or dropped]
   ```

Phase 3 is complete when `AUDIT_NNN-SYNTHESIS.md` is written.

---

## Phase 4: Devil's Advocate

**Goal**: Challenge the synthesis for false positives, severity
miscalibrations, and missed findings.

### Step 1 — Launch Codex Devil's Advocate

```bash
codex exec "Read docs/design/AUDIT_NNN-SYNTHESIS.md. Your job is \
  to attack it, not improve it. Write your challenge to \
  docs/design/AUDIT_NNN-DEVILS-ADVOCATE.md covering: \
  (1) False positives — findings that reflect intentional design \
  choices rather than actual problems (e.g. deliberate deviation \
  from a heuristic for product reasons). \
  (2) Severity miscalibrations — findings rated too high or too low \
  given the actual user impact and breadth. \
  (3) Missing findings — design issues that both reviewers missed. \
  (4) Remediation steps that are impractical, contradict the project \
  design system, or would introduce new inconsistencies. \
  Be specific. Every challenge must cite the finding ID."
```

### Step 2 — Incorporate Valid Challenges

Once `AUDIT_NNN-DEVILS-ADVOCATE.md` is written, read it and:

- **Remove** confirmed false positives (intentional design choices)
  from the working finding list
- **Recalibrate** severity where the challenge is valid and evidence
  supports it
- **Add** genuinely missed findings with new synthesis IDs
- **Document every rejected challenge** in a "Rejected Challenges"
  section at the bottom of `AUDIT_NNN-SYNTHESIS.md`:

  ```markdown
  ## Rejected Devil's Advocate Challenges

  | Finding/Claim | Reason Rejected |
  |---|---|
  | [Claim from devil's advocate] | [Why it was not accepted] |
  ```

Phase 4 is complete when challenges are incorporated and rejections
are documented.

---

## Phase 5: Sprint Output

**Goal**: Produce a standard `SPRINT-NNN.md` sprint document with
design findings as executable tasks.

### Sprint Mapping Rules

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

Each sprint task must include:
- Finding ID (from synthesis)
- File and component reference where applicable
- Clear description of the design issue
- Concrete, specific remediation step (not just "fix the design")
- Heuristic reference
- Verification step: how to confirm the fix is correct

### No-Findings Case

If the synthesis contains zero findings after Phase 4:
- Create a single P0 task: "Verify no findings — [scope], [date]"
- The task description must document: what scope was covered, what
  categories were reviewed, date of review, and reviewer agents
- Do not produce an empty sprint

### Write the Sprint

Create `docs/sprints/SPRINT-NNN.md` following the standard sprint
template from `docs/sprints/README.md`:

```markdown
# Sprint NNN: Design Audit — [scope] ([YYYY-MM-DD])

## Overview

[1-2 paragraphs: audit scope, total findings by severity, top 3
issues. Remind the reader that static LLM review has inherent
limitations — it cannot validate visual rendering or dynamic
interaction without browser testing.]

## Audit Summary

| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Total | N |

Intermediate audit artifacts: `docs/design/AUDIT_NNN-*.md`

## Implementation Plan

### P0: Must Ship

[One task per Critical/High finding]

**Task: [Finding ID] — [Title]**
- Location: `path/to/file:line`
- Heuristic: [standard this violates]
- Issue: [design problem description]
- Remediation: [specific fix]
- Verification: [how to confirm it's fixed]

### P1: Ship If Capacity Allows

[One task per Medium finding, same format]

### Deferred

[Low findings with brief rationale]

## Definition of Done

- [ ] All P0 tasks completed and verified
- [ ] No new design inconsistencies introduced by the remediations
- [ ] Reviewer confirms task ordering was appropriate for dependencies
[add finding-specific verification items]

## Security Considerations

- Command files and audit artifacts may reveal design or UX details
  about the application — review before committing to public repos
- Task descriptions must be specific enough to be unambiguous when
  executed by an agent

## Dependencies

- AUDIT_NNN intermediate files: `docs/design/AUDIT_NNN-*.md`
```

### Register and Hand Off

1. Register the sprint in the ledger:

   Use the `/ledger add NNN "Design: [scope]"` skill. If it fails,
   instruct the user to run it manually:
   ```
   /ledger add NNN "Design: [scope]"
   ```

2. Inform the user:

   > ✅ Design audit complete. SPRINT-NNN has been created and
   > added to the ledger.
   >
   > **Before running /sprint-work**, review the task ordering in
   > `docs/sprints/SPRINT-NNN.md` — some design remediations may
   > depend on shared tokens or components and should be sequenced.
   >
   > When ready: `/sprint-work NNN`

---

## Output Checklist

At the end of this workflow, verify:

- [ ] `docs/design/AUDIT_NNN-CLAUDE.md` — written using finding schema, ID prefix A
- [ ] `docs/design/AUDIT_NNN-CODEX.md` — written using finding schema, ID prefix C
- [ ] Both files are non-empty (or single-agent warning added to synthesis)
- [ ] `docs/design/AUDIT_NNN-SYNTHESIS.md` — unified findings with canonical S-prefix IDs
- [ ] `docs/design/AUDIT_NNN-DEVILS-ADVOCATE.md` — Codex challenge complete
- [ ] Valid devil's advocate challenges incorporated into synthesis
- [ ] Rejected challenges documented with reasoning in synthesis
- [ ] `docs/sprints/SPRINT-NNN.md` — written with P0/P1/Deferred tiering
- [ ] Each P0/P1 task has: finding ID, location, heuristic, issue, remediation, verification
- [ ] No-findings case handled if applicable
- [ ] `/ledger add NNN` completed (or user instructed to run manually)
- [ ] User instructed to review task ordering, then run `/sprint-work NNN`

---

## Reference

- Sprint conventions: `docs/sprints/README.md`
- Design audit artifacts: `docs/design/`
- Audit family: `audit-*` commands in `commands/`
