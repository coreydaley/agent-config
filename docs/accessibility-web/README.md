# Web Accessibility Audit Reference

Schema and severity reference for the `/audit-accessibility-web` command.
For native Apple platforms, see [`../accessibility-apple/README.md`](../accessibility-apple/README.md).

Audit artifacts are written outside this repo to
`~/Reports/<org>/<repo>/audits/<TS>-accessibility/` — `<org>/<repo>` is
derived from the `upstream` remote (falling back to `origin`), and `<TS>`
is the audit start timestamp (`YYYY-MM-DDTHH-MM-SS`).

## Output

Each audit run produces these files in its own timestamped
`$AUDIT_DIR`:

| File | Description |
|------|-------------|
| `claude.md` | Claude's independent web accessibility review (ID prefix `A`) |
| `codex.md` | Codex's independent web accessibility review (ID prefix `C`) |
| `synthesis.md` | Unified, deduplicated findings with calibrated severity (canonical `S`-prefix IDs); appends a "Rejected Devil's Advocate Challenges" section after Phase 4 |
| `devils-advocate.md` | Codex's challenge pass against the synthesis |
| `REPORT.md` | Final findings report (the human-facing artifact, P0/P1/Deferred sprint task layout) |

`REPORT.md` is reference material. To act on the findings, run
`/sprint-plan` with the report path as the seed prompt:

```
/sprint-plan ~/Reports/<org>/<repo>/audits/<TS>-accessibility/REPORT.md
```

## Finding Schema

All intermediate audit files (`claude.md`, `codex.md`, `synthesis.md`) use
this table format:

```
| ID | Severity | Title | Location | WCAG | Level | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

`synthesis.md` adds a `Sources` column that lists the source review IDs
each unified finding merges (e.g. `A002, C003`).

**ID prefix convention:**
- Claude's review: `A001`, `A002`... (Audit)
- Codex's review: `C001`, `C002`... (Codex)
- Synthesis: `S001`, `S002`... (Synthesis canonical)

**Severity levels:** Critical, High, Medium, Low

**WCAG column**: Success criterion number (e.g., `1.4.3`) or
`Best Practice` for items beyond WCAG scope. WCAG 2.1/2.2 is the
normative reference.

**Level column**: `A`, `AA`, `AAA`, or `BP` (Best Practice).

**Verification column**: `code` (inspectable from source) or
`runtime` (requires browser and/or assistive technology testing).

**Default severity mapping** (starting point — override based on actual
exclusion severity, task blockage, AT impact, and breadth of affected
users):

| WCAG Level | Default Severity |
|---|---|
| A | Critical |
| AA | High |
| AAA | Medium |
| Best Practice | Low |

## Categories Reviewed

The subagent reviews ten WCAG-anchored categories:

1. Semantic structure and heading hierarchy
2. Images and non-text content (WCAG 1.1.1)
3. Color and contrast (WCAG 1.4.3, 1.4.11)
4. Keyboard navigation and tab order (WCAG 2.1.1, 2.1.2)
5. Focus management and focus visibility (WCAG 2.4.3, 2.4.7, 2.4.11, 2.4.12)
6. ARIA usage — roles, states, properties
7. Form labels and error messages (WCAG 1.3.1, 3.3.1, 3.3.2)
8. Dynamic content and live regions (WCAG 4.1.3)
9. Motion and animation — `prefers-reduced-motion` (WCAG 2.3.3)
10. Cognitive accessibility (WCAG 2.2.1, 3.3.4, 3.2.3)

## Sprint Mapping

`REPORT.md` maps findings to sprint priorities:

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

## Inherent Limitations

These artifacts reflect static code review against WCAG 2.1/2.2.
They are a structured starting point, not a conformance certification.
Findings marked `runtime` in the Verification column require browser
and assistive technology testing to confirm — screen reader output,
focus management behavior, and live-region announcements cannot be
validated from source alone.

## References

- WCAG 2.1: https://www.w3.org/TR/WCAG21/
- WCAG 2.2: https://www.w3.org/TR/WCAG22/
- Subagent definition: [`../../subagents/audit-accessibility-web.md`](../../subagents/audit-accessibility-web.md)
