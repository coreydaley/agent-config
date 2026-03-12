# Sprint 005 Intent: `audit-design` and `audit-accessibility` Commands

## Seed

> now that we have an audit-security command, let's also create an
> audit-design which audits the UI/UX to ensure we are adhering to
> best practices, and an audit-accessibility that audits any
> accessibility components like ensure that those with visual
> disabilities can use the application/website/whatever easily and
> thoroughly

## Context

SPRINT-004 created `commands/audit-security.md` — the first command in
the `audit-*` family — and explicitly deferred additional `audit-*`
commands. This sprint delivers the next two in that family:

- **`audit-design`**: reviews UI/UX against established design best
  practices (layout, typography, color, consistency, component patterns,
  design system adherence, information hierarchy)
- **`audit-accessibility`**: reviews a project against WCAG 2.1/2.2
  guidelines and broader accessibility best practices (semantic HTML,
  ARIA roles, keyboard navigation, focus management, color contrast,
  screen reader support, motion/animation sensitivity, cognitive load)

Both commands follow the same 5-phase dual-agent pattern as
`audit-security`: Orient → Independent Reviews (parallel Claude+Codex)
→ Synthesis → Devil's Advocate → Sprint Output. The output in each
case is a standard `SPRINT-NNN.md` document consumable by
`/sprint-work`.

## Recent Sprint Context

- **SPRINT-002**: Fixed `superplan.md` defects; created
  `docs/sprints/README.md`. Established sprint template conventions.
- **SPRINT-003**: Fixed ledger model-invocation blocker; hardened
  `sprint.md` edge-case handling. `/ledger` skill is reliable.
- **SPRINT-004**: Created `commands/audit-security.md` — 5-phase
  dual-agent workflow, finding schema table, `docs/security/`
  intermediate artifacts, sprint output. Deferred additional
  `audit-*` commands explicitly. This sprint is the direct follow-on.

## Relevant Codebase Areas

- `commands/audit-security.md` — **primary template** for both new commands
- `commands/sprint-plan.md` — peer reference for large command structure
- `docs/sprints/README.md` — sprint template conventions
- `skills/ledger/` — `/ledger add NNN` call syntax
- `README.md` — will need updates for discoverability (P1)

## Constraints

- Must follow project conventions in CLAUDE.md
- Frontmatter: single-line `description:` value (Gemini TOML compatible)
- No `--model` or `--full-auto` flags in any `codex exec` call
- No `$ARGUMENTS` raw interpolation into shell strings (validated in Phase 1)
- Output must be a sprint document consumable by `/sprint-work`
- Intermediate artifacts: `docs/security/` for audit-security used
  a shared directory; audit-design and audit-accessibility should use
  purpose-specific subdirectories (approach decision below)
- Keep each command file self-contained and readable top-to-bottom

## Success Criteria

1. `commands/audit-design.md` exists with valid frontmatter and a
   complete 5-phase workflow that is structurally parallel to
   `audit-security.md`
2. `commands/audit-accessibility.md` exists with valid frontmatter and
   a complete 5-phase workflow, with WCAG 2.1/2.2 as the normative
   reference
3. Both commands produce a standard sprint document as output
4. Both commands share the same finding schema as `audit-security`
5. Neither command shares audit artifact directories with `audit-security`

## Verification Strategy

- **Reference implementation**: `commands/audit-security.md` is the
  canonical pattern. Each new command should pass a structural diff
  check: same phases, same output contract, same finding schema.
- **Spec/documentation**: WCAG 2.1 (https://www.w3.org/TR/WCAG21/) and
  WCAG 2.2 for `audit-accessibility`; Material Design, Apple HIG,
  Nielsen-Norman heuristics for `audit-design`.
- **Edge cases**: no-UI project (audit-design scope contains no
  frontend files), no-findings result, path-scoped audit, multi-path
  audit
- **Testing approach**: manual read-through of each command
  phase-by-phase; spot-check that Phase 5 sprint format conforms to
  `docs/sprints/README.md`

## Uncertainty Assessment

- **Correctness uncertainty**: Low — `audit-security` is a clear
  template; the main creative work is customizing finding categories
  and WCAG/design heuristics
- **Scope uncertainty**: Low — seed is specific: two commands, each
  following `audit-security` pattern
- **Architecture uncertainty**: Low/Medium — the main decision is
  intermediate artifact directory layout (shared `docs/security/` vs.
  separate dirs per command type)

## Approaches Considered

| Approach | Pros | Cons | Verdict |
|---|---|---|---|
| **A: Shared `docs/security/` for all audit artifacts** | Consistent with existing `audit-security`; one place for all audit output | Design and accessibility artifacts mixed with security findings; harder to scan; `docs/security/` name is semantically wrong for design/UX content | Rejected — naming confusion and mixing of concerns |
| **B: Separate per-command directories (`docs/design/`, `docs/accessibility/`)** | Each command owns its artifact space; naming is semantically accurate; easier to `.gitignore` selectively | Three separate directories; slight inconsistency with `audit-security` (which uses `docs/security/`) | **Selected** — semantic clarity wins; mirrors `audit-security`'s approach of a purpose-specific directory |
| **C: Single `docs/audits/NNN-TYPE-*.md` flat structure** | All audit artifacts in one place; easy to correlate across audit types | Sprint NNN numbering for different audit types would collide or require prefixing; complex to navigate | Rejected — NNN collision risk and directory-level type mixing |

## Open Questions

1. Should `audit-design` and `audit-accessibility` share the WCAG
   overlap (e.g. color contrast appears in both)? → Proposed: each
   command covers its primary domain fully; overlap is acceptable since
   commands are run independently and findings become separate sprints.
2. Should the finding schema for design/accessibility add a "WCAG
   Criterion" or "Heuristic" column? → Proposed: yes for
   `audit-accessibility` (WCAG criterion ID is essential), optional
   metadata column for `audit-design` (maps to heuristic).
3. Should `README.md` be updated in P0 or P1? → Proposed: P1, same
   as `audit-security` did.
