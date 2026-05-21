---
name: audit-web-responsive
description: Dual-agent responsive design audit for web frontends — viewport, breakpoints, touch targets, fluid layouts, typography, overflow, media. Mobile and tablet viewports. For native Apple adaptive UI (size classes, iPad multitasking, visionOS windowing), use `audit-apple-adaptivity`.
---

# Web Responsive Design Audit

You are orchestrating a dual-agent responsive design audit for web
frontends across mobile and tablet viewports.

**Required reading**: Before starting, read [`lib/audit-framework.md`](../lib/audit-framework.md).
This file specifies only the audit-specific deltas.

**Audit identifier**: `web-responsive` — `$AUDIT_DIR` is
`~/Reports/<org>/<repo>/audits/<TS>-web-responsive/`

**Scope**: web frontend code (HTML, CSS, JS/TS components). For native
Apple adaptive UI (UISizeClass, ViewThatFits, iPad multitasking,
visionOS windowing, Dynamic Type AX5 layout), use `audit-apple-adaptivity`.

**Inherent limitations**: Static code review can identify structural
responsiveness issues but cannot validate visual rendering, layout
reflow, or touch behavior without browser and device testing. Findings
marked `runtime` require testing at minimum with Chrome DevTools device
emulation at 375 px (iPhone), 768 px (iPad), and 1024 px
(iPad landscape / small laptop); physical device testing is preferred.

---

## Schema extensions

Beyond the framework baseline, add:

| Column | Description |
|---|---|
| `Breakpoint` | Affected viewport range(s). Default: `xs (<576px)`, `sm (576–767px)`, `md (768–991px)`, `lg (992–1199px)`, `xl (≥1200px)`, `All`. When the project uses a framework with different breakpoint names (Tailwind, Foundation), use those instead. |
| `Verification` | `code` (inspectable from source) or `runtime` (requires browser/device testing) |

Full schema:
```
| ID | Severity | Title | Location | Breakpoint | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

---

## Categories

The audit reviews ten categories:

| # | Category | Covers |
|---|---|---|
| 1 | Viewport meta tag | Presence, correctness, no `user-scalable=no` |
| 2 | Fluid layouts | Fixed pixel widths blocking reflow; %/vw/vh/fr/clamp; max-width usage |
| 3 | Breakpoint coverage | Common device widths; mobile-first vs desktop-first consistency |
| 4 | Typography scaling | Body ≥16px on mobile; responsive scale; `clamp()`; line-length |
| 5 | Touch targets | 44×44 px minimum; tap-target spacing; hover-only patterns |
| 6 | Horizontal overflow | Elements wider than viewport; `overflow-x` handling |
| 7 | Images and media | `max-width: 100%`; responsive video/iframe; `srcset` / `<picture>` |
| 8 | Navigation and menus | Mobile-nav alternatives; hamburger usability; touch-friendly dropdowns |
| 9 | Forms and inputs | Sizing on mobile; `autocomplete` / `inputmode` / `type`; label association |
| 10 | Component-level | Modals, carousels, data tables, grid/card collapse behavior |

---

## Severity calibration

Default mapping (override based on whether the issue blocks a primary
user flow, how common the affected device size is, and breadth of
affected components):

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

---

## Phase 1: Audit-specific orient

### Tooling

None — pure-LLM audit. Reviewers note any existing responsive tooling
in the project (Percy, Chromatic, BrowserStack visual regression) so
findings can reference or defer to it.

### Emergency exit

None.

### Survey

Beyond the framework baseline:

- Identify relevant files: HTML/template files (.html, .htm, .erb,
  .haml, .slim, .jinja), CSS/SCSS/SASS/LESS, components (.jsx/.tsx/
  .vue/.svelte/.astro), config files (Tailwind config, Bootstrap
  overrides, breakpoint tokens)
- Note CSS framework and version (Bootstrap, Tailwind, Foundation,
  etc.) — affects breakpoint naming
- Identify custom breakpoint tokens or design-system breakpoints
- **If no frontend files found**: notify and stop. Do not create
  artifact files.

---

## Phase 2: Codex prompt body

Substitute into the canonical invocation (framework Phase 2 Step 1):

```text
Perform a thorough responsive design audit of [RESOLVED_SCOPE] for
mobile and tablet viewports. Write all findings to $AUDIT_DIR/codex.md
using this exact table format for each finding:
| ID | Severity | Title | Location | Breakpoint | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
where ID uses prefix C (e.g. C001, C002).

Breakpoint column: xs (<576px), sm (576-767px), md (768-991px),
lg (992-1199px), xl (>=1200px), All, or framework-specific names.
Verification column: code (inspectable from source) or runtime
(requires browser/device testing).

Cover these 10 categories:
(1) Viewport meta tag — presence, correctness, no user-scalable=no.
(2) Fluid layouts — fixed pixel widths that prevent reflow; use of
percentage, vw/vh, or fr units; max-width usage.
(3) Breakpoint coverage — missing breakpoints for common device widths;
desktop-only CSS with no mobile override; breakpoint order issues
(mobile-first vs desktop-first).
(4) Typography scaling — font sizes that are too small (<16px body)
on mobile; lack of clamp() or responsive type scale; line-length too
wide/narrow at small viewports.
(5) Touch targets — interactive elements below 44x44px; tap targets
too close together (< 8px gap); hover-only interactions with no touch
equivalent.
(6) Horizontal overflow — elements wider than the viewport;
overflow-x not handled; tables, code blocks, or images causing forced
horizontal scroll.
(7) Images and media — missing max-width:100% on images;
non-responsive video/iframe embeds; missing srcset or picture element
for HiDPI/small screens; background-size not set for decorative
images.
(8) Navigation and menus — desktop-only navigation with no mobile
alternative; hamburger menus that are inaccessible or too small;
dropdowns that are unusable on touch.
(9) Forms and inputs — input fields too small or misaligned on mobile;
missing autocomplete/inputmode/type attributes; labels not associated;
submit buttons below the minimum touch target size.
(10) Component-level issues — modals or dialogs that overflow
viewport; carousels or sliders with no swipe support; data tables
with no horizontal scroll container; cards or grid items that
collapse poorly.

Grouping rule: when the same broken pattern appears across many
components, create one representative finding and document the
extent in Evidence/Notes rather than duplicating per instance.

Do not read or reference any other review file.
```

## Phase 2: Claude review checklist

Same 10 categories. Apply the grouping rule: one representative
finding per broken pattern. Mark `Verification` carefully — many
responsive issues only appear on actual device emulation.

---

## Phase 4: Devil's advocate prompt body

```text
Read $AUDIT_DIR/synthesis.md. Your job is to attack it, not improve
it. Write your challenge to $AUDIT_DIR/devils-advocate.md covering:
(1) False positives — findings that are actually correct responsive
behavior (e.g. an intentional fixed-width component, a desktop-only
admin panel, or a pattern that degrades gracefully on mobile).
(2) Severity miscalibrations — findings rated too high or too low
given the actual device breakdown and user flow impact.
(3) Missing findings — responsive issues both reviewers missed.
(4) Remediation steps that are incorrect, impractical, or would
introduce new layout or accessibility issues.
Be specific. Every challenge must cite the finding ID.
```

---

## Phase 5: Sprint mapping override

Baseline P0/P1/Deferred mapping applies.

---

## Output checklist additions

Beyond framework baseline:

- [ ] Each P0/P1 task has: finding ID, breakpoint, verification mode,
      location, issue, remediation, verification guidance with specific
      DevTools emulation targets or physical device
- [ ] Runtime-verification note included in hand-off — at minimum test
      at 375 px, 768 px, 1024 px

---

## Reference

- Audit reference doc: [`docs/web-responsive/README.md`](../docs/web-responsive/README.md)
- Framework: [`lib/audit-framework.md`](../lib/audit-framework.md)
- MDN Responsive Design: https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Responsive_Design
- WCAG 1.4.4 (Resize Text): https://www.w3.org/WAI/WCAG21/Understanding/resize-text.html
- WCAG 1.4.10 (Reflow): https://www.w3.org/WAI/WCAG21/Understanding/reflow.html
- WCAG 2.5.5 (Target Size): https://www.w3.org/WAI/WCAG21/Understanding/target-size.html
