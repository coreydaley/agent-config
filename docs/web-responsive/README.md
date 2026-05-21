# Responsive Design Audit Reference

Schema and severity reference for the `/audit-web-responsive` command.

Audit artifacts are written outside this repo to
`~/Reports/<org>/<repo>/audits/<TS>-web-responsive/` — `<org>/<repo>` is
derived from the `upstream` remote (falling back to `origin`), and
`<TS>` is the audit start timestamp (`YYYY-MM-DDTHH-MM-SS`).

## Output

Each audit run produces these files in its own timestamped `$AUDIT_DIR`:

| File | Description |
|------|-------------|
| `claude.md` | Claude's independent responsive design review (ID prefix `A`) |
| `codex.md` | Codex's independent responsive design review (ID prefix `C`) |
| `synthesis.md` | Unified, deduplicated findings (canonical `S`-prefix IDs); appends a "Rejected Devil's Advocate Challenges" section after Phase 4 |
| `devils-advocate.md` | Codex's challenge pass against the synthesis |
| `REPORT.md` | Final findings report (the human-facing artifact, P0/P1/Deferred sprint task layout) |

`REPORT.md` is reference material. To act on the findings, run
`/sprint-plan` with the report path as the seed prompt:

```
/sprint-plan ~/Reports/<org>/<repo>/audits/<TS>-web-responsive/REPORT.md
```

## Finding Schema

All intermediate audit files (`claude.md`, `codex.md`, `synthesis.md`)
use this table format:

```
| ID | Severity | Title | Location | Breakpoint | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

`synthesis.md` adds a `Sources` column listing the source review IDs each
unified finding merges (e.g. `A002, C003`).

**ID prefix convention:**
- Claude's review: `A001`, `A002`... (Audit)
- Codex's review: `C001`, `C002`... (Codex)
- Synthesis: `S001`, `S002`... (Synthesis canonical)

**Severity levels:** Critical, High, Medium, Low

**Breakpoint column**: The viewport range(s) affected. Default values:
`xs (<576px)`, `sm (576–767px)`, `md (768–991px)`, `lg (992–1199px)`,
`xl (≥1200px)`, `All`, or a combination (e.g. `xs, sm`). When the
project uses a framework with different breakpoint names (Tailwind,
Foundation), those names are used instead.

**Verification column**: `code` (inspectable from source alone) or
`runtime` (requires browser/device testing to confirm).

**Default severity mapping** (starting point — override based on whether
the issue blocks a primary user flow, how common the affected device
size is, and breadth of affected components):

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

## Categories Reviewed

The subagent reviews ten categories:

1. Viewport meta tag — presence, correctness, no `user-scalable=no`
2. Fluid layouts — fixed pixel widths blocking reflow; percentage / vw / vh / fr / clamp / max-width usage
3. Breakpoint coverage — common device widths, mobile-first vs desktop-first consistency
4. Typography scaling — body font ≥ 16px on mobile, responsive scale, `clamp()`
5. Touch targets — 44×44 px minimum, tap-target spacing, hover-only patterns
6. Horizontal overflow — elements wider than the viewport; `overflow-x` handling
7. Images and media — `max-width: 100%`, responsive video / iframe, `srcset` / `<picture>` for HiDPI
8. Navigation and menus — mobile navigation alternatives, hamburger usability, touch-friendly dropdowns
9. Forms and inputs — sizing on mobile, `autocomplete` / `inputmode` / `type`, label association
10. Component-level issues — modals, carousels, data tables, grid/card collapse behavior

## Sprint Mapping

`REPORT.md` maps findings to sprint priorities:

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

## Inherent Limitations

Static code review can identify structural responsiveness issues but
cannot validate visual rendering, layout reflow, or touch behavior
without browser and device testing. Findings marked `runtime` require
testing at minimum with Chrome DevTools device emulation at 375 px
(iPhone), 768 px (iPad), and 1024 px (iPad landscape / small laptop);
physical device testing is preferred for `runtime`-flagged findings.

This review is a structured starting point, not a cross-device
compatibility certification.

## References

- Subagent definition: [`../../subagents/audit-web-responsive.md`](../../subagents/audit-web-responsive.md)
- MDN Responsive Design: https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Responsive_Design
- WCAG 1.4.4 (Resize Text): https://www.w3.org/WAI/WCAG21/Understanding/resize-text.html
- WCAG 1.4.10 (Reflow): https://www.w3.org/WAI/WCAG21/Understanding/reflow.html
- WCAG 2.5.5 (Target Size): https://www.w3.org/WAI/WCAG21/Understanding/target-size.html
