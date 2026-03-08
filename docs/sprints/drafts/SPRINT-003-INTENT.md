# Sprint 003 Intent: sprint.md + ledger Skill Integration

## Seed

> review @commands/sprint.md and see if it can be improved, you can also pull in @skills/ledger if that makes sense for this sprint since they work together

## Context

`commands/sprint.md` orchestrates the AI-led sprint execution workflow: find the next planned sprint, mark it in progress, complete all Definition of Done items, then mark it complete. It references the `/ledger` skill for all three state transitions (`stats`, `start NNN`, `complete NNN`).

**Primary defect**: `skills/ledger/SKILL.md` has `disable-model-invocation: true`, which prevents Claude from invoking it via the Skill tool. When the `/sprint` command runs, any call to `/ledger` via the Skill tool fails with "Skill ledger cannot be used with Skill tool due to disable-model-invocation". This means the sprint command's core ledger references are broken for model-driven execution.

**Secondary issues** identified on read-through:
- No handling for the case when no planned sprints exist in the ledger
- No handling for the case when a sprint is already in_progress
- Step 3 ("Run the project's build and test commands") is vague — no reference to where those commands are defined
- No guidance on what to do when the ledger has no entry yet for the sprint being planned (e.g., a brand-new repo)

## Recent Sprint Context

| Sprint | Title | Theme |
|--------|-------|-------|
| SPRINT-001 | Agent-Config Repository Revamp | Foundation: capability-routed architecture, 4-agent symlink system |
| SPRINT-002 | superplan.md Command Improvements | Bug fixes to the planning workflow; created docs/sprints/README.md |

SPRINT-002's pattern: make the smallest correct edits; fix observed defects; don't redesign. This sprint should follow the same pattern.

## Relevant Codebase Areas

| File | Role |
|------|------|
| `commands/sprint.md` | Primary command being reviewed/improved |
| `skills/ledger/SKILL.md` | Ledger skill definition — `disable-model-invocation: true` is the key flag |
| `skills/ledger/scripts/ledger.py` | Underlying Python CLI; correct and fully functional |
| `docs/sprints/README.md` | Reference doc; correctly cited in sprint.md |
| `docs/sprints/ledger.tsv` | The actual TSV data file |

## Constraints

- Must follow project conventions in CLAUDE.md (smallest correct edit; no over-engineering)
- Gemini TOML compatibility must be preserved (frontmatter + Markdown body structure in sprint.md unchanged)
- `megaplan.md` is out of scope (same as SPRINT-002)
- The ledger.py script itself is correct and should not be modified

## Success Criteria

1. Claude can successfully run a full `/sprint` cycle (find → start → complete) without hitting the `disable-model-invocation` error
2. Sprint.md handles the empty-ledger and no-planned-sprints edge cases gracefully
3. Sprint.md provides concrete guidance on finding build/test commands
4. The ledger skill integration is explicit and correct in both the command and skill definition

## Verification Strategy

- Reference implementation: ledger.py CLI already works correctly; sprint.md just needs to call it properly
- Correctness: grep checks confirm no broken references remain
- Edge cases: empty ledger (no entries), no planned sprints, sprint already in_progress
- Testing: manual read-through of sprint.md phase-by-phase after all edits

## Uncertainty Assessment

- Correctness uncertainty: **Low** — the defect is clear (disable-model-invocation blocks Skill tool usage)
- Scope uncertainty: **Medium** — the fix could be: (A) remove `disable-model-invocation`, (B) replace skill references with direct Bash calls, or (C) hybrid
- Architecture uncertainty: **Low** — no new systems; text edits only

## Open Questions

1. Should ledger's `disable-model-invocation: true` be removed (enabling Skill tool invocation from sprint.md), or should sprint.md call ledger.py directly via Bash?
2. What's the right behavior when no planned sprints exist: error, suggest running `/superplan`, or just inform and stop?
3. Should sprint.md reference `make` targets for build/test, or keep it generic and reference CLAUDE.md?
