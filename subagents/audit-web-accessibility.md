---
name: audit-web-accessibility
description: Dual-agent web accessibility audit against WCAG 2.1/2.2 — HTML/CSS/JS/component files. For native Apple platforms (SwiftUI / UIKit / AppKit), use `audit-apple-accessibility`.
---

# Web Accessibility Audit

You are orchestrating a dual-agent web accessibility audit against
WCAG 2.1/2.2.

**Required reading**: Before starting, read [`lib/audit-framework.md`](../lib/audit-framework.md).
This file specifies only the audit-specific deltas.

**Audit identifier**: `web-accessibility` — `$AUDIT_DIR` is
`~/Reports/<org>/<repo>/audits/<TS>-web-accessibility/`

**Scope**: web frontend code (HTML, CSS, JS/TS, components). For
native Apple platforms (SwiftUI / UIKit / AppKit / WatchKit), use
`audit-apple-accessibility`.

**Inherent limitations**: Static code review can identify likely
issues but cannot fully validate dynamic behavior, screen reader
output, or focus management without browser and assistive technology
testing. Findings marked `runtime` require browser/AT testing to
confirm. Not a WCAG conformance certification.

---

## Schema extensions

Beyond the framework baseline, add:

| Column | Description |
|---|---|
| `WCAG` | Success criterion number (e.g. `1.4.3`) or `Best Practice` for items beyond WCAG scope. WCAG 2.1/2.2 is the normative reference. |
| `Level` | `A`, `AA`, `AAA`, or `BP` (Best Practice). |
| `Verification` | `code` (inspectable from source) or `runtime` (requires browser and/or assistive technology testing) |

Full schema:
```
| ID | Severity | Title | Location | WCAG | Level | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

---

## Categories

The audit reviews ten WCAG-anchored categories:

| # | Category | Anchors |
|---|---|---|
| 1 | Semantic structure & heading hierarchy | Landmark regions, heading levels, list markup |
| 2 | Images & non-text content | WCAG 1.1.1 |
| 3 | Color & contrast | WCAG 1.4.3 (minimum), 1.4.11 (non-text), 1.4.1 (not sole means) |
| 4 | Keyboard navigation & tab order | WCAG 2.1.1, 2.1.2 |
| 5 | Focus management & focus visibility | WCAG 2.4.3, 2.4.7, 2.4.11, 2.4.12 |
| 6 | ARIA usage | Roles, states, properties; avoid misuse |
| 7 | Form labels & error messages | WCAG 1.3.1, 3.3.1, 3.3.2 |
| 8 | Dynamic content & live regions | WCAG 4.1.3 |
| 9 | Motion & animation | WCAG 2.3.3 (`prefers-reduced-motion`), 2.2.2 |
| 10 | Cognitive accessibility | WCAG 2.2.1, 3.3.4, 3.2.3 |

---

## Severity calibration

WCAG level is the starting point; override based on actual exclusion
severity, task blockage, AT impact, and breadth of affected users.

| WCAG Level | Default Severity | Rationale |
|---|---|---|
| A | Critical | Blocking for assistive technology users |
| AA | High | Standard compliance requirement |
| AAA | Medium | Enhanced accessibility |
| Best Practice | Low | Beyond WCAG scope but recommended |

---

## Phase 1: Audit-specific orient

### Tooling

None — pure-LLM audit. Reviewers note any existing accessibility
tooling (axe-core, Lighthouse CI, pa11y, jest-axe) so findings can
reference or defer to it.

### Emergency exit

None.

### Survey

Beyond the framework baseline:

- Identify HTML files (.html, .htm), components (.jsx/.tsx/.vue/
  .svelte/.astro), Angular templates, CSS for contrast/focus/motion,
  JS/TS for ARIA manipulation and keyboard handling, image assets in
  markup
- Note existing accessibility tooling
- **If no frontend files found**: notify and stop. Do not create
  artifact files.

---

## Phase 2: Codex prompt body

Substitute into the canonical invocation (framework Phase 2 Step 1):

```text
Perform a thorough accessibility review of [RESOLVED_SCOPE] against
WCAG 2.1/2.2. Write all findings to $AUDIT_DIR/codex.md using this
exact table format for each finding:
| ID | Severity | Title | Location | WCAG | Level | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
where ID uses prefix C (e.g. C001, C002).

WCAG column: use criterion number (e.g. 1.4.3) or Best Practice.
Level column: A, AA, AAA, or BP.
Verification column: code (inspectable from source) or runtime
(requires browser/AT testing).
Default severity: Level A=Critical, AA=High, AAA=Medium, BP=Low;
override based on actual exclusion severity and breadth.

Cover these 10 categories:
(1) Semantic structure and heading hierarchy.
(2) Images and non-text content (WCAG 1.1.1).
(3) Color and contrast (WCAG 1.4.3 minimum contrast, 1.4.11 non-text
contrast).
(4) Keyboard navigation and tab order.
(5) Focus management and focus visibility (WCAG 2.4.3, 2.4.7, 2.4.11,
2.4.12).
(6) ARIA usage — roles, states, properties; avoid misuse.
(7) Form labels and error messages (WCAG 1.3.1, 3.3.1, 3.3.2).
(8) Dynamic content and live regions (WCAG 4.1.3).
(9) Motion and animation — prefers-reduced-motion (WCAG 2.3.3).
(10) Cognitive accessibility — error messages, consistency,
timeouts (WCAG 2.2.1, 3.3.4).

Grouping rule: when the same broken pattern appears across many
components, create one representative finding and document the extent
in Evidence/Notes rather than duplicating per instance.

Do not read or reference any other review file.
```

## Phase 2: Claude review checklist

Same 10 categories. Mark Verification carefully — focus restoration
and live-region behavior often require runtime testing. Apply the
grouping rule for repeated patterns.

---

## Phase 4: Devil's advocate prompt body

```text
Read $AUDIT_DIR/synthesis.md. Your job is to attack it, not improve
it. Write your challenge to $AUDIT_DIR/devils-advocate.md covering:
(1) False positives — findings that are actually accessible in
context (e.g. an element with an accessible name from a parent
container, or a pattern that is correct for its ARIA role).
(2) Severity miscalibrations — findings rated too high or too low
given the actual AT impact and user exclusion severity.
(3) Missing findings — accessibility issues that both reviewers
missed.
(4) Remediation steps that are incorrect, incomplete, or would
themselves introduce new accessibility issues.
Be specific. Every challenge must cite the finding ID and the WCAG
criterion if applicable.
```

---

## Phase 5: Sprint mapping override

Baseline P0/P1/Deferred mapping applies. Hand-off note: some findings
require browser/AT verification — include this in task execution for
items marked `runtime`.

---

## Output checklist additions

Beyond framework baseline:

- [ ] Each task has: finding ID, WCAG criterion, level, verification
      mode, location, issue, remediation, verification guidance
- [ ] Runtime-verification note included in hand-off

---

## Reference

- Audit reference doc: [`docs/web-accessibility/README.md`](../docs/web-accessibility/README.md)
- Framework: [`lib/audit-framework.md`](../lib/audit-framework.md)
- WCAG 2.1: https://www.w3.org/TR/WCAG21/
- WCAG 2.2: https://www.w3.org/TR/WCAG22/
