# Sprint 003: sprint.md + ledger Skill Integration Fix

## Overview

`commands/sprint.md` is the AI-executed command that drives sprint completion: find the next planned sprint, mark it in progress, complete all Definition of Done items, then mark it done. It references the `/ledger` skill for every state transition (`stats`, `start NNN`, `complete NNN`).

The problem: `skills/ledger/SKILL.md` has `disable-model-invocation: true`, which blocks the Skill tool invocation and breaks the entire workflow. This defect has been present since the sprint command was authored.

This sprint fixes the integration by removing `disable-model-invocation: true` from the ledger skill, tightens sprint.md's edge-case handling (empty ledger, no planned sprints, existing in-progress sprint), corrects a wrong command reference (`/ledger status` is mutating, not a read command), and adds concrete build/test guidance anchored to the repo's `README.md` and `Makefile`.

All changes are text edits to two files.

## Guiding Principles

- Fix observed defects; do not redesign the workflow
- Prefer the smallest edit that correctly solves each problem
- Keep Gemini TOML conversion compatibility (frontmatter + Markdown body structure unchanged)
- `ledger.py` is correct and must not be modified
- `megaplan.md` is out of scope

## P0: Must Ship

### P0-A: Fix Ledger Model Invocation

**Goal**: Allow `commands/sprint.md` to call the `/ledger` skill via the Skill tool.

**Files:**
- `skills/ledger/SKILL.md`

**Tasks:**
- [ ] Remove `disable-model-invocation: true` from the frontmatter
- [ ] Verify the remaining frontmatter fields are valid: `name`, `description`, `argument-hint`, `allowed-tools`
- [ ] Verify `allowed-tools: Bash(python3 *)` is preserved (this is the execution guardrail)
- [ ] Add a note in the SKILL.md body clarifying that model invocation of this skill is intentional and scoped to the `/sprint` command workflow (security hygiene for future maintainers)

**Acceptance:**
- `grep -n "disable-model-invocation" skills/ledger/SKILL.md` returns no results
- The skill can be invoked from `commands/sprint.md` via the Skill tool without error

### P0-B: Harden sprint.md Flow for Real-World Ledger States

**Goal**: Handle the cases that currently cause undefined or failing behavior.

**Files:**
- `commands/sprint.md`

**Tasks:**
- [ ] **Empty ledger / no planned sprints**: After the "use `/ledger stats`" step, add: if no planned sprints exist, inform the user and suggest running `/superplan` to create one, then stop.
- [ ] **In-progress guard**: Before starting a new sprint, check if one is already `in_progress` (use `/ledger current`). If so, surface it as a soft prompt — show the user which sprint is running and ask whether to continue it or abort. Default: continue the existing in-progress sprint.
- [ ] **Explicit sprint number path**: When `$ARGUMENTS` is a sprint number (e.g. `005`), verify the sprint exists in the ledger first using `/ledger list`. If the sprint is not in the ledger, instruct the user to run `/ledger sync` (if the sprint doc exists) or `/ledger add NNN "Title"` (if adding fresh), then stop. Note: if a sprint is both provided explicitly AND one is already in_progress, the explicit argument takes precedence — but still show a note about the in-progress sprint.
- [ ] **Ledger sync guidance**: Add a note that if sprint docs and ledger entries are out of sync, `/ledger sync` will reconcile them.

**Acceptance:**
- sprint.md Step 1 documents behavior for: planned sprint found, no planned sprint, sprint already in_progress, explicit NNN not in ledger
- No reference to root-level `CLAUDE.md` (not a file in this repo)
- No use of `/ledger status` as a read/verification step (it is a mutating command)

### P0-C: Tighten Build/Test Validation Guidance

**Goal**: Replace vague "run the project's build and test commands" with concrete command-discovery instructions.

**Files:**
- `commands/sprint.md`

**Tasks:**
- [ ] Replace Step 3 validation wording with: check `README.md` for documented build/test commands; check `Makefile` for available targets (e.g. `make all`, `make test`); fall back to the sprint document's own Definition of Done for validation steps
- [ ] Ensure the wording does not hard-code specific targets (stays generic, repo-agnostic)

**Acceptance:**
- Step 3 references `README.md` and `Makefile` as the source for validation commands
- No hard-coded targets that may not exist in all repos

## Files Summary

| File | Action | Purpose |
|------|--------|---------|
| `skills/ledger/SKILL.md` | Modify | Remove `disable-model-invocation: true` (P0-A) |
| `commands/sprint.md` | Modify | Edge-case handling + build guidance (P0-B, P0-C) |

## Definition of Done

- [ ] `grep -n "disable-model-invocation" skills/ledger/SKILL.md` returns no results
- [ ] `/sprint` can invoke `/ledger stats`, `/ledger start NNN`, `/ledger complete NNN` via Skill tool without error
- [ ] sprint.md Step 1 handles: planned sprint found, no planned sprint (inform + suggest `/superplan`), already in_progress (soft prompt), explicit NNN not in ledger (instruct sync/add)
- [ ] sprint.md Step 3 references `README.md` and `Makefile` for build/test commands
- [ ] No reference to root-level `CLAUDE.md` in sprint.md
- [ ] `/ledger status` is not used as a read/verification step
- [ ] `skills/ledger/scripts/ledger.py` is unchanged
- [ ] `megaplan.md` is unchanged
- [ ] Gemini TOML frontmatter structure in sprint.md is unchanged
- [ ] The soft in-progress prompt explicitly names the sprint (number + title) and requires user confirmation before continuing — auto-continue without surfacing sprint identity does not pass
- [ ] All `/ledger` calls in sprint.md are audited: no mutating commands (`start`, `complete`, `skip`, `status`, `add`) are used for read-only verification purposes
- [ ] Manual read-through of sprint.md for four scenarios: (1) normal run, (2) no planned sprint, (3) existing in-progress sprint (no argument), (4) explicit NNN not in ledger

## Execution Order

1. Confirm defect: `grep -n "disable-model-invocation" skills/ledger/SKILL.md`
2. Remove `disable-model-invocation: true` from `skills/ledger/SKILL.md` (P0-A)
3. Apply P0-B changes to `commands/sprint.md` one item at a time
4. Apply P0-C changes
5. Run all acceptance grep checks
6. Manual scenario read-through (four scenarios including explicit NNN missing from ledger)

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Enabling model invocation broadens where ledger runs autonomously | Low | Medium | `/sprint` is user-initiated; `allowed-tools: Bash(python3 *)` constrains execution |
| Edge-case text in sprint.md makes the command feel heavy | Low | Low | Keep additions to 1-2 sentences per case |
| Validation guidance drifts from actual repo commands | Low | Low | Anchor to `README.md`/`Makefile` rather than hard-coding targets |
| Gemini TOML conversion breaks | Low | Low | Frontmatter is unchanged; body is plain text |

## Security Considerations

- Removing `disable-model-invocation` from ledger: Claude can now update ledger state when running `/sprint`. This is an explicit user-initiated action; `allowed-tools: Bash(python3 *)` remains as the execution guardrail.
- sprint.md edits are text-only; no new execution surfaces introduced
- ledger.py is unchanged; no injection surface changes

## Dependencies

- SPRINT-001 (completed) — established repo architecture and conventions
- SPRINT-002 (completed) — created `docs/sprints/README.md`, fixed superplan.md

## Open Questions Resolved

| Question | Answer |
|----------|--------|
| Remove `disable-model-invocation` or use Bash calls? | Remove it — `/sprint` is user-initiated; `allowed-tools` provides the guardrail |
| No planned sprints behavior? | Inform user + suggest `/superplan`; stop |
| In-progress sprint behavior? | Soft prompt: surface it, ask to confirm continuing; default is to continue |
| Explicit NNN not in ledger? | Instruct user to run `/ledger sync` or `/ledger add`, then stop |
