# Architecture Audit Reference

Schema and severity reference for the `/audit-architecture` command.

Audit artifacts are written outside this repo to
`~/Reports/<org>/<repo>/audits/<TS>-architecture/` — `<org>/<repo>` is
derived from the `upstream` remote (falling back to `origin`), and `<TS>`
is the audit start timestamp (`YYYY-MM-DDTHH-MM-SS`).

## Output

Each audit run produces these files in its own timestamped `$AUDIT_DIR`:

| File | Description |
|------|-------------|
| `claude.md` | Claude's independent architecture review (ID prefix `A`) |
| `codex.md` | Codex's independent architecture review (ID prefix `C`) |
| `synthesis.md` | Unified, deduplicated findings (canonical `S`-prefix IDs); appends a "Rejected Devil's Advocate Challenges" section after Phase 4 |
| `devils-advocate.md` | Codex's challenge pass against the synthesis |
| `REPORT.md` | Final findings report (the human-facing artifact, P0/P1/Deferred sprint task layout) |

`REPORT.md` is reference material. To act on the findings, run
`/sprint-plan` with the report path as the seed prompt:

```
/sprint-plan ~/Reports/<org>/<repo>/audits/<TS>-architecture/REPORT.md
```

## Finding Schema

All intermediate audit files (`claude.md`, `codex.md`, `synthesis.md`)
use this table format:

```
| ID | Severity | Title | Location | Pattern/Principle | Why It Matters | Alternative | Migration Cost | Recommended Fix | Evidence/Notes |
```

`synthesis.md` adds a `Sources` column listing the source review IDs each
unified finding merges (e.g. `A001, C002`).

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

Reviewer agreement raises **confidence**, not severity.

### Evidence Discipline

A finding without a named `Pattern/Principle` (or explicit trade-off
description) and a concrete `Alternative` is not a valid finding.
Opinion-only observations without a named architectural principle or
observable structural tension are omitted by the subagent.

## Categories Reviewed

The subagent reviews seven categories:

1. Module boundaries and separation of concerns
2. Coupling and cohesion
3. Naming and conventions
4. Data flow and state management
5. Extensibility and DRY
6. YAGNI and over-engineering
7. **Agent-config specific** — when auditing an agent-config repo,
   apply extra scrutiny to `commands/`, `skills/`, `agents/`, `prompts/`,
   `scripts/` structure: clarity of command/skill boundary, agent scope,
   invocation chain traceability, prompt duplication across files

## Sprint Mapping

`REPORT.md` maps findings to sprint priorities:

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

**Migration Cost nuance**: P0 tasks with `Migration Cost=High` carry a
"Requires team alignment and design discussion before execution" note —
architecture changes that touch shared boundaries shouldn't ship without
team validation.

## Synthesis Format

`synthesis.md` includes sections for:

- **Unified Findings** — deduplicated table with the `Sources` column
- **Findings Present in Only One Review** — uncorroborated findings with
  rationale for retaining or dropping
- **Rejected Devil's Advocate Challenges** — every challenge from the
  devil's advocate file that was not accepted, with explicit reasoning

## Inherent Limitations

LLM architectural review cannot replace domain knowledge about runtime
behavior, team conventions, or organizational constraints. Architecture
is uniquely susceptible to LLM overconfidence: unlike security (anchored
to CVEs / exploitability) or accessibility (anchored to WCAG / HIG),
architectural "correctness" is context-dependent. Treat every finding as
a hypothesis requiring team validation before execution. The evidence
discipline (named principle + concrete alternative) reduces noise but
cannot eliminate it.

## References

- Subagent definition: [`../../subagents/audit-architecture.md`](../../subagents/audit-architecture.md)
