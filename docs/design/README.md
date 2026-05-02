# Design Audit Reference

Schema and severity reference for the `/audit-design` command.
Audit artifacts are written outside this repo to
`~/Reports/<repo-path>/` (derived from `pwd`).

## Output

Each audit run produces five timestamp-prefixed files in
`~/Reports/<repo-path>/`:

| File | Description |
|------|-------------|
| `<TS>-audit-design-claude.md` | Claude's independent design review |
| `<TS>-audit-design-codex.md` | Codex's independent design review |
| `<TS>-audit-design-synthesis.md` | Unified, deduplicated findings with calibrated severity |
| `<TS>-audit-design-devils-advocate.md` | Codex's challenge pass against the synthesis |
| `<TS>-audit-design-report.md` | Final findings report (the human-facing artifact) |

The report is reference material. To act on the findings, run
`/sprint-plan` with the report path as the seed prompt.

## Finding Schema

All audit files use this table format:

```
| ID | Severity | Title | Location | Heuristic | Why It Matters | Recommended Fix | Evidence/Notes |
```

**ID prefix convention:**
- Claude's review: `A001`, `A002`... (Audit)
- Codex's review: `C001`, `C002`... (Codex)
- Synthesis: `S001`, `S002`... (Synthesis)

**Severity levels:** Critical, High, Medium, Low

**Heuristic column**: Maps each finding to a design standard in
priority order: (1) project design system, (2) cross-pattern
consistency, (3) Nielsen's heuristics (N#1–N#10), (4) platform
guidelines (Material Design, Apple HIG).

When standards conflict, the finding notes the disagreement
explicitly rather than resolving silently.
