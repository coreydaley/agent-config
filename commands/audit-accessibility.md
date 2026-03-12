---
description: >-
  Dual-agent accessibility audit — Claude and Codex review against WCAG
  2.1/2.2 independently, synthesize, devil's advocate pass, output as
  executable sprint
---

# Accessibility Audit: Dual-Agent Review

You are orchestrating a dual-agent accessibility audit that produces an
executable sprint document. Claude and Codex review independently
against WCAG 2.1/2.2, findings are synthesized, Codex attacks the
synthesis, and the final output is a standard `SPRINT-NNN.md` sprint
worked by `/sprint-work`.

This command is part of the `audit-*` family and follows the same
5-phase workflow as `audit-security`. The `audit-accessibility`
finding schema extends the core schema with `WCAG`, `Level`, and
`Verification` columns that anchor each finding to a normative
success criterion.

**Inherent limitations**: This is a workflow aid for human-reviewed
accessibility work, not an automated conformance checker. Static code
review can identify likely issues but cannot fully validate dynamic
behavior, screen reader output, or focus management without browser
and assistive technology testing. Findings marked `runtime` in the
Verification column require browser/AT testing to confirm. This
review is a structured starting point, not a WCAG conformance
certification.

## Arguments

`$ARGUMENTS` is an optional path or scope to audit. Examples:

- `audit-accessibility` — audits the current working directory
- `audit-accessibility src/components` — scopes to `src/components`
- `audit-accessibility src/components src/pages` — scopes to multiple paths

If no argument is provided, the scope is the current working
directory. Scope is validated as a path in Phase 1 before being
used anywhere else — raw user input is never interpolated into
shell strings.

## Workflow Overview

This is a **5-phase workflow**:

1. **Orient** — Determine scope, identify frontend files, note existing
   tooling, determine next sprint number
2. **Independent Reviews** — Claude and Codex review in parallel (Codex
   in background, Claude simultaneously)
3. **Synthesis** — Deduplicate findings; flag agreements as higher confidence;
   calibrate severity using WCAG level as starting point
4. **Devil's Advocate** — Codex attacks the synthesis for false positives,
   severity miscalibrations, and gaps
5. **Sprint Output** — Produce `SPRINT-NNN.md` with findings as tasks;
   register in ledger; hand off to `/sprint-work`

---

## Finding Schema

All intermediate audit files must use this table format so synthesis
and devil's advocate phases operate on consistent data:

```
| ID | Severity | Title | Location | WCAG | Level | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
|----|----------|-------|----------|------|-------|--------------|----------------|-----------------|----------------|
| A001 | Critical | Missing alt text | path/to/img.jsx:12 | 1.1.1 | A | code | Impact explanation | Concrete fix | Code quote |
```

**ID prefix convention:**
- Claude's review: `A001`, `A002`... (Audit)
- Codex's review: `C001`, `C002`... (Codex)
- Synthesis: `S001`, `S002`... (Synthesis)

**Severity levels:** Critical, High, Medium, Low

**WCAG column**: Success criterion number (e.g., `1.4.3`) or
`Best Practice` for items beyond WCAG scope.

**Level column**: `A`, `AA`, `AAA`, or `BP` (Best Practice).

**Verification column**: `code` (inspectable from source alone) or
`runtime` (requires browser and/or assistive technology testing).

**WCAG 2.1/2.2 is the normative reference** for all findings. When
citing a criterion, use the criterion number (e.g., `1.4.3 Contrast
(Minimum)`). WCAG 2.2 additions (e.g., `2.4.11 Focus Appearance`,
`2.4.12 Focus Not Obscured`) apply where relevant.

**Default severity mapping** (starting point; override based on
actual user impact evidence):

| WCAG Level | Default Severity | Rationale |
|---|---|---|
| A | Critical | Blocking for assistive technology users |
| AA | High | Standard compliance requirement |
| AAA | Medium | Enhanced accessibility |
| Best Practice | Low | Beyond WCAG scope but recommended |

Override severity upward when exclusion is severe, task blockage is
total, or breadth of affected users is large. Override downward when
impact evidence is limited or a runtime verification reveals no
actual issue.

---

## Phase 1: Orient

**Goal**: Understand the scope, identify relevant files, note existing
accessibility tooling, and determine the next sprint number.

### Orient Steps

1. **Validate and resolve scope** from `$ARGUMENTS`:
   - If no argument: scope is the current working directory
   - If an argument is provided: verify the path exists
   - Exclude: `build/`, `dist/`, `.next/`, `.nuxt/`, generated files,
     vendored/third-party code, and binary assets — unless explicitly
     included in `$ARGUMENTS`
   - Store the resolved scope path — do not use raw `$ARGUMENTS`
     text in any Codex exec prompt string

2. **Identify relevant files** in the resolved scope:
   - HTML files (`.html`, `.htm`)
   - Component files (`.jsx`, `.tsx`, `.vue`, `.svelte`, `.astro`)
   - Angular templates (`.component.html`)
   - CSS files — for contrast, focus styles, motion (`.css`, `.scss`)
   - JavaScript/TypeScript — for ARIA manipulation and keyboard handling
   - Image assets referenced in markup — for alt text coverage

3. **No UI files found**: if no frontend files exist in the resolved
   scope, notify the user and stop:
   > No frontend files found in [scope]. Re-scope to a directory
   > containing UI files and re-run: `/audit-accessibility path/to/frontend`
   Do not create a sprint or artifact files.

4. **Note existing accessibility tooling** in the project:
   - Check for axe-core, Lighthouse CI, pa11y, jest-axe, or similar
   - These tools complement but do not replace manual/LLM review —
     note their presence so reviewers can reference or defer to
     automated results where appropriate

5. **Determine next sprint number**:
   ```bash
   ls docs/sprints/SPRINT-*.md | tail -1
   ```
   Extract NNN and increment. If no sprint files exist, start at `001`.
   Call this `AUDIT_NNN` — use the literal number in all subsequent
   file references, not a variable.

6. **Create output directory**:
   ```bash
   mkdir -p docs/accessibility
   ```
   Create this before launching Codex in Phase 2.

### Orient Deliverable

A brief orientation note (3-5 bullets) covering:
- Resolved scope and what it includes/excludes
- Frontend file types and count identified
- Any existing accessibility tooling noted
- The next sprint number (`AUDIT_NNN`)

---

## Phase 2: Independent Reviews (Parallel)

**Goal**: Get two independent accessibility perspectives without
cross-contamination.

### Step 1 — Launch Codex in Background

Run this command, substituting the resolved scope and `AUDIT_NNN`:

```bash
codex exec "Perform a thorough accessibility review of [RESOLVED_SCOPE] \
  against WCAG 2.1/2.2. \
  Write all findings to docs/accessibility/AUDIT_NNN-CODEX.md using \
  this exact table format for each finding: \
  | ID | Severity | Title | Location | WCAG | Level | Verification | Why It Matters | Recommended Fix | Evidence/Notes | \
  where ID uses prefix C (e.g. C001, C002). \
  WCAG column: use criterion number (e.g. 1.4.3) or Best Practice. \
  Level column: A, AA, AAA, or BP. \
  Verification column: code (inspectable from source) or runtime \
  (requires browser/AT testing). \
  Default severity: Level A=Critical, AA=High, AAA=Medium, BP=Low; \
  override based on actual exclusion severity and breadth. \
  Cover these 10 categories: \
  (1) Semantic structure and heading hierarchy. \
  (2) Images and non-text content (WCAG 1.1.1). \
  (3) Color and contrast (WCAG 1.4.3 minimum contrast, 1.4.11 \
  non-text contrast). \
  (4) Keyboard navigation and tab order. \
  (5) Focus management and focus visibility (WCAG 2.4.3, 2.4.7, \
  2.4.11, 2.4.12). \
  (6) ARIA usage — roles, states, properties; avoid misuse. \
  (7) Form labels and error messages (WCAG 1.3.1, 3.3.1, 3.3.2). \
  (8) Dynamic content and live regions (WCAG 4.1.3). \
  (9) Motion and animation — prefers-reduced-motion (WCAG 2.3.3). \
  (10) Cognitive accessibility — error messages, consistency, \
  timeouts (WCAG 2.2.1, 3.3.4). \
  Grouping rule: when the same broken pattern appears across many \
  components, create one representative finding and document the \
  extent in Evidence/Notes rather than duplicating per instance. \
  Do not read or reference any other review file."
```

### Step 2 — Claude's Independent Review (Simultaneous)

While Codex runs, write your own independent accessibility review to
`docs/accessibility/AUDIT_NNN-CLAUDE.md` using the same finding
schema (ID prefix `A`). Cover the same 10 categories:

1. **Semantic structure and heading hierarchy** — landmark regions,
   heading levels, list markup
2. **Images and non-text content** — alt text presence and quality,
   decorative image handling (WCAG 1.1.1)
3. **Color and contrast** — text contrast (WCAG 1.4.3), non-text
   contrast (WCAG 1.4.11), color not sole means of conveying info
   (WCAG 1.4.1)
4. **Keyboard navigation and tab order** — all interactive elements
   reachable, logical tab sequence (WCAG 2.1.1, 2.1.2)
5. **Focus management and focus visibility** — focus indicator visible
   (WCAG 2.4.7), focus not obscured (WCAG 2.4.11, 2.4.12), focus
   managed correctly in modals and SPAs (WCAG 2.4.3)
6. **ARIA usage** — roles, states, and properties used correctly;
   no ARIA that misrepresents semantics or conflicts with native HTML
7. **Form labels and error messages** — all inputs labeled (WCAG 1.3.1,
   3.3.2), errors identified and described (WCAG 3.3.1)
8. **Dynamic content and live regions** — status messages announced
   (WCAG 4.1.3); note that live region behavior requires `runtime`
   verification
9. **Motion and animation** — `prefers-reduced-motion` honored
   (WCAG 2.3.3); auto-playing content paused (WCAG 2.2.2)
10. **Cognitive accessibility** — session timeouts warned (WCAG 2.2.1),
    error prevention and recovery (WCAG 3.3.4), consistent navigation
    (WCAG 3.2.3)

Note: focus restoration and live region behavior often require
`runtime` verification — mark Verification column accordingly.

When the same broken pattern appears across many components (e.g.,
missing `aria-label` on all icon buttons), create one representative
finding and document the extent in Evidence/Notes.

Wait for Codex to finish before proceeding to Phase 3.

---

## Phase 3: Synthesis

**Goal**: Produce a unified, deduplicated finding list with calibrated
severity and confidence.

### Synthesis Steps

1. **Verify both reviews exist and are non-empty**:
   - Check `docs/accessibility/AUDIT_NNN-CLAUDE.md` and
     `docs/accessibility/AUDIT_NNN-CODEX.md` exist and contain at
     least one finding row
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
   - A single element may fail multiple WCAG criteria — preserve each
     as a separate finding if the remediation differs
   - Grouping rule: when the same broken pattern is found across many
     components, keep one representative finding with extent documented
     in Evidence/Notes
   - Agreement = higher confidence, not higher severity

3. **Calibrate severity**:
   - Use WCAG level as the starting point (A=Critical, AA=High,
     AAA=Medium, BP=Low)
   - Override based on: exclusion severity (does this block a user
     from completing a task?), assistive technology impact, breadth
     of affected users
   - Do not automatically escalate severity because both reviewers
     flagged the same issue

4. **Write synthesis**:

   Write `docs/accessibility/AUDIT_NNN-SYNTHESIS.md`:

   ```markdown
   # Accessibility Audit Synthesis — AUDIT_NNN

   ## Scope
   [Resolved scope path(s)]

   ## WCAG Version
   WCAG 2.1/2.2 — Levels A, AA reviewed as standard compliance;
   AAA and Best Practices noted where identified.

   ## Summary
   - Total findings: N (Critical: X, High: X, Medium: X, Low: X)
   - Reviewers: Claude (A-prefix), Codex (C-prefix)
   - [Single-agent warning if applicable]

   ## Unified Findings

   | ID | Severity | Title | Location | WCAG | Level | Verification | Why It Matters | Recommended Fix | Evidence/Notes | Sources |
   |----|----------|-------|----------|------|-------|--------------|----------------|-----------------|----------------|---------|
   | S001 | ... | ... | ... | ... | ... | ... | ... | ... | ... | A001, C002 |

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
codex exec "Read docs/accessibility/AUDIT_NNN-SYNTHESIS.md. Your job \
  is to attack it, not improve it. Write your challenge to \
  docs/accessibility/AUDIT_NNN-DEVILS-ADVOCATE.md covering: \
  (1) False positives — findings that are actually accessible in \
  context (e.g. an element with an accessible name from a parent \
  container, or a pattern that is correct for its ARIA role). \
  (2) Severity miscalibrations — findings rated too high or too low \
  given the actual AT impact and user exclusion severity. \
  (3) Missing findings — accessibility issues that both reviewers \
  missed. \
  (4) Remediation steps that are incorrect, incomplete, or would \
  themselves introduce new accessibility issues. \
  Be specific. Every challenge must cite the finding ID and the \
  WCAG criterion if applicable."
```

### Step 2 — Incorporate Valid Challenges

Once `AUDIT_NNN-DEVILS-ADVOCATE.md` is written, read it and:

- **Remove** confirmed false positives (elements that are accessible
  in context) from the working finding list
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
accessibility findings as executable tasks.

### Sprint Mapping Rules

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

Each sprint task must include:
- Finding ID (from synthesis)
- WCAG criterion and conformance level
- Verification mode (`code` or `runtime`)
- File and element reference where applicable
- Clear description of the accessibility issue
- Concrete, specific remediation step
- Verification step: how to confirm the fix is correct, including
  whether browser/AT testing is required

### No-Findings Case

If the synthesis contains zero findings after Phase 4:
- Create a single P0 task: "Verify no findings — [scope], [date]"
- The task description must document: scope covered, 10 categories
  reviewed, WCAG version audited (2.1/2.2), date of review, and
  reviewer agents
- Do not produce an empty sprint

### Write the Sprint

Create `docs/sprints/SPRINT-NNN.md` following the standard sprint
template from `docs/sprints/README.md`:

```markdown
# Sprint NNN: Accessibility Audit — [scope] ([YYYY-MM-DD])

## Overview

[1-2 paragraphs: audit scope, total findings by severity, top 3
issues, WCAG version audited. Remind the reader that static LLM
review cannot fully validate dynamic behavior, screen reader output,
or focus management without browser and assistive technology testing.]

## Audit Summary

| Severity | Count |
|---|---|
| Critical (Level A) | N |
| High (Level AA) | N |
| Medium (Level AAA) | N |
| Low (Best Practice) | N |
| Total | N |

WCAG version: 2.1/2.2. Levels A and AA reviewed as standard
compliance requirement.

Intermediate audit artifacts: `docs/accessibility/AUDIT_NNN-*.md`

## Implementation Plan

### P0: Must Ship

[One task per Critical/High finding]

**Task: [Finding ID] — [Title]**
- Location: `path/to/file:line`
- WCAG: [criterion number and name]
- Level: [A / AA]
- Verification: [code / runtime]
- Issue: [accessibility problem description]
- Remediation: [specific fix]
- Verification: [how to confirm it's fixed; note if AT/browser testing required]

### P1: Ship If Capacity Allows

[One task per Medium finding, same format]

### Deferred

[Low findings with brief rationale]

## Definition of Done

- [ ] All P0 tasks completed and verified
- [ ] Runtime-verification findings tested in browser with AT where required
- [ ] No new accessibility issues introduced by the remediations
- [ ] Reviewer confirms task ordering was appropriate for dependencies
[add finding-specific verification items]

## Security Considerations

- Accessibility audit artifacts may reveal UX or compliance gaps —
  review before committing to public repos
- Task descriptions must be specific enough to be unambiguous when
  executed by an agent

## Dependencies

- AUDIT_NNN intermediate files: `docs/accessibility/AUDIT_NNN-*.md`

## Notes

Some findings require browser and assistive technology verification
(marked `runtime` in the Verification column). Include AT testing
in task execution for these items. This sprint was generated from
static code review against WCAG 2.1/2.2 and is a structured starting
point, not a conformance certification.
```

### Register and Hand Off

1. Register the sprint in the ledger:

   Use the `/ledger add NNN "Accessibility: [scope]"` skill. If it
   fails, instruct the user to run it manually:
   ```
   /ledger add NNN "Accessibility: [scope]"
   ```

2. Inform the user:

   > ✅ Accessibility audit complete. SPRINT-NNN has been created and
   > added to the ledger.
   >
   > **Note**: Some findings require browser/AT verification — include
   > this in task execution for items marked `runtime`.
   >
   > **Before running /sprint-work**, review the task ordering in
   > `docs/sprints/SPRINT-NNN.md`. Some remediations (e.g., fixing
   > ARIA roles before updating keyboard handlers) must be sequenced.
   >
   > When ready: `/sprint-work NNN`

---

## Output Checklist

At the end of this workflow, verify:

- [ ] `docs/accessibility/AUDIT_NNN-CLAUDE.md` — written using finding schema, ID prefix A
- [ ] `docs/accessibility/AUDIT_NNN-CODEX.md` — written using finding schema, ID prefix C
- [ ] Both files are non-empty (or single-agent warning added to synthesis)
- [ ] `docs/accessibility/AUDIT_NNN-SYNTHESIS.md` — unified findings with canonical S-prefix IDs
- [ ] `docs/accessibility/AUDIT_NNN-DEVILS-ADVOCATE.md` — Codex challenge complete
- [ ] Valid devil's advocate challenges incorporated into synthesis
- [ ] Rejected challenges documented with reasoning in synthesis
- [ ] `docs/sprints/SPRINT-NNN.md` — written with P0/P1/Deferred tiering
- [ ] Each P0/P1 task has: finding ID, WCAG criterion, level, verification mode,
      location, issue, remediation, verification guidance
- [ ] No-findings case handled if applicable
- [ ] Runtime-verification note included before `/sprint-work` instruction
- [ ] `/ledger add NNN` completed (or user instructed to run manually)
- [ ] User instructed to review task ordering, then run `/sprint-work NNN`

---

## Reference

- Sprint conventions: `docs/sprints/README.md`
- Accessibility audit artifacts: `docs/accessibility/`
- Audit family: `audit-*` commands in `commands/`
- WCAG 2.1: https://www.w3.org/TR/WCAG21/
- WCAG 2.2: https://www.w3.org/TR/WCAG22/
