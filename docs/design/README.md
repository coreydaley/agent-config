# Design Audit Reference

Schema and severity reference for the `/audit-design` command.

Audit artifacts are written outside this repo to
`~/Reports/<org>/<repo>/audits/<TS>-design/` — `<org>/<repo>` is derived
from the `upstream` remote (falling back to `origin`), and `<TS>` is the
audit start timestamp (`YYYY-MM-DDTHH-MM-SS`).

## Output

Each audit run produces these files in its own timestamped `$AUDIT_DIR`:

| File | Description |
|------|-------------|
| `claude.md` | Claude's independent design review (ID prefix `A`) |
| `codex.md` | Codex's independent design review (ID prefix `C`) |
| `synthesis.md` | Unified, deduplicated findings (canonical `S`-prefix IDs); appends a "Rejected Devil's Advocate Challenges" section after Phase 4 |
| `devils-advocate.md` | Codex's challenge pass against the synthesis |
| `REPORT.md` | Final findings report (the human-facing artifact, P0/P1/Deferred sprint task layout) |

`REPORT.md` is reference material. To act on the findings, run
`/sprint-plan` with the report path as the seed prompt:

```
/sprint-plan ~/Reports/<org>/<repo>/audits/<TS>-design/REPORT.md
```

## Finding Schema

All intermediate audit files (`claude.md`, `codex.md`, `synthesis.md`)
use this table format:

```
| ID | Severity | Title | Location | Heuristic | Why It Matters | Recommended Fix | Evidence/Notes |
```

`synthesis.md` adds a `Sources` column listing the source review IDs each
unified finding merges (e.g. `A002, C003`).

**ID prefix convention:**
- Claude's review: `A001`, `A002`... (Audit)
- Codex's review: `C001`, `C002`... (Codex)
- Synthesis: `S001`, `S002`... (Synthesis canonical)

**Severity levels:** Critical, High, Medium, Low

Severity is assessed on user impact, breadth of affected surface, task
interruption severity, and cost of inconsistency. Agreement between
reviewers raises **confidence**, not severity.

**Heuristic column priority order:**

1. Project design system (if present) — always takes precedence
2. Cross-pattern consistency with existing project UI
3. Nielsen's heuristics (N#1–N#10)
4. Platform guidelines (Material Design, Apple HIG) as tiebreaker

When standards conflict, the finding notes the disagreement explicitly
rather than resolving silently.

## Categories Reviewed

The subagent reviews seven categories:

1. Layout and visual hierarchy — spacing, alignment, grid consistency,
   information priority
2. Typography — font scale, line height, weight usage, readability
3. Color and visual design — palette consistency, contrast, use of color
   to convey meaning
4. Component consistency — reuse patterns, prop/variant naming, visual
   coherence
5. Navigation and interaction patterns — affordances, feedback, error
   states, loading states
6. Design system adherence — token usage, component library compliance,
   deviations from established patterns
7. Mobile and responsive design — breakpoint behavior, touch targets,
   layout reflow (for deeper responsive coverage, see
   [`../web-responsive/README.md`](../web-responsive/README.md))

## Sprint Mapping

`REPORT.md` maps findings to sprint priorities:

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

Some design remediations depend on shared tokens or components — task
ordering should be reviewed before executing.

## Inherent Limitations

This is a workflow aid for human-reviewed design work, not an automated
scanner. LLM review can identify likely issues but cannot validate
visual rendering, user perception, or dynamic interaction without
browser/device testing. Treat the output as a structured starting point
for human judgment, not a guarantee of full coverage.

This audit overlaps with accessibility and responsive concerns. For deep
WCAG coverage use [`/audit-web-accessibility`](../accessibility-web/README.md);
for deep mobile/tablet viewport coverage use
[`/audit-web-responsive`](../web-responsive/README.md).

## References

- Subagent definition: [`../../subagents/audit-design.md`](../../subagents/audit-design.md)
- Nielsen's 10 Usability Heuristics: https://www.nngroup.com/articles/ten-usability-heuristics/
- Material Design: https://m3.material.io/
- Apple Human Interface Guidelines: https://developer.apple.com/design/human-interface-guidelines/
