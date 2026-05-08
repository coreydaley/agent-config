---
name: audit-responsive
description: Dual-agent responsive design audit — Claude and Codex review independently for mobile/tablet issues (viewport, breakpoints, touch targets, fluid layouts, typography, overflow, media), synthesize, devil's advocate pass, output as findings report. Invoke with a scope path or leave empty to audit the current working directory.
---

# Responsive Design Audit: Dual-Agent Review

You are orchestrating a dual-agent responsive design audit that produces a
findings report. Claude and Codex review independently for mobile and tablet
issues, findings are synthesized, Codex attacks the synthesis, and the final
output is a report written to `$AUDIT_DIR/REPORT.md`.

The scope to audit is provided in your input prompt. If no scope is specified,
audit the current working directory.

The `audit-responsive` finding schema extends the core schema with a
`Breakpoint` column that anchors each finding to the affected viewport range.

**Inherent limitations**: Static code review can identify structural
responsiveness issues but cannot validate visual rendering, layout reflow, or
touch behavior without browser and device testing. Findings marked `runtime`
require browser testing (DevTools device emulation at minimum, physical device
preferred) to confirm. This review is a structured starting point, not a
full cross-device compatibility certification.

## Scope Handling

Parse your input prompt for a path or paths to audit. Examples:
- No path specified → scope is the current working directory
- `app/views` → scope is `app/views`
- `app/views app/assets` → scope is multiple paths

Scope is validated as a path in Phase 1 — raw user input is never
interpolated into shell strings.

## Workflow Overview

This is a **5-phase workflow**:

1. **Orient** — Determine scope, identify frontend files, note existing tooling
2. **Independent Reviews** — Claude and Codex review in parallel (Codex in
   background, Claude simultaneously)
3. **Synthesis** — Deduplicate findings; flag agreements as higher confidence;
   calibrate severity
4. **Devil's Advocate** — Codex attacks the synthesis for false positives,
   severity miscalibrations, and gaps
5. **Report Output** — Produce `$AUDIT_DIR/REPORT.md`
   with findings as tasks for human review; present to user

---

## Finding Schema

All intermediate audit files must use this table format:

```
| ID | Severity | Title | Location | Breakpoint | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
|----|----------|-------|----------|------------|--------------|----------------|-----------------|----------------|
| A001 | High | Missing viewport meta | app/views/layouts/application.html.erb:3 | All | code | Causes unzoomed desktop render on mobile | Add <meta name="viewport" content="width=device-width, initial-scale=1"> | Code quote |
```

**ID prefix convention:**
- Claude's review: `A001`, `A002`... (Audit)
- Codex's review: `C001`, `C002`... (Codex)
- Synthesis: `S001`, `S002`... (Synthesis)

**Severity levels:** Critical, High, Medium, Low

**Breakpoint column**: The viewport range(s) affected. Use: `xs (<576px)`,
`sm (576–767px)`, `md (768–991px)`, `lg (992–1199px)`, `xl (≥1200px)`,
`All`, or a combination (e.g. `xs, sm`). When using a framework with
different breakpoints (Tailwind, Foundation), use those names instead.

**Verification column**: `code` (inspectable from source alone) or `runtime`
(requires browser/device testing to confirm).

**Default severity mapping:**

| Issue Type | Default Severity |
|---|---|
| Broken layout / content inaccessible at common viewport | Critical |
| Horizontal overflow / forced scrolling | High |
| Touch targets below 44×44 px / tap areas too close | High |
| Missing viewport meta tag | High |
| Fixed widths that cause reflow problems | Medium |
| Typography not scaling appropriately | Medium |
| Images not constrained / overflow container | Medium |
| Minor spacing/padding inconsistencies on small screens | Low |

Override upward when the issue blocks a primary user flow on a common device
size. Override downward when the affected breakpoint is rare in the project's
actual user base.

---

## Phase 1: Orient

**Goal**: Understand the scope, identify relevant files, note existing
responsive tooling, and determine the output location.

### Orient Steps

1. **Validate and resolve scope** from the input prompt:
   - If no path specified: scope is the current working directory
   - If a path is provided: verify the path exists
   - Exclude: `build/`, `dist/`, `.next/`, `.nuxt/`, generated files,
     vendored/third-party code, and binary assets — unless explicitly included
   - Store the resolved scope path — do not use raw input text in any Codex
     exec prompt string

2. **Identify relevant files** in the resolved scope:
   - HTML/template files (`.html`, `.htm`, `.erb`, `.haml`, `.slim`, `.jinja`)
   - CSS and style files (`.css`, `.scss`, `.sass`, `.less`)
   - Component files (`.jsx`, `.tsx`, `.vue`, `.svelte`, `.astro`)
   - JavaScript/TypeScript — for viewport-dependent logic or resize handlers
   - Config files — Tailwind config, Bootstrap overrides, breakpoint tokens

3. **No UI files found**: if no frontend files exist in the resolved scope,
   notify the user and stop. Do not create artifact files.

4. **Note existing responsive tooling** in the project:
   - CSS framework and version (Bootstrap, Tailwind, Foundation, etc.)
   - Custom breakpoint tokens or design system breakpoints
   - Any viewport testing tools (Percy, Chromatic, BrowserStack, etc.)

5. **Determine output location**:
   ```bash
   REMOTE=$(git remote get-url upstream 2>/dev/null || git remote get-url origin 2>/dev/null || echo "")
   ORG_REPO=$(echo "$REMOTE" | sed 's|.*github\.com[:/]||; s|\.git$||')
   REPORTS_BASE="$HOME/Reports/$ORG_REPO"
   REPORT_TS=$(date +%Y-%m-%dT%H-%M-%S)
   AUDIT_DIR="$REPORTS_BASE/audits/$REPORT_TS-responsive"
   mkdir -p "$AUDIT_DIR"
   ```
   Each audit run gets its own timestamped folder under
   `~/Reports/<org>/<repo>/audits/`, matching the layout
   `/sprint-plan` uses for sprint sessions. All audit artifacts
   for this run live in `$AUDIT_DIR`. Create this before launching
   Codex in Phase 2.
   Create this before launching Codex in Phase 2.

### Orient Deliverable

A brief orientation note (3-5 bullets) covering:
- Resolved scope and what it includes/excludes
- Frontend file types and count identified
- CSS framework and breakpoints detected
- The audit directory (`AUDIT_DIR`) for this run's artifacts

---

## Phase 2: Independent Reviews (Parallel)

**Goal**: Get two independent responsive design perspectives without
cross-contamination.

### Step 1 — Launch Codex in Background

Run this command, substituting the resolved scope and the literal value of
`AUDIT_DIR`:

```bash
codex exec "Perform a thorough responsive design audit of [RESOLVED_SCOPE] \
  for mobile and tablet viewports. \
  Write all findings to $AUDIT_DIR/codex.md using \
  this exact table format for each finding: \
  | ID | Severity | Title | Location | Breakpoint | Verification | Why It Matters | Recommended Fix | Evidence/Notes | \
  where ID uses prefix C (e.g. C001, C002). \
  Breakpoint column: xs (<576px), sm (576-767px), md (768-991px), \
  lg (992-1199px), xl (>=1200px), All, or framework-specific names. \
  Verification column: code (inspectable from source) or runtime \
  (requires browser/device testing). \
  Cover these 10 categories: \
  (1) Viewport meta tag — presence, correctness, no user-scalable=no. \
  (2) Fluid layouts — fixed pixel widths that prevent reflow; use of \
  percentage, vw/vh, or fr units; max-width usage. \
  (3) Breakpoint coverage — missing breakpoints for common device widths; \
  desktop-only CSS with no mobile override; breakpoint order issues \
  (mobile-first vs desktop-first). \
  (4) Typography scaling — font sizes that are too small (<16px body) \
  on mobile; lack of clamp() or responsive type scale; line-length \
  too wide/narrow at small viewports. \
  (5) Touch targets — interactive elements below 44x44px; tap targets \
  too close together (< 8px gap); hover-only interactions with no \
  touch equivalent. \
  (6) Horizontal overflow — elements wider than the viewport; \
  overflow-x not handled; tables, code blocks, or images causing \
  forced horizontal scroll. \
  (7) Images and media — missing max-width:100% on images; non-responsive \
  video/iframe embeds; missing srcset or picture element for HiDPI/small \
  screens; background-size not set for decorative images. \
  (8) Navigation and menus — desktop-only navigation with no mobile \
  alternative; hamburger menus that are inaccessible or too small; \
  dropdowns that are unusable on touch. \
  (9) Forms and inputs — input fields too small or misaligned on mobile; \
  missing autocomplete/inputmode/type attributes; labels not associated; \
  submit buttons below the minimum touch target size. \
  (10) Component-level issues — modals or dialogs that overflow viewport; \
  carousels or sliders with no swipe support; data tables with no \
  horizontal scroll container; cards or grid items that collapse poorly. \
  Grouping rule: when the same broken pattern appears across many \
  components, create one representative finding and document the \
  extent in Evidence/Notes rather than duplicating per instance. \
  Do not read or reference any other review file."
```

### Step 2 — Claude's Independent Review (Simultaneous)

While Codex runs, write your own independent responsive design review to
`$AUDIT_DIR/claude.md` using the same finding
schema (ID prefix `A`). Cover the same 10 categories:

1. **Viewport meta tag** — presence in layout templates; `width=device-width,
   initial-scale=1`; absence of `user-scalable=no` (also an accessibility
   issue, WCAG 1.4.4)
2. **Fluid layouts** — fixed `px` widths blocking reflow; percentage/fr/vw
   usage; `max-width` on containers
3. **Breakpoint coverage** — missing breakpoints for common device widths
   (360px, 375px, 768px, 1024px); desktop-only styles with no mobile
   override; mobile-first vs desktop-first consistency
4. **Typography scaling** — body font below 16px on mobile; absence of
   responsive type scale or `clamp()`; line-length extremes at small/large
   viewports
5. **Touch targets** — interactive elements below 44×44px; tap targets
   spaced < 8px apart; hover-only interactions (`:hover` without `:focus`
   or touch equivalent)
6. **Horizontal overflow** — elements wider than viewport; missing
   `overflow-x` handling; tables, code blocks, or images causing horizontal
   scroll
7. **Images and media** — missing `max-width: 100%` on images; non-responsive
   `<video>` or `<iframe>` embeds; missing `srcset`/`<picture>` for
   HiDPI or bandwidth-constrained devices
8. **Navigation and menus** — desktop-only navigation with no mobile
   alternative; hamburger menus below touch target minimums; touch-unfriendly
   dropdowns
9. **Forms and inputs** — inputs misaligned or too small on mobile; missing
   `autocomplete`, `inputmode`, or appropriate `type` attributes;
   submit buttons below touch target minimums
10. **Component-level issues** — modals overflowing viewport; carousels
    without swipe support; data tables without scroll containers; grid/card
    layouts that collapse poorly

When the same broken pattern appears across many components, create one
representative finding and document the extent in Evidence/Notes.

Wait for Codex to finish before proceeding to Phase 3.

---

## Phase 3: Synthesis

**Goal**: Produce a unified, deduplicated finding list with calibrated
severity and confidence.

### Synthesis Steps

1. **Verify both reviews exist and are non-empty**:
   - Check `$AUDIT_DIR/claude.md` and
     `$AUDIT_DIR/codex.md`
   - If one is missing or empty: proceed with single-agent synthesis and add
     warning: "⚠️ Single-agent synthesis — [agent] review was unavailable.
     Coverage may be incomplete."

2. **Deduplicate findings**:
   - Merge overlapping findings — note both source IDs (e.g. `A002, C003`)
   - Preserve the most specific `Location` and best `Evidence/Notes`
   - A single element may have multiple distinct responsive issues — keep
     them separate if remediation differs
   - Grouping rule: one representative finding per broken pattern, extent
     in Evidence/Notes
   - Agreement = higher confidence, not higher severity

3. **Calibrate severity**:
   - Re-evaluate using the severity mapping table from the Finding Schema
   - Override based on: whether the issue blocks a primary user flow, how
     common the affected device size is, and breadth of affected components

4. **Write synthesis** to `$AUDIT_DIR/synthesis.md`:

   ```markdown
   # Responsive Design Audit Synthesis — [REPORT_TS]

   ## Scope
   [Resolved scope path(s)]

   ## CSS Framework / Breakpoints
   [Framework detected, breakpoints used]

   ## Summary
   - Total findings: N (Critical: X, High: X, Medium: X, Low: X)
   - Reviewers: Claude (A-prefix), Codex (C-prefix)
   - [Single-agent warning if applicable]

   ## Unified Findings

   | ID | Severity | Title | Location | Breakpoint | Verification | Why It Matters | Recommended Fix | Evidence/Notes | Sources |
   |----|----------|-------|----------|------------|--------------|----------------|-----------------|----------------|---------|
   | S001 | ... | ... | ... | ... | ... | ... | ... | ... | A001, C002 |

   ## Findings Present in Only One Review
   [Note findings not corroborated by the other reviewer and why they are
   retained or dropped]
   ```

Phase 3 is complete when `synthesis.md` is written.

---

## Phase 4: Devil's Advocate

**Goal**: Challenge the synthesis for false positives, severity
miscalibrations, and missed findings.

```bash
codex exec "Read $AUDIT_DIR/synthesis.md. Your job \
  is to attack it, not improve it. Write your challenge to \
  $AUDIT_DIR/devils-advocate.md covering: \
  (1) False positives — findings that are actually correct responsive behavior \
  (e.g. an intentional fixed-width component, a desktop-only admin panel, or \
  a pattern that degrades gracefully on mobile). \
  (2) Severity miscalibrations — findings rated too high or too low given the \
  actual device breakdown and user flow impact. \
  (3) Missing findings — responsive issues both reviewers missed. \
  (4) Remediation steps that are incorrect, impractical, or would introduce \
  new layout or accessibility issues. \
  Be specific. Every challenge must cite the finding ID."
```

Once `devils-advocate.md` is written, read it and:

- **Remove** confirmed false positives from the working finding list
- **Recalibrate** severity where the challenge is valid and evidence supports it
- **Add** genuinely missed findings with new synthesis IDs
- **Document every rejected challenge** in a "Rejected Challenges" section at
  the bottom of `synthesis.md`:

  ```markdown
  ## Rejected Devil's Advocate Challenges

  | Finding/Claim | Reason Rejected |
  |---|---|
  | [Claim] | [Why not accepted] |
  ```

Phase 4 is complete when challenges are incorporated and rejections are documented.

---

## Phase 5: Report Output

**Goal**: Produce a findings report at
`$AUDIT_DIR/REPORT.md` with responsive findings
as prioritized tasks.

### Sprint Mapping Rules

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

Each sprint task must include:
- Finding ID (from synthesis)
- Affected breakpoint(s)
- Verification mode (`code` or `runtime`)
- File and element reference where applicable
- Clear description of the responsive problem
- Concrete, specific remediation step
- Verification step: how to confirm the fix, including required device sizes
  or browser DevTools emulation targets

### No-Findings Case

If the synthesis contains zero findings after Phase 4:
- Create a single P0 task: "Verify no findings — [scope], [date]"
- Document: scope covered, 10 categories reviewed, breakpoints tested, date,
  reviewer agents
- Do not produce an empty sprint

### Write the Report

Create `$AUDIT_DIR/REPORT.md`:

```markdown
# Responsive Design Audit — [scope] ([YYYY-MM-DD])

## Overview

[1-2 paragraphs: audit scope, total findings by severity, top 3 issues,
breakpoints covered. Remind the reader that static LLM review cannot fully
validate visual rendering, layout reflow, or touch behavior without browser
and device testing.]

## Audit Summary

| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Total | N |

CSS framework: [name + version]
Breakpoints reviewed: [list]

Intermediate audit artifacts: `$AUDIT_DIR/claude.md`,
`$AUDIT_DIR/codex.md`,
`$AUDIT_DIR/synthesis.md`,
`$AUDIT_DIR/devils-advocate.md`

## Implementation Plan

### P0: Must Ship

**Task: [Finding ID] — [Title]**
- Location: `path/to/file:line`
- Breakpoint: [affected viewport(s)]
- Verification: [code / runtime]
- Issue: [responsive problem description]
- Remediation: [specific fix]
- Verification: [how to confirm; specify DevTools emulation targets or physical device]

### P1: Ship If Capacity Allows

[Same format]

### Deferred

[Low findings with brief rationale]

## Definition of Done

- [ ] All P0 tasks completed and verified
- [ ] Runtime-verification findings tested in browser at specified breakpoints
- [ ] No new responsive regressions introduced
- [ ] Reviewer confirms task ordering is appropriate for dependencies
[add finding-specific verification items]

## Notes

Some findings require browser and/or device verification (marked `runtime`).
Test at minimum with Chrome DevTools device emulation at 375px (iPhone),
768px (iPad), and 1024px (iPad landscape / small laptop). This report was
generated from static code review and is a structured starting point,
not a cross-device compatibility certification.

## Dependencies

- Audit intermediate files: `$AUDIT_DIR/{claude,codex,synthesis,devils-advocate}.md`
```

### Hand Off

Inform the user:

> ✅ Responsive design audit complete. Report at
> `$AUDIT_DIR/REPORT.md`.
>
> **Note**: Findings marked `runtime` require browser/device testing to
> confirm — at minimum use Chrome DevTools at 375px, 768px, and 1024px.
>
> Run /sprint-plan against this report to create an actionable sprint when ready.

---

## Output Checklist

- [ ] `$AUDIT_DIR/claude.md` — finding schema, ID prefix A
- [ ] `$AUDIT_DIR/codex.md` — finding schema, ID prefix C
- [ ] Both non-empty (or single-agent warning in synthesis)
- [ ] `$AUDIT_DIR/synthesis.md` — canonical S-prefix IDs
- [ ] `$AUDIT_DIR/devils-advocate.md` — Codex challenge complete
- [ ] Valid challenges incorporated; rejections documented
- [ ] `$AUDIT_DIR/REPORT.md` — P0/P1/Deferred tiering
- [ ] Each P0/P1 task has: finding ID, breakpoint, verification mode, location,
      issue, remediation, verification guidance
- [ ] No-findings case handled if applicable
- [ ] Runtime-verification note included before hand-off
- [ ] No raw user input text in any Codex exec prompt

---

## Reference

- Report output: `~/Reports/<org>/<repo>/audits/<TS>-responsive/REPORT.md` (org/repo from upstream remote, falls back to origin)
- Responsive audit artifacts: `$AUDIT_DIR/{claude,codex,synthesis,devils-advocate}.md`
- MDN Responsive Design: https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Responsive_Design
- WCAG 1.4.4 (Resize Text): https://www.w3.org/WAI/WCAG21/Understanding/resize-text.html
- WCAG 1.4.10 (Reflow): https://www.w3.org/WAI/WCAG21/Understanding/reflow.html
