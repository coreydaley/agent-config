# Security Audit Reference

Schema and severity reference for the `/audit-security` command.
Audit artifacts are written outside this repo to
`~/Reports/<repo-path>/` (derived from `pwd`).

## Output

Each audit run produces five timestamp-prefixed files in
`~/Reports/<repo-path>/`:

| File | Contents |
|------|----------|
| `<TS>-audit-security-claude.md` | Claude's independent security review |
| `<TS>-audit-security-codex.md` | Codex's independent security review |
| `<TS>-audit-security-synthesis.md` | Unified findings (canonical `S`-prefix IDs) |
| `<TS>-audit-security-devils-advocate.md` | Codex's challenge of the synthesis |
| `<TS>-audit-security-report.md` | Final findings report (the human-facing artifact) |

The report is reference material. To act on the findings, run
`/sprint-plan` with the report path as the seed prompt.

## Finding Schema

All intermediate files use this table format:

```
| ID | Severity | Title | Location | Why It Matters | Recommended Fix | Evidence/Notes |
```

**ID prefixes:**
- `A` — Claude (Audit): `A001`, `A002`...
- `C` — Codex: `C001`, `C002`...
- `S` — Synthesis canonical: `S001`, `S002`...

**Severity:** Critical, High, Medium, Low

Severity is assessed on evidence (impact, exploitability, blast radius,
reachability) — not on the number of reviewers who flagged it.

## Sensitive Content

These files describe security vulnerabilities and may contain exploit
details, exposed credential patterns, or descriptions of attack paths.
Because they live under `~/Reports/` (outside any git repo by default),
they don't risk accidental commit. Review before sharing.
