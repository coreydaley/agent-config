# Sprint 005 Merge Notes

## Claude Draft Strengths
- Execution-ready specification level: the draft specifies the actual
  5-phase workflow, artifact paths, finding schema, Codex exec prompts,
  and output contract for both commands.
- Explicit WCAG severity mapping (Level A → Critical, AA → High, etc.)
- No-UI warn-and-stop behavior (confirmed in interview)
- Inherent-limitations disclaimer for static accessibility review
- Phase 5 per-task format (finding ID, WCAG criterion, location, issue,
  remediation, verification)
- Directory-specific README files (P1-B) matching `audit-security` pattern
- Rollback and observability sections

## Claude Draft Weaknesses (from Codex critique)
- **Schema divergence not made explicit**: adding `Heuristic`, `WCAG`,
  `Level` columns conflicts with the "same schema as audit-security"
  success criterion if not declared as an intentional extension decision
- **Overstated static accessibility coverage**: listing screen reader
  support, live region announcements, focus restoration as review
  categories without distinguishing code-inspectable from
  runtime-verified findings
- **Design rubric no precedence order**: Nielsen, Material Design, Apple
  HIG, project design system all listed as co-equal references without
  a priority order
- **Multi-path scope handling underspecified**: scope described as
  a single resolved path; multiple-path audits not clearly traced

## Codex Draft Strengths
- **P0-C explicit consistency task**: naming the family-level concerns
  once rather than repeating them per command
- **Better severity anchors**:
  - Design: "user impact, breadth, task interruption, consistency cost"
  - Accessibility: "exclusion severity, task blockage, assistive-tech
    impact, breadth of affected users"
- **README detail**: invocation examples across Claude, Codex, and
  Gemini — matches the multi-agent nature of this repo
- **Appropriate abstraction level** for a sprint plan

## Codex Draft Weaknesses (from Claude critique)
- No finding schema definition for domain-specific columns
- No-UI behavior left ambiguous
- Missing inherent-limitations disclaimer
- Missing WCAG severity mapping
- Missing directory READMEs (P1-B)
- Missing rollback/observability section
- Too high-level for command file implementation (leaves too many
  unstated choices for executing agent)

## Valid Critiques Accepted

1. **Schema extension must be explicit** — The `Heuristic`, `WCAG`,
   `Level` columns ARE justified (they anchor findings to standards).
   But the sprint doc should declare this explicitly: "the `audit-*`
   family uses the `audit-security` core schema as a base; domain
   commands may add extension columns for standards references."
   → Added to Overview and Key Decisions sections.

2. **Static vs. runtime distinction** — For `audit-accessibility`,
   findings will be categorized by verification mode: "code-inspectable"
   vs "requires browser/AT testing." Sprint tasks will include a
   verification mode field.
   → Incorporated into P0-B task spec.

3. **Design rubric priority order** — Will add explicit priority:
   (1) project design system, (2) cross-pattern consistency,
   (3) Nielsen heuristics, (4) platform guidelines as tiebreaker.
   → Incorporated into P0-A task spec.

4. **Codex's severity anchors** — Adopt for both commands (they are
   better than "user impact and frequency").

5. **README multi-agent invocation detail** — Include specific invocation
   examples for Claude, Codex, and Gemini in P1-A.

6. **Multi-path scope** — Both commands' Phase 1 will explicitly handle
   multiple space-separated path arguments.

## Critiques Rejected (with reasoning)

1. **Keep one schema with no extensions** — Rejected. WCAG criterion
   and conformance level are not optional metadata; they are the primary
   standard the command is auditing against. A finding row without
   `WCAG` and `Level` is not actionable for accessibility remediation.
   Same for `Heuristic` in design: it prevents findings from being pure
   reviewer opinion. The extension must be declared, not dropped.

2. **Drop directory READMEs (P1-B) as over-engineering** — Partially
   rejected. They are small (naming convention + schema, ~30 lines each)
   and consistent with `docs/security/README.md` from SPRINT-004. Keep
   as P1-B.

3. **Remove standards categories from command because they're "embedded
   standards documentation"** — Rejected. The command files are the
   execution spec. Without explicit category lists, executing agents
   will make inconsistent coverage choices. The detail stays.

## Interview Refinements Applied
- No-UI behavior: warn and stop (Phase 1 detects no frontend files,
  notifies user, stops without producing a sprint)

## Final Decisions

1. Both commands follow `audit-security`'s 5-phase structure exactly
2. Finding schema is the `audit-security` base + explicit domain extensions
   (declared as a family design decision, not a quiet divergence)
3. `audit-design` adds `Heuristic` column; priority: (1) project design
   system, (2) cross-pattern consistency, (3) Nielsen heuristics
4. `audit-accessibility` adds `WCAG` and `Level` columns; severity maps
   to WCAG conformance level; findings categorized by verification mode
5. Artifact directories: `docs/design/` and `docs/accessibility/`
6. No-UI: warn and stop
7. P0-C consistency task retained (Codex's contribution)
8. README P1-A includes multi-agent invocation examples (Claude/Codex/Gemini)
9. Directory READMEs kept as P1-B

## Simplest Viable Filter Applied

- Removed embedded Codex exec prompt text from the sprint plan body
  (the full prompt text belongs in the command files, not the sprint plan)
- Collapsed per-command DoD into a single family-level DoD
- Removed phase-by-phase workflow details from sprint plan
  (kept at task-spec level: what each command must do, not full text)
- Kept P0-C as explicit consistency checkpoint

## Sprint Sizing Gate

Single sprint scope: two new command files + optional README and
directory READMEs. All P0 work is text authoring of two command files.
No external dependencies. This is appropriately sized for a single sprint.
Gate passed.
