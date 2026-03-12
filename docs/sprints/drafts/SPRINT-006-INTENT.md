# Sprint 006 Intent: `audit-architecture` Command

## Seed

> now that we have the audit-security command, let's create an audit-architecture command
> that takes a deep investigatory look at the architecture choices that we made for our
> project and tries to come up with any better alternatives

## Context

- SPRINT-004 shipped `audit-security` — the foundational `audit-*` family command.
  Five-phase workflow (Orient → Independent Reviews → Synthesis → Devil's Advocate →
  Sprint Output) is proven and working.
- SPRINT-005 (planned, not started) extends the family with `audit-design` and
  `audit-accessibility`.
- No in-progress sprint; SPRINT-006 can begin planning immediately.
- The `audit-*` family convention is clear: each command mirrors the 5-phase structure,
  extends the base finding schema with domain-specific columns, produces a
  `/sprint-work`-consumable sprint document.
- The repo is an agent-config system; architecture means both general software
  architecture (for arbitrary projects) and agent-config architecture specifically
  (commands/skills/agents structure, invocation patterns, data flow through agent prompts).

## Recent Sprint Context

- **SPRINT-002**: Established `docs/sprints/README.md` and the standard sprint template.
- **SPRINT-003**: Fixed `skills/ledger/SKILL.md` disable-model-invocation defect;
  hardened sprint.md edge-case handling.
- **SPRINT-004**: Created `commands/audit-security.md` — the dual-agent audit template
  that SPRINT-006 will extend. Established `docs/security/` artifact directory pattern.
- **SPRINT-005** (planned): Creates `audit-design` and `audit-accessibility` following
  the same template; also declares the schema extension convention (core columns + domain
  extension columns).

## Relevant Codebase Areas

- `commands/audit-security.md` — the primary template to mirror
- `commands/sprint-plan.md` — reference for the 8-phase planning workflow (longer, more
  complex; shows what a well-structured command file looks like)
- `docs/sprints/README.md` — standard sprint template
- `docs/sprints/SPRINT-004.md` — design decisions for the audit-security command
  (especially Finding Schema, Phase 2 parallel structure, devil's advocate)
- `docs/sprints/SPRINT-005.md` — schema extension pattern declaration
- No existing `commands/audit-architecture.md` — this is a new file

## Constraints

- Must follow project conventions in `CLAUDE.md`
- Must integrate with the established `audit-*` family (5-phase workflow, finding schema
  base, `/sprint-work` output contract)
- No `--model` or `--full-auto` flags in any `codex exec` call
- `$ARGUMENTS` must be validated as a path before use in any shell string
- Codex exec prompts must be self-contained (no shell variables — use resolved literals)
- Single-line `description:` frontmatter (Gemini TOML compatible)

## Success Criteria

- `commands/audit-architecture.md` exists and follows the 5-phase `audit-*` pattern
- Running `/audit-architecture` (or scoped to a path) produces:
  - Intermediate artifact files in `docs/architecture/`
  - A final `docs/sprints/SPRINT-NNN.md` with architecture findings as tasks
  - Ledger entry for the sprint
- The command is useful for both:
  1. General software architecture review (any repo)
  2. Agent-config architecture specifically (commands/skills/agents structure)
- Finding schema meaningfully captures: architectural decision, pattern/principle violated
  or tension, alternative approach, and estimated migration impact

## Verification Strategy

- Reference implementation: `commands/audit-security.md` — the output contract is
  verified by confirming structural parity
- Spec/documentation: `docs/sprints/README.md` for sprint format;
  `docs/sprints/SPRINT-005.md` for schema extension pattern
- Edge cases identified:
  - No recognizable architecture patterns in scope (warn and continue, unlike no-UI
    stop in design/accessibility)
  - Single-reviewer scenario (one agent review missing/empty)
  - Findings that are opinions vs. findings that cite specific principles or patterns
  - Repos with no conventional structure (scripts-only, flat directories)
- Testing approach: Manual read-through — each phase produces what the next phase
  consumes; compare sprint output format against `docs/sprints/README.md` template

## Uncertainty Assessment

- **Correctness uncertainty: Medium** — "architecture" is inherently more subjective than
  security or WCAG compliance. The finding schema must carefully anchor findings to named
  principles or observable tradeoffs, not personal preference.
- **Scope uncertainty: Low** — the command structure is clear from the template; the main
  open question is the right finding schema columns.
- **Architecture uncertainty: Low** — follows the established audit-* family pattern.

## Approaches Considered

| Approach | Pros | Cons | Verdict |
|---|---|---|---|
| **A: Mirror audit-security exactly** — same 5 phases, same base schema extended with `Pattern` and `Alternative` columns, artifact dir `docs/architecture/` | Maximally consistent with family; easiest to maintain alongside audit-security/design/accessibility; proven workflow | Architecture findings may blend opinions with facts — schema must enforce evidence anchoring | **Selected** — the schema discipline (requiring named principles and concrete alternatives) is the right mitigation; family consistency outweighs a bespoke workflow |
| **B: Architecture-specific multi-phase workflow** — Orient + Discovery + Trade-off Analysis + Alternatives + Sprint Output | Better tailored to architecture discovery; allows ranking decisions by effort vs. impact | Breaks family consistency; harder to maintain; no clear advantage over Approach A with good schema design | Rejected — over-engineers the problem |
| **C: Produce an architecture decision record (ADR) instead of a sprint** — output ADRs documenting decisions and alternatives | Better documentation artifact; standard format | Does not integrate with `/sprint-work`; breaks the audit-* output contract; ADRs are static docs not actionable tasks | Rejected — the sprint output contract is the key value of the audit-* family |

## Open Questions

1. Should `audit-architecture` stop (like `audit-design`/`audit-accessibility`) if no
   recognizable architecture patterns are found, or warn-and-continue? Architecture is
   always present in any codebase — even "no structure" is an architectural decision.
   Proposal: warn-and-continue (not stop).

2. What columns should the finding schema include beyond the base? Candidates:
   `Pattern/Principle` (what architectural rule or principle is in tension),
   `Alternative` (the proposed better approach), `Migration Cost` (Low/Medium/High
   estimate of effort to change).

3. Should the command have a mode or flag for agent-config repos specifically? Or should
   agent-config awareness be baked into the Phase 2 Codex prompt the way
   `audit-security` handles it?
   Proposal: bake it in — the Codex prompt should explicitly cover `commands/*.md`,
   `skills/`, `agents/` when those directories exist.
