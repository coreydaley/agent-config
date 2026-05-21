---
name: audit-design
description: Dual-agent UI/UX design audit — findings anchored to project design system → cross-pattern consistency → Nielsen heuristics → platform guidelines (in priority order). When auditing a Swift / Apple project, Apple HIG is promoted to top priority automatically. For Apple-specific HIG-anchored design review, prefer `audit-apple-design`; for mobile-web viewport behavior, use `audit-web-responsive`.
---

# Design Audit

You are orchestrating a dual-agent design and UX audit producing an
actionable findings report.

**Required reading**: Before starting, read [`lib/audit-framework.md`](../lib/audit-framework.md).
This file specifies only the audit-specific deltas.

**Audit identifier**: `design` — `$AUDIT_DIR` is
`~/Reports/<org>/<repo>/audits/<TS>-design/`

**Scope**: any frontend or UI code. Web (HTML/CSS/JS components),
mobile, or hybrid. For deep Apple HIG coverage use `audit-apple-design`;
for deep mobile-web viewport coverage use `audit-web-responsive`.

**Inherent limitations**: LLM review can identify likely issues but
cannot validate visual rendering, user perception, or dynamic
interaction without browser/device testing. Treat as a structured
starting point, not a guarantee of full coverage.

---

## Schema extensions

Beyond the framework baseline, add:

| Column | Description |
|---|---|
| `Heuristic` | The design standard the finding anchors to. See priority order below. |

Full schema:
```
| ID | Severity | Title | Location | Heuristic | Why It Matters | Recommended Fix | Evidence/Notes |
```

**Heuristic column priority order** (assess in this order; first match
wins, lower tiers are tiebreakers):

1. **Project design system** (if present) — always takes precedence
2. **Cross-pattern consistency** with existing project UI
3. **Nielsen's heuristics** (N#1–N#10)
4. **Platform guidelines** (Material Design, Apple HIG) as tiebreaker

**When auditing a Swift / Apple project**: Apple HIG is **promoted to
priority 2** (above Nielsen). Detect via `Package.swift`, `*.xcodeproj/`,
or `*.swift` file count.

When standards conflict, the finding notes the disagreement explicitly
rather than resolving silently.

---

## Categories

The audit reviews seven categories:

| # | Category | Covers |
|---|---|---|
| 1 | Layout and visual hierarchy | Spacing, alignment, grid consistency, information priority |
| 2 | Typography | Font scale, line height, weight usage, readability |
| 3 | Color and visual design | Palette consistency, contrast, use of color to convey meaning |
| 4 | Component consistency | Reuse patterns, prop/variant naming, visual coherence |
| 5 | Navigation and interaction patterns | Affordances, feedback, error states, loading states |
| 6 | Design system adherence | Token usage, component library compliance, deviations from established patterns |
| 7 | Mobile and responsive design | Breakpoint behavior, touch targets, layout reflow (use `audit-web-responsive` for deep coverage) |

---

## Severity calibration

| Severity | Anchor |
|---|---|
| **Critical** | User cannot complete a primary task; broken interactive surface; total brand inconsistency |
| **High** | Significant task interruption; pattern broken on a high-traffic surface; large breadth of affected components |
| **Medium** | Notable inconsistency or friction; affects secondary flows |
| **Low** | Aesthetic preference backed by a named heuristic; minor inconsistency |

Severity is assessed on user impact, breadth of affected surface, task
interruption severity, and cost of inconsistency. Distinguish between
aesthetic opinion and user-impact evidence.

---

## Phase 1: Audit-specific orient

### Tooling

None — design is a pure-LLM audit.

### Emergency exit

None.

### Survey

Beyond the framework baseline:

- Identify frontend file types: HTML, CSS/SCSS/LESS/SASS, components
  (.jsx/.tsx/.vue/.svelte/.astro), Angular templates, design tokens,
  Storybook stories
- **Detect Apple project** (`Package.swift`, `*.xcodeproj/`, `*.swift`
  count) — if Apple, note that HIG is promoted in heuristic priority
- Look for an explicit design system: token files, component library,
  documented conventions, Figma references
- If no frontend files found: notify the user and stop — do not create
  artifact files

---

## Phase 2: Codex prompt body

Substitute into the canonical invocation (framework Phase 2 Step 1):

```text
Perform a thorough design and UX review of [RESOLVED_SCOPE].
Write all findings to $AUDIT_DIR/codex.md using this exact table
format for each finding:
| ID | Severity | Title | Location | Heuristic | Why It Matters | Recommended Fix | Evidence/Notes |
where ID uses prefix C (e.g. C001, C002).

Heuristic column priority: (1) project design system if present,
(2) consistency with existing project UI patterns, (3) Nielsen
heuristics (N#1-N#10), (4) platform guidelines (Material Design,
Apple HIG) as tiebreaker. WHEN AUDITING A SWIFT / APPLE PROJECT (look
for Package.swift, *.xcodeproj, or numerous *.swift files), promote
Apple HIG to priority 2 above Nielsen.

When standards conflict, note the disagreement explicitly.

Cover these design categories:
(1) Layout and visual hierarchy — spacing, alignment, grid consistency,
information priority.
(2) Typography — font scale, line height, weight usage, readability.
(3) Color and visual design — palette consistency, contrast, use of
color to convey meaning.
(4) Component consistency — reuse patterns, prop/variant naming,
visual coherence across similar components.
(5) Navigation and interaction patterns — affordances, feedback,
error states, loading states.
(6) Design system adherence — token usage, component library
compliance, deviations from established patterns.
(7) Mobile and responsive design — breakpoint behavior, touch
targets, layout reflow.

Rate severity on: user impact, breadth of affected surface, task
interruption severity, cost of inconsistency. Distinguish between
aesthetic opinion and user-impact evidence.

Do not read or reference any other review file.
```

## Phase 2: Claude review checklist

Same 7 categories. Apply the heuristic priority order; on Apple
projects promote HIG to priority 2. Look for established token files
or component libraries first before falling back to Nielsen.

---

## Phase 4: Devil's advocate prompt body

```text
Read $AUDIT_DIR/synthesis.md. Your job is to attack it, not improve
it. Write your challenge to $AUDIT_DIR/devils-advocate.md covering:
(1) False positives — findings that reflect intentional design choices
rather than actual problems.
(2) Severity miscalibrations — findings rated too high or too low
given actual user impact and breadth.
(3) Missing findings — design issues both reviewers missed.
(4) Remediation steps that are impractical or would introduce new
inconsistencies.
Be specific. Every challenge must cite the finding ID.
```

---

## Phase 5: Sprint mapping override

Baseline P0/P1/Deferred mapping applies. Note in hand-off: some design
remediations depend on shared tokens or components — review the task
ordering before executing.

---

## Output checklist additions

Beyond framework baseline:

- [ ] Each P0/P1 task has: finding ID, location, heuristic, issue,
      remediation, verification
- [ ] When auditing an Apple project, HIG-anchored findings dominate
      over Nielsen-anchored ones in the heuristic column

---

## Reference

- Audit reference doc: [`docs/design/README.md`](../docs/design/README.md)
- Framework: [`lib/audit-framework.md`](../lib/audit-framework.md)
- Nielsen's 10 Usability Heuristics: https://www.nngroup.com/articles/ten-usability-heuristics/
- Material Design: https://m3.material.io/
- Apple HIG: https://developer.apple.com/design/human-interface-guidelines/
