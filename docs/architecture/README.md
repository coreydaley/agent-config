# Architecture Audit Reference

Schema and severity reference for the `/audit-architecture` command.
Audit artifacts are written outside this repo to
`~/Reports/<repo-path>/` (derived from `pwd`).

## Output

Each audit run produces five timestamp-prefixed files in
`~/Reports/<repo-path>/`:

| File | Contents |
|---|---|
| `<TS>-audit-architecture-claude.md` | Claude's independent architecture review (ID prefix `A`) |
| `<TS>-audit-architecture-codex.md` | Codex's independent architecture review (ID prefix `C`) |
| `<TS>-audit-architecture-synthesis.md` | Unified findings after deduplication and devil's advocate (ID prefix `S`) |
| `<TS>-audit-architecture-devils-advocate.md` | Codex's challenge of the synthesis |
| `<TS>-audit-architecture-report.md` | Final findings report (the human-facing artifact) |

The report is reference material. To act on the findings, run
`/sprint-plan` with the report path as the seed prompt.

## Finding Schema

All audit files use this table format:

```
| ID | Severity | Title | Location | Pattern/Principle | Why It Matters | Alternative | Migration Cost | Recommended Fix | Evidence/Notes |
```

### Core Columns

| Column | Description |
|---|---|
| `ID` | Unique finding identifier with reviewer prefix (`A`, `C`, or `S`) |
| `Severity` | Critical / High / Medium / Low |
| `Title` | Short description of the issue |
| `Location` | File path and line number where applicable |
| `Why It Matters` | Impact on maintainability, extensibility, or defect rate |
| `Recommended Fix` | Concrete implementation step |
| `Evidence/Notes` | Observable evidence; code quote or reference |

### Architecture Extension Columns

| Column | Description |
|---|---|
| `Pattern/Principle` | Named architectural rule or observable trade-off in tension (e.g., `SOLID:SRP`, `DRY`, `Separation of Concerns`, `Low Coupling`, `YAGNI`). For agent-config repos: `Command/Skill Boundary`, `Agent Scope Creep`, `Prompt Composability`. When no formal principle applies, describe the trade-off explicitly. |
| `Alternative` | Specific alternative design to move toward — not "refactor this" but a concrete target. When no clear alternative exists: "Investigate options for [issue]". |
| `Migration Cost` | `Low`, `Medium`, or `High` — effort to change, including coordination risk and touching shared boundaries |

### Severity Anchors

| Severity | Meaning |
|---|---|
| Critical | Prevents correct behavior or creates an unmaintainable trajectory |
| High | Significantly impedes extensibility, causes repeated defects, or creates systematic blind spots |
| Medium | Notable friction, inconsistency, or a pattern that degrades over time |
| Low | Minor improvement backed by a named principle |

### Evidence Discipline

A finding without a named `Pattern/Principle` (or explicit trade-off
description) and a concrete `Alternative` is not a valid finding.
Opinion-only observations without a named architectural principle or
observable structural tension are omitted.

Reviewer agreement raises **confidence**, not severity.

## Synthesis Format

`<TS>-audit-architecture-synthesis.md` adds an extra column to the
unified table:

- `Sources` — the original reviewer IDs that contributed to the finding
  (e.g., `A001, C002`)

It also includes sections for:
- **Findings Present in Only One Review** — findings not corroborated
  by the other reviewer, with rationale for retaining or dropping
- **Rejected Devil's Advocate Challenges** — every challenge from the
  devil's advocate file that was not accepted, with explicit reasoning
