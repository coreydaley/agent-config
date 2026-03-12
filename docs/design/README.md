# Design Audit Artifacts

This directory contains intermediate artifacts produced by the
`/audit-design` command.

## Naming Convention

Files are named using the sprint number (`NNN`) that matches the
sprint document produced at the end of the audit workflow:

| File | Description |
|------|-------------|
| `NNN-CLAUDE.md` | Claude's independent design review |
| `NNN-CODEX.md` | Codex's independent design review |
| `NNN-SYNTHESIS.md` | Unified, deduplicated findings with calibrated severity |
| `NNN-DEVILS-ADVOCATE.md` | Codex's challenge pass against the synthesis |

`NNN` matches the `SPRINT-NNN.md` document in `docs/sprints/` that
was produced by this audit run.

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

## Security Note

These files may reveal UI/UX details, design system structure, or
compliance gaps about the audited application. **Review before
committing to a public repository.**
