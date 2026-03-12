# Security Audit Reference

This directory stores intermediate artifacts produced by the
`/audit-security` command during a security review.

## Relationship to Sprints

`/audit-security` produces a standard `docs/sprints/SPRINT-NNN.md`
sprint document as its final output. The sprint NNN matches the
intermediate files stored here. Execute the sprint with `/sprint-work NNN`.

The `audit-*` command family uses this pattern:
- Intermediate working files → `docs/security/`
- Final executable output → `docs/sprints/SPRINT-NNN.md`

## Naming Convention

All files use the sprint number `NNN` from the audit run:

| File | Contents |
|------|----------|
| `NNN-CLAUDE.md` | Claude's independent security review |
| `NNN-CODEX.md` | Codex's independent security review |
| `NNN-SYNTHESIS.md` | Unified findings (with canonical S-prefix IDs) |
| `NNN-DEVILS-ADVOCATE.md` | Codex's challenge of the synthesis |

`NNN` is the sprint number assigned at the start of the audit run.
A finding `S003` in `AUDIT-004-SYNTHESIS.md` corresponds to `SPRINT-004.md`.

## Finding Schema

All intermediate files use this table format:

```
| ID | Severity | Title | Location | Why It Matters | Recommended Fix | Evidence/Notes |
|----|----------|-------|----------|----------------|-----------------|----------------|
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

**Review these files before committing them to a public repository.**
Consider adding `docs/security/` to `.gitignore` if the repo is public
and audits are run before issues are remediated.
