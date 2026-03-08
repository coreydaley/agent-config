# Sprint 003: sprint.md + ledger Skill Integration Fix

## Overview

`commands/sprint.md` is the AI-executed command that drives sprint completion: find the next planned sprint, mark it in progress, complete all Definition of Done items, then mark it done. It relies on the `/ledger` skill for every state transition.

The problem: `skills/ledger/SKILL.md` has `disable-model-invocation: true`, which silently breaks the entire workflow when Claude tries to invoke the ledger skill via the Skill tool. This defect has been present since the sprint command was authored.

This sprint fixes the integration by removing `disable-model-invocation: true` from the ledger skill (allowing the sprint command to call it as intended), tightens up the sprint command's edge-case handling, and adds concrete build/validation guidance.

## Use Cases

1. **Normal sprint run**: User invokes `/sprint`; Claude finds the next planned sprint, marks it in progress, works through all DoD items, marks it complete — ledger updates succeed.
2. **No planned sprints**: User invokes `/sprint` with an empty ledger or all sprints completed; Claude informs the user rather than failing silently.
3. **Sprint already in progress**: User invokes `/sprint` but a sprint is already in_progress; Claude surfaces this state rather than adding confusion.
4. **Explicit sprint number**: User invokes `/sprint 005`; Claude runs that specific sprint, even if it's not in `planned` status.
5. **Build/test validation**: Claude knows where to look for build commands (Makefile, CLAUDE.md) without ambiguity.

## Architecture

```
User invokes /sprint [NNN]
        │
        ▼
   sprint.md command
        │
        ├─► /ledger stats         (via Skill tool — now works after fix)
        │         │
        │         └─► identify lowest-numbered planned sprint
        │
        ├─► /ledger start NNN     (via Skill tool — marks in_progress)
        │
        ├─► Read SPRINT-NNN.md
        │         │
        │         └─► Work through all DoD items
        │                   │
        │                   └─► Run build/test validation
        │
        └─► /ledger complete NNN  (via Skill tool — marks completed)
```

## Implementation Plan

### Phase 1: Fix ledger skill model invocation (~30%)

**Files:**
- `skills/ledger/SKILL.md` — remove `disable-model-invocation: true`

**Tasks:**
- [ ] Remove `disable-model-invocation: true` from ledger SKILL.md frontmatter
- [ ] Verify the remaining frontmatter is valid YAML (`name`, `description`, `argument-hint`, `allowed-tools`)
- [ ] Confirm `allowed-tools: Bash(python3 *)` still restricts execution correctly

**Rationale**: The `disable-model-invocation` flag was preventing Claude from using the Skill tool to invoke the ledger. Since the `/sprint` command is an explicitly user-initiated action, it's safe for Claude to manage ledger state during execution. The `allowed-tools` restriction (Bash with python3 only) provides the appropriate execution guardrail.

### Phase 2: Fix and improve sprint.md (~60%)

**Files:**
- `commands/sprint.md`

**Tasks:**
- [ ] **Ledger invocation audit**: grep all `/ledger` references; confirm they use Skill-tool-compatible syntax (they already do — just broken due to Phase 1 issue)
- [ ] **No-planned-sprints handling**: after the "find the next sprint" step, add explicit guidance: if no planned sprints exist, inform the user (suggest running `/superplan` to create one) and stop
- [ ] **In-progress guard**: add a check — if a sprint is already `in_progress`, surface it to the user and ask whether to continue with it or abort
- [ ] **Build/test guidance**: replace "Run the project's build and test commands to validate" with concrete guidance: check for `Makefile` (run `make all` or `make test`), check `CLAUDE.md` for project-specific test commands, fall back to listing validation steps from the sprint document's Definition of Done
- [ ] **Explicit sprint number handling**: clarify the `$ARGUMENTS` path — if a sprint number is provided, use `/ledger status NNN` to verify it exists before starting, not just jump in
- [ ] **TaskCreate/TaskUpdate note**: move the note to be more prominent (currently buried at the bottom)

### Phase 3: Acceptance verification (~10%)

**Tasks:**
- [ ] `grep -n "disable-model-invocation" skills/ledger/SKILL.md` returns no results
- [ ] Manual read-through of sprint.md confirming all steps connect logically
- [ ] Verify all ledger invocations in sprint.md use `/ledger <subcommand>` syntax
- [ ] Verify no-planned-sprints case is handled in the command text

## Files Summary

| File | Action | Purpose |
|------|--------|---------|
| `skills/ledger/SKILL.md` | Modify | Remove `disable-model-invocation: true` |
| `commands/sprint.md` | Modify | Edge cases, build guidance, in-progress guard |

## Definition of Done

- [ ] `grep -n "disable-model-invocation" skills/ledger/SKILL.md` returns no results
- [ ] `/sprint` can call `/ledger stats`, `/ledger start NNN`, `/ledger complete NNN` via Skill tool without error
- [ ] sprint.md handles no-planned-sprints case explicitly (inform user, suggest `/superplan`)
- [ ] sprint.md handles already-in-progress case explicitly
- [ ] sprint.md provides concrete build/test guidance (Makefile → `make all`, CLAUDE.md fallback)
- [ ] Explicit sprint number (`$ARGUMENTS = NNN`) path has a verification step before execution
- [ ] Gemini TOML frontmatter structure is unchanged (description field preserved)
- [ ] Manual read-through confirms each step connects logically to the next
- [ ] No out-of-scope structural changes made

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Removing disable-model-invocation allows unintended autonomous ledger updates | Low | Medium | `/sprint` is always user-initiated; `allowed-tools: Bash(python3 *)` still constrains execution |
| Sprint.md edge-case additions bloat the command | Medium | Low | Keep additions minimal; 1-2 lines per edge case, not full sub-workflows |
| Gemini TOML conversion breaks on sprint.md edits | Low | Low | Frontmatter unchanged; body is plain text |
| In-progress guard creates confusion for the common case | Low | Low | Make it a soft check (inform, don't block hard) |

## Security Considerations

- Removing `disable-model-invocation` from ledger: Claude can now update ledger state when running `/sprint`. This is an explicit user-initiated action; the risk of unauthorized modification is low. The `allowed-tools: Bash(python3 *)` restriction remains as a guardrail.
- sprint.md edits are text-only; no new execution surfaces introduced
- ledger.py is unchanged; no injection surface changes

## Dependencies

- SPRINT-001 (completed) — established the repo architecture
- SPRINT-002 (completed) — established sprint conventions and docs/sprints/README.md

## Open Questions

- Should `disable-model-invocation` be removed entirely, or replaced with a narrower restriction? Current proposal: remove it, relying on `allowed-tools` and user-initiated context as the guardrail.
- Should the in-progress guard be a hard stop (error) or a soft prompt (ask user to confirm)?
