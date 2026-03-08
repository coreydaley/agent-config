# Sprint 002 Intent: superplan.md Improvements

## Seed

Review the superplan.md command and see if there are any improvements that can be made.

## Context

`superplan.md` is a command that orchestrates an 8-phase collaborative sprint planning workflow using Claude + Codex. It is an extended version of `megaplan.md` (6 phases) that adds a Devil's Advocate phase (Phase 7) and a Security Review phase (Phase 8). The file lives at `commands/superplan.md` and is symlinked into `~/.claude/commands/` and `~/.codex/prompts/`.

## Recent Sprint Context

- **SPRINT-001** (completed 2026-03-07): Revamped repo architecture from uniform-loop to capability-routed model. Established the generate+symlink pipeline, Gemini TOML conversion, and capability matrix. This sprint established the project conventions that all subsequent work builds on.

## Relevant Codebase Areas

- `commands/superplan.md` — primary file under review
- `commands/megaplan.md` — 6-phase predecessor; canonical reference for shared phases
- `commands/sprint.md` — shows preferred ledger usage patterns (`/ledger` skill, not direct python)
- `docs/sprints/README.md` — sprint template conventions
- `skills/ledger/SKILL.md` — ledger skill definition

## Constraints

- Must follow project conventions in CLAUDE.md
- Do not over-engineer; fix only what is clearly wrong or clearly improvable
- Prefer editing existing files over creating new ones
- Changes to `superplan.md` must not break its use as a Gemini TOML command

## Success Criteria

The superplan.md command is internally consistent, references the correct tools/patterns, has no copy-paste artifacts from megaplan.md, and provides clearer guidance in the phases where it currently under-specifies.

## Verification Strategy

- Reference implementation: `megaplan.md` (for shared phases 1-6)
- Spec/documentation: `commands/sprint.md` (for correct ledger invocation pattern)
- Edge cases: graceful behavior when no sprints exist yet; correct file structure comment
- Testing approach: manual review of each phase against the reference files

## Uncertainty Assessment

- Correctness uncertainty: Low — issues are observable by direct inspection
- Scope uncertainty: Low — bounded to one file with well-defined improvement categories
- Architecture uncertainty: Low — no architectural changes, text edits only

## Open Questions

1. Should Phase 5 codex command include `--model` and `--full-auto` flags (as megaplan does) or keep the simpler `codex exec`?
2. Should megaplan.md be updated in sync, or only superplan.md?
