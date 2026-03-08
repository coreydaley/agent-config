# Sprint 003 Codex Draft: sprint.md + Ledger Skill Integration Hardening

## Sprint Objective
Make `commands/sprint.md` reliably executable by fixing ledger integration and hardening execution flow for real-world states (empty ledger, no planned sprints, existing in-progress sprint), while keeping scope limited to text/config updates.

## Problem Statement
`commands/sprint.md` currently depends on `/ledger` skill calls, but `skills/ledger/SKILL.md` sets `disable-model-invocation: true`, which blocks model invocation and breaks the command's core flow.

Additional correctness gaps increase operator ambiguity:
- no explicit behavior when `docs/sprints/ledger.tsv` is empty or has no planned rows
- no policy for existing `in_progress` sprint state when `/sprint` is invoked without an argument
- vague build/test guidance in Step 3 with no concrete command discovery path
- unclear bootstrap path when a sprint doc exists but ledger is missing a matching entry

## Guiding Principles
- Fix the concrete defect first: model-callable ledger integration.
- Preserve existing `/sprint` workflow shape (find/start/complete).
- Prefer minimal edits to `commands/sprint.md` and `skills/ledger/SKILL.md`.
- Keep `ledger.py` unchanged; it is already the working reference implementation.
- Maintain Markdown/frontmatter compatibility for downstream command conversion.

## Scope

### In Scope
1. Resolve skill-invocation incompatibility between `/sprint` and `/ledger`.
2. Add explicit `/sprint` behavior for empty ledger and no-planned-sprints cases.
3. Add explicit handling for existing `in_progress` sprint state.
4. Tighten Step 3 build/test guidance using concrete repository references.
5. Clarify ledger bootstrap/sync behavior when sprint docs and ledger entries diverge.

### Out of Scope
1. Rewriting `skills/ledger/scripts/ledger.py` behavior.
2. Introducing new sprint orchestration commands.
3. Broad redesign of sprint lifecycle states beyond current ledger statuses.

## Key Decisions
1. **Ledger invocation model**: remove `disable-model-invocation: true` from `skills/ledger/SKILL.md` so `/sprint` can use `/ledger ...` directly as written.
2. **No planned sprint behavior**: `/sprint` should stop with a clear message and point users to planning flow (`/superplan` and/or adding planned entries).
3. **Existing in-progress behavior**: when no explicit sprint argument is provided and one sprint is already `in_progress`, continue that sprint instead of starting a different sprint.
4. **Build/test command discovery**: instruct agents to read `README.md` and `Makefile` for canonical validation targets before execution.

## Implementation Plan

### Phase 1: Baseline and Defect Confirmation
**Files:**
- `commands/sprint.md`
- `skills/ledger/SKILL.md`
- `docs/sprints/ledger.tsv`

**Tasks:**
- [ ] Confirm `/sprint` currently depends on `/ledger` skill calls in all state transitions.
- [ ] Confirm `disable-model-invocation: true` is the direct blocker in `skills/ledger/SKILL.md`.
- [ ] Confirm current ledger states and data-shape assumptions in `docs/sprints/ledger.tsv`.

### Phase 2: Ledger Integration Fix
**Files:**
- `skills/ledger/SKILL.md`

**Tasks:**
- [ ] Remove the model-invocation block so the skill is callable from command flows.
- [ ] Preserve existing `allowed-tools` and script invocation contract.
- [ ] Verify no other metadata conflicts with `/sprint` usage.

### Phase 3: sprint.md Flow Hardening
**Files:**
- `commands/sprint.md`

**Tasks:**
- [ ] Add explicit branching for empty ledger and no planned sprints.
- [ ] Add explicit branching for already `in_progress` sprint.
- [ ] Add guidance for explicit sprint argument when requested sprint is absent from ledger.
- [ ] Clarify when to run `/ledger sync` vs `/ledger add` before state transitions.

### Phase 4: Validation Guidance Tightening
**Files:**
- `commands/sprint.md`
- `README.md`
- `Makefile`

**Tasks:**
- [ ] Replace vague Step 3 wording with concrete command-discovery instructions.
- [ ] Align validation wording with repo-supported targets and conventions.
- [ ] Ensure failure-handling instructions are actionable and deterministic.

### Phase 5: Consistency and Read-Through Verification
**Files:**
- `commands/sprint.md`
- `skills/ledger/SKILL.md`

**Tasks:**
- [ ] Run a full dry read-through of `/sprint` for three paths: normal run, no planned sprint, existing in-progress sprint.
- [ ] Verify all referenced files exist and all ledger calls are consistent.
- [ ] Confirm no `ledger.py` changes were introduced.

## Files Summary

| File | Action | Purpose |
|---|---|---|
| `commands/sprint.md` | Modify | Harden flow control and validation guidance for realistic ledger states |
| `skills/ledger/SKILL.md` | Modify | Re-enable model invocation so `/sprint` can call `/ledger` |
| `docs/sprints/ledger.tsv` | Reference only | Source of truth for runtime state and edge-case behavior |
| `skills/ledger/scripts/ledger.py` | Reference only | Existing correct CLI behavior; no code changes planned |
| `README.md` | Reference only | Canonical project-level command guidance |
| `Makefile` | Reference only | Canonical executable targets for build/test validation |

## Acceptance Criteria
- [ ] `/sprint` no longer fails due to `disable-model-invocation` when calling `/ledger`.
- [ ] `/sprint` documents explicit behavior for empty ledger.
- [ ] `/sprint` documents explicit behavior when no sprint is `planned`.
- [ ] `/sprint` documents explicit behavior when a sprint is already `in_progress`.
- [ ] Step 3 includes concrete guidance on where build/test commands are defined (`README.md`, `Makefile`).
- [ ] `skills/ledger/scripts/ledger.py` remains unchanged.
- [ ] Final instructions remain compatible with current command-file formatting expectations.

## Verification Plan
1. Static diff check: confirm only `commands/sprint.md` and `skills/ledger/SKILL.md` are modified.
2. Content check: verify no residual references to impossible ledger call patterns remain.
3. Scenario read-through:
   - ledger has planned sprint
   - ledger has no planned sprint
   - ledger has an existing in-progress sprint
   - ledger missing entry for requested sprint argument
4. Integration check: ensure `/sprint` and `/ledger` instructions are semantically consistent end-to-end.

## Risks and Mitigations
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Enabling model invocation broadens where ledger skill can run | Medium | Medium | Keep `allowed-tools` constrained and scope usage text to sprint workflows |
| Ambiguous policy for in-progress sprint resume vs override | Medium | Medium | Encode explicit default behavior and require explicit argument to override |
| Validation guidance drifts from actual repo commands | Low | High | Anchor wording to `README.md`/`Makefile` rather than hard-coded assumptions |

## Definition of Done
- [ ] `commands/sprint.md` updated with explicit edge-case behavior and concrete validation guidance.
- [ ] `skills/ledger/SKILL.md` updated to allow `/sprint`-driven invocation.
- [ ] Manual phase-by-phase read-through passes for all intended scenarios.
- [ ] Changes remain narrow, text-only, and aligned to Sprint 003 intent.
