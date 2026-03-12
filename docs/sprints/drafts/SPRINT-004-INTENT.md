# Sprint 004 Intent: Dual-Agent Security Audit Command

## Seed

> I want to create a dual-security-review command that works along
> similar lines as the @commands/sprint-plan where claude and codex
> both perform independent security reviews, and then a synthesized
> review is drafted, and then there is a devil's advocate pass by
> codex on the final draft and then the final security review is
> produced, this should have actionable items that can be addressed
> by an AI agent in another dual-security-address command that
> should also be created. Since the security-review command is
> already taken within Claude, if you can come up with two better
> command names than dual-security-review and dual-security-address
> give me those options.

## Context

The project currently has four commands in `commands/`:
- `commit.md` — structured commit workflow
- `tag.md` — release tagging workflow
- `sprint-plan.md` — multi-agent sprint planning (Claude + Codex competing drafts → synthesis → devil's advocate → final)
- `sprint-work.md` — executes a planned sprint

The seed asks for a dual-agent security review command mirroring
the `sprint-plan.md` pattern. After discussion, the design was
refined to:

1. **One command: `audit-security`** — Claude and Codex independently
   review code for security vulnerabilities, reviews are synthesized,
   Codex attacks the synthesis via devil's advocate, and a final
   report is produced — as a standard `SPRINT-NNN.md` sprint document.

2. **No separate remediation command** — the sprint output is
   executed with the existing `/sprint-work` command. Critical/High
   findings map to P0 tasks, Medium to P1, Low to Deferred.

3. **Naming convention: `audit-*`** — namespaced for future extensibility
   (`audit-deps`, `audit-performance`, etc.)

4. **Same sprint ledger and SPRINT-NNN numbering** — security remediation
   sprints are regular sprints.

The constraint: `security-review` is a reserved Claude built-in
command name. Both new commands need distinct names.

## Recent Sprint Context

- **SPRINT-001**: Established capability-routed architecture
  (generate + symlink per agent); all 4 agents wired correctly.
  Baseline for all command files being in `commands/`.
- **SPRINT-002**: Created `docs/sprints/README.md`, fixed bugs in
  `superplan.md` (now renamed `sprint-plan.md`). Established the
  sprint document template and conventions used by both new
  commands.
- **SPRINT-003**: Fixed ledger skill integration (`disable-model-
  invocation` removed), hardened `sprint.md` (now `sprint-work.md`)
  edge-case handling. Pattern: small targeted text edits, no script
  changes.

## Relevant Codebase Areas

- `commands/sprint-plan.md` — primary template/pattern for the
  new review command (8-phase workflow, Codex exec pattern, devil's
  advocate phase)
- `commands/sprint-work.md` — primary template/pattern for the
  new remediation command (takes prior output and executes it)
- `docs/sprints/README.md` — sprint document conventions that
  Codex reads in Phase 5 prompts
- `commands/` — all new files land here
- The two new commands should follow the same YAML frontmatter
  structure (`description:`) and Markdown body structure as
  existing commands

## Constraints

- Must follow project conventions in CLAUDE.md (Conventional
  Commits, no over-engineering)
- Must not use `security-review` as a command name (reserved by
  Claude)
- Must follow the same frontmatter format as existing commands
- Codex exec calls must use `codex exec "..."` with no
  `--model`/`--full-auto` flags
- Must be compatible with the Gemini TOML auto-conversion pipeline
  (single-line `description:`, no embedded triple-quoted strings
  in frontmatter)
- Review command output must be structured so the remediation
  command can parse and act on it

## Success Criteria

- `commands/audit-security.md` exists and follows command conventions
- The command orchestrates a 5-phase dual-agent workflow and
  produces a standard `SPRINT-NNN.md` sprint document where
  Critical/High findings are P0 tasks, Medium are P1, Low are Deferred
- The sprint output can be executed directly with `/sprint-work`
  without modification
- Naming establishes the `audit-*` namespace for future audit commands

## Verification Strategy

- Reference implementation: `commands/sprint-plan.md` (review
  command mirrors its structure) and `commands/sprint-work.md`
  (remediation command mirrors its structure)
- Correctness: manual read-through of each phase for logical
  flow and Codex exec prompt completeness
- Edge cases: no prior review exists (remediation command should
  halt gracefully); no findings (review command should produce
  a clean-bill report); file path scope argument provided vs. not
- Testing approach: manual read-through; validate Codex exec
  prompts are unambiguous; validate actionable items format is
  machine-parseable

## Uncertainty Assessment

- Correctness uncertainty: **Low** — well-understood domain;
  mirrors existing `sprint-plan.md` pattern closely
- Scope uncertainty: **Medium** — command name choice requires
  user input; scope of remediation command (auto-fix vs. guided)
  needs clarification; output file location (docs/security/ vs.
  inline) needs decision
- Architecture uncertainty: **Low** — extends existing patterns;
  no new infrastructure needed

## Approaches Considered

| Approach | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **A: `audit-security` — one command, sprint output** | `audit-*` namespace enables future `audit-deps`, etc.; output is a `SPRINT-NNN.md` worked by `/sprint-work` (no new execution infrastructure); single-responsibility | None significant | **Selected** — minimal new infrastructure; extensible naming; integrates with proven sprint workflow |
| **B: `security-audit` + `security-remediate` — two commands** | Explicit remediation step | Two commands to maintain; remediation logic duplicates sprint-work; `security-*` namespace doesn't extend as cleanly | Rejected — user confirmed single command + sprint-work is preferred |
| **C: `security-audit` with custom FINAL.md output** | Familiar security tooling output format | Requires a separate remediation command or manual follow-through; doesn't reuse sprint-work | Rejected — unnecessary when sprint format already covers structured task execution |

## Open Questions Resolved

| Question | Answer |
|---|---|
| Command names? | `audit-security` — single command, `audit-*` namespace for extensibility |
| One command or two? | One — output is a standard `SPRINT-NNN.md` executed by `/sprint-work` |
| Severity → sprint tier mapping? | Critical/High → P0, Medium → P1, Low → Deferred |
| Sprint ledger integration? | Same ledger and SPRINT-NNN sequence as all other sprints |
| Output file location? | `docs/security/` for intermediate drafts; final output is `docs/sprints/SPRINT-NNN.md` |
