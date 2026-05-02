# Accessibility Audit Reference

Schema and severity reference for the `/audit-accessibility` command.
Audit artifacts are written outside this repo to
`~/Reports/<repo-path>/` (derived from `pwd`).

## Output

Each audit run produces five timestamp-prefixed files in
`~/Reports/<repo-path>/`:

| File | Description |
|------|-------------|
| `<TS>-audit-accessibility-claude.md` | Claude's independent accessibility review |
| `<TS>-audit-accessibility-codex.md` | Codex's independent accessibility review |
| `<TS>-audit-accessibility-synthesis.md` | Unified, deduplicated findings with calibrated severity |
| `<TS>-audit-accessibility-devils-advocate.md` | Codex's challenge pass against the synthesis |
| `<TS>-audit-accessibility-report.md` | Final findings report (the human-facing artifact) |

The report is reference material. To act on the findings, run
`/sprint-plan` with the report path as the seed prompt.

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
