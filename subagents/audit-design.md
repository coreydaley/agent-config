---
name: audit-design
description: Dual-agent design audit — Claude and Codex review UI/UX independently, synthesize findings, devil's advocate pass, output as findings report. Invoke with a scope path or leave empty to audit the current working directory.
---

# Design Audit: Dual-Agent Review

You are orchestrating a dual-agent design audit that produces an
findings report. Claude and Codex review independently,
findings are synthesized, Codex attacks the synthesis, and the final
output is a sprint document written to `$AUDIT_DIR/REPORT.md`.

The scope to audit is provided in your input prompt. If no scope is
specified, audit the current working directory.

The `audit-design` finding schema extends the core schema with a
`Heuristic` column that anchors each finding to a normative design standard.

**Inherent limitations**: This is a workflow aid for human-reviewed
design work, not an automated scanner. LLM review can identify likely
issues but cannot validate visual rendering, user perception, or
dynamic interaction without browser testing. Treat the output as a
structured starting point for human judgment, not a guarantee of full
coverage.

## Scope Handling

Parse your input prompt for a path or paths to audit. Examples:
- No path specified → scope is the current working directory
- `src/components` → scope is `src/components`
- `src/components src/pages` → scope is multiple paths

Scope is validated as a path in Phase 1 before being used anywhere else —
raw user input is never interpolated into shell strings.

## Workflow Overview

This is a **5-phase workflow**:

1. **Orient** — Determine scope, identify frontend files
2. **Independent Reviews** — Claude and Codex review in parallel (Codex
   in background, Claude simultaneously)
3. **Synthesis** — Deduplicate findings; flag agreements as higher confidence;
   calibrate severity
4. **Devil's Advocate** — Codex attacks the synthesis for false positives,
   severity miscalibrations, and gaps
5. **Report Output** — Produce `$AUDIT_DIR/REPORT.md` with findings as tasks for human review;
   present to user for review

---

## Finding Schema

All intermediate audit files must use this table format:

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
resolving silently.

---

## Phase 1: Orient

**Goal**: Understand the scope, identify frontend files, and determine
the output location.

### Orient Steps

1. **Validate and resolve scope** from the input prompt:
   - If no path specified: scope is the current working directory
   - If a path is provided: verify the path exists
   - Exclude: `build/`, `dist/`, `.next/`, `.nuxt/`, generated files,
     vendored/third-party UI code, and binary assets
   - Store the resolved scope path — do not use raw input text in
     any Codex exec prompt string

2. **Identify frontend files** in the resolved scope:
   - HTML files (`.html`, `.htm`)
   - CSS and style files (`.css`, `.scss`, `.sass`, `.less`)
   - Component files (`.jsx`, `.tsx`, `.vue`, `.svelte`, `.astro`)
   - Angular templates and components
   - Design tokens and theme files
   - Storybook stories

3. **No UI files found**: if no frontend files exist in the resolved
   scope, notify the user and stop. Do not create a sprint or artifact files.

4. **Determine output location**:
   ```bash
   REMOTE=$(git remote get-url upstream 2>/dev/null || git remote get-url origin 2>/dev/null || echo "")
   ORG_REPO=$(echo "$REMOTE" | sed 's|.*github\.com[:/]||; s|\.git$||')
   REPORTS_BASE="$HOME/Reports/$ORG_REPO"
   REPORT_TS=$(date +%Y-%m-%dT%H-%M-%S)
   AUDIT_DIR="$REPORTS_BASE/audits/$REPORT_TS-design"
   mkdir -p "$AUDIT_DIR"
   ```
   Each audit run gets its own timestamped folder under
   `~/Reports/<org>/<repo>/audits/`, matching the layout
   `/sprint-plan` uses for sprint sessions. All audit artifacts
   for this run live in `$AUDIT_DIR`. Create this before launching
   Codex in Phase 2.

### Orient Deliverable

A brief orientation note (3-5 bullets) covering:
- Resolved scope and what it includes/excludes
- Frontend file types and count identified
- Any design system or token files found
- Audit output directory (`AUDIT_DIR`) — all artifacts for this audit run live here

---

## Phase 2: Independent Reviews (Parallel)

**Goal**: Get two independent design perspectives without cross-contamination.

### Step 1 — Launch Codex in Background

Run this command, substituting the resolved scope and the literal value of `AUDIT_DIR`:

```bash
codex exec "Perform a thorough design and UX review of [RESOLVED_SCOPE]. \
  Write all findings to $AUDIT_DIR/codex.md using this \
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
`$AUDIT_DIR/claude.md` using the same finding schema
(ID prefix `A`). Cover the same seven categories:

1. **Layout and visual hierarchy**
2. **Typography**
3. **Color and visual design**
4. **Component consistency**
5. **Navigation and interaction patterns**
6. **Design system adherence**
7. **Mobile and responsive design**

Apply the Heuristic column priority order as documented in the
Finding Schema section. Look for established token files or component
libraries first before falling back to Nielsen heuristics.

Wait for Codex to finish before proceeding to Phase 3.

---

## Phase 3: Synthesis

**Goal**: Produce a unified, deduplicated finding list with calibrated
severity and confidence.

### Synthesis Steps

1. **Verify both reviews exist and are non-empty**:
   - If one is missing or empty: proceed with single-agent synthesis
     and add warning: "⚠️ Single-agent synthesis — [agent] review was
     unavailable. Coverage may be incomplete."

2. **Deduplicate findings**:
   - Merge overlapping findings — note both source IDs
   - Do not flatten findings with different affected components or
     distinct remediation steps
   - Agreement = higher confidence, not higher severity

3. **Calibrate severity**:
   - Re-evaluate based on: user impact, breadth, task interruption
     severity, cost of inconsistency
   - Distinguish between aesthetic opinion and user-impact evidence

4. **Write synthesis** to `$AUDIT_DIR/synthesis.md`:

   ```markdown
   # Design Audit Synthesis — [REPORT_TS]

   ## Scope
   [Resolved scope path(s)]

   ## Summary
   - Total findings: N (Critical: X, High: X, Medium: X, Low: X)
   - Reviewers: Claude (A-prefix), Codex (C-prefix)

   ## Unified Findings

   | ID | Severity | Title | Location | Heuristic | Why It Matters | Recommended Fix | Evidence/Notes | Sources |
   |----|----------|-------|----------|-----------|----------------|-----------------|----------------|---------|

   ## Findings Present in Only One Review
   ```

---

## Phase 4: Devil's Advocate

**Goal**: Challenge the synthesis for false positives, severity
miscalibrations, and missed findings.

```bash
codex exec "Read $AUDIT_DIR/synthesis.md. Your job is \
  to attack it, not improve it. Write your challenge to \
  $AUDIT_DIR/devils-advocate.md covering: \
  (1) False positives — findings that reflect intentional design \
  choices rather than actual problems. \
  (2) Severity miscalibrations — findings rated too high or too low \
  given actual user impact and breadth. \
  (3) Missing findings — design issues both reviewers missed. \
  (4) Remediation steps that are impractical or would introduce new \
  inconsistencies. \
  Be specific. Every challenge must cite the finding ID."
```

Incorporate valid challenges: remove false positives, recalibrate severity,
add missed findings, document every rejected challenge in synthesis.

---

## Phase 5: Report Output

### Sprint Mapping Rules

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

Each sprint task must include: finding ID, file/component reference,
issue description, remediation, heuristic reference, verification step.

### Write the Sprint

Create `$AUDIT_DIR/REPORT.md`:

```markdown
# Design Audit — [scope] ([YYYY-MM-DD])

## Overview
[1-2 paragraphs. Remind the reader that static LLM review cannot
validate visual rendering or dynamic interaction without browser testing.]

## Audit Summary
| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Total | N |

## Implementation Plan

### P0: Must Ship
**Task: [Finding ID] — [Title]**
- Location: `path/to/file:line`
- Heuristic: [standard this violates]
- Issue: [design problem description]
- Remediation: [specific fix]
- Verification: [how to confirm]

### P1: Ship If Capacity Allows
### Deferred

## Definition of Done
- [ ] All P0 tasks completed and verified
- [ ] No new design inconsistencies introduced

## Dependencies
- Audit intermediate files: `$AUDIT_DIR/{claude,codex,synthesis,devils-advocate}.md`
```

### Hand Off

   > ✅ Design audit complete.
   >
   > **Report:** <literal absolute path to $AUDIT_DIR/REPORT.md>
   >
   > **Next:** Run `/sprint-plan` against the report to create an actionable sprint:
   >
   > ```
   > /sprint-plan <literal absolute path>
   > ```
   >
   > **Note:** Some design remediations may depend on shared tokens or components — review the task ordering before executing.

Substitute the literal absolute path of `$AUDIT_DIR/REPORT.md`
(e.g. `/Users/corey/Reports/myorg/myrepo/audits/2026-04-22T10-30-00-design/REPORT.md`)
so the user can copy-paste the `/sprint-plan` command directly.

---

## Output Checklist

- [ ] `$AUDIT_DIR/claude.md` — finding schema, ID prefix A
- [ ] `$AUDIT_DIR/codex.md` — finding schema, ID prefix C
- [ ] Both non-empty (or single-agent warning in synthesis)
- [ ] `$AUDIT_DIR/synthesis.md` — canonical S-prefix IDs
- [ ] `$AUDIT_DIR/devils-advocate.md` — Codex challenge complete
- [ ] Valid challenges incorporated; rejections documented
- [ ] `$AUDIT_DIR/REPORT.md` — P0/P1/Deferred tiering
- [ ] Each P0/P1 task has: finding ID, location, heuristic, issue, remediation, verification
- [ ] No-findings case handled
- [ ] No raw user input text in any Codex exec prompt
