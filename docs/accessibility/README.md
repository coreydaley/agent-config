# Accessibility Audit Artifacts

This directory contains intermediate artifacts produced by the
`/audit-accessibility` command.

## Naming Convention

Files are named using the sprint number (`NNN`) that matches the
sprint document produced at the end of the audit workflow:

| File | Description |
|------|-------------|
| `NNN-CLAUDE.md` | Claude's independent accessibility review |
| `NNN-CODEX.md` | Codex's independent accessibility review |
| `NNN-SYNTHESIS.md` | Unified, deduplicated findings with calibrated severity |
| `NNN-DEVILS-ADVOCATE.md` | Codex's challenge pass against the synthesis |

`NNN` matches the `SPRINT-NNN.md` document in `docs/sprints/` that
was produced by this audit run.

## Finding Schema

All audit files use this table format:

```
| ID | Severity | Title | Location | WCAG | Level | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

**ID prefix convention:**
- Claude's review: `A001`, `A002`... (Audit)
- Codex's review: `C001`, `C002`... (Codex)
- Synthesis: `S001`, `S002`... (Synthesis)

**Severity levels:** Critical, High, Medium, Low

**WCAG column**: Success criterion number (e.g., `1.4.3`) or
`Best Practice` for items beyond WCAG scope. WCAG 2.1/2.2 is the
normative reference.

**Level column**: `A`, `AA`, `AAA`, or `BP` (Best Practice).

**Verification column**: `code` (inspectable from source) or
`runtime` (requires browser and/or assistive technology testing).

**Default severity mapping:**

| WCAG Level | Default Severity |
|---|---|
| A | Critical |
| AA | High |
| AAA | Medium |
| Best Practice | Low |

Severity may be overridden based on actual exclusion severity,
task blockage, AT impact, and breadth of affected users.

## Inherent Limitations

These artifacts reflect static code review against WCAG 2.1/2.2.
They are a structured starting point, not a conformance
certification. Findings marked `runtime` in the Verification column
require browser and assistive technology testing to confirm.

## Security Note

These files may reveal UX details, design gaps, or compliance status
about the audited application. **Review before committing to a public
repository.**
