# Sprint 002 Codex Draft: superplan.md Consistency and Hardening

## Sprint Objective
Make `commands/superplan.md` internally consistent, convention-aligned, and execution-safe by removing stale `megaplan` artifacts, correcting path/tool references, and tightening underspecified phase guidance without changing the 8-phase architecture.

## Problem Statement
`superplan.md` is directionally strong but has several correctness and clarity gaps that can cause operator error:
- stale references (for example, `docs/sprints/README.md`, `CLAUDE.md` at repo root, and "After megaplan completes")
- mixed ledger invocation patterns (`/ledger` skill vs `python3 docs/sprints/ledger.py sync`)
- inconsistent Codex invocation guidance compared to `megaplan.md`
- under-specified acceptance checks in added Phases 7 and 8

This sprint fixes those issues in place, with minimal scope and no workflow redesign.

## Guiding Principles
- Preserve the existing 8-phase `superplan` flow.
- Prefer small, text-only edits in `commands/superplan.md`.
- Align with current repo conventions in `agents/claude/CLAUDE.md` and `commands/sprint.md`.
- Keep Gemini TOML conversion compatibility (frontmatter + Markdown body structure unchanged).

## Scope

### In Scope
1. Correct stale references and copy-paste artifacts in `commands/superplan.md`.
2. Standardize ledger usage to `/ledger` skill patterns.
3. Align Phase 5 Codex command guidance with project policy.
4. Clarify deliverables/checklists for Phases 7 and 8.
5. Ensure file structure and output checklist match actual 8-phase outputs.

### Out of Scope
1. Reworking workflow sequencing or removing phases.
2. Adding new files/scripts/automation outside `commands/superplan.md`.
3. Updating `megaplan.md` unless a direct blocker is discovered.

## Key Decisions
1. **Phase 5 Codex command flags**: include `--model` and `--full-auto` for parity with `megaplan.md` and reproducibility.
2. **`megaplan.md` sync strategy**: do not broaden Sprint-002 scope; only patch `megaplan.md` if a required shared fix is discovered while validating Phase 1-6 parity.

## Implementation Plan

### Phase 1: Baseline Audit and Delta Map
**Files:**
- `commands/superplan.md`
- `commands/megaplan.md`
- `commands/sprint.md`
- `agents/claude/CLAUDE.md`

**Tasks:**
- [ ] Build a section-by-section diff map (`superplan` vs `megaplan`) limited to Phases 1-6 and shared boilerplate.
- [ ] Record each concrete inconsistency as a required edit.
- [ ] Confirm ledger invocation convention from `commands/sprint.md`.

### Phase 2: Consistency and Reference Fixes
**Files:**
- `commands/superplan.md`

**Tasks:**
- [ ] Replace stale path references to match repo reality (`agents/claude/CLAUDE.md` and actual sprint conventions source).
- [ ] Remove/replace `docs/sprints/README.md` references (file currently absent).
- [ ] Fix copy text from "After megaplan completes" to "After superplan completes".
- [ ] Ensure all phase descriptions and filenames consistently use the same naming.

### Phase 3: Tooling and Invocation Alignment
**Files:**
- `commands/superplan.md`

**Tasks:**
- [ ] Standardize ledger actions to `/ledger ...` skill usage (including final sync wording).
- [ ] Update Phase 5 Codex command to include `--model` and `--full-auto` flags.
- [ ] Ensure command snippets are executable and quote-safe.

### Phase 4: Phase 7/8 Hardening
**Files:**
- `commands/superplan.md`

**Tasks:**
- [ ] Tighten Devil's Advocate incorporation rules (what to patch vs what to annotate).
- [ ] Tighten Security Review integration rules (required handling of Critical/High findings).
- [ ] Ensure checklist items correspond to explicit required actions in the phase text.

### Phase 5: Verification Pass
**Files:**
- `commands/superplan.md`

**Tasks:**
- [ ] Run a full manual read-through as if executing the command start-to-finish.
- [ ] Verify every referenced file/path exists or is intentionally generated during workflow.
- [ ] Verify all listed deliverables appear in file structure and output checklist exactly once.

## Files Summary

| File | Action | Purpose |
|---|---|---|
| `commands/superplan.md` | Modify | Correct inconsistencies, stale references, and under-specified guidance |
| `commands/megaplan.md` | Reference only (default) | Canonical baseline for Phases 1-6 parity |
| `commands/sprint.md` | Reference only | Canonical ledger skill usage pattern |
| `agents/claude/CLAUDE.md` | Reference only | Project-structure convention source |

## Acceptance Criteria
- [ ] `superplan.md` contains no stale `megaplan` wording in user-facing instructions.
- [ ] No references remain to non-existent `docs/sprints/README.md`.
- [ ] CLAUDE convention references point to `agents/claude/CLAUDE.md`.
- [ ] Ledger usage is consistently skill-based (`/ledger`) and does not regress to direct python invocation.
- [ ] Phase 5 Codex invocation includes `--model` and `--full-auto`.
- [ ] Phases 7 and 8 have explicit, testable incorporation rules reflected in checklist items.
- [ ] File structure block and output checklist accurately reflect all 8-phase artifacts.

## Verification Plan
1. Structural diff check: compare `superplan.md` against `megaplan.md` for Phases 1-6 to ensure only intentional differences.
2. Reference integrity check: grep for stale paths/terms (`README.md` in `docs/sprints`, `After megaplan completes`, root `CLAUDE.md` reference where inappropriate).
3. Command usability review: validate every shell block is syntactically plausible and context-correct.
4. End-to-end dry execution review: walk each phase and confirm no missing prerequisite instructions.

## Risks and Mitigations
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Over-correcting and diverging from `megaplan` intentionally | Medium | Medium | Restrict edits to observed defects and 8-phase-specific needs |
| Breaking Gemini TOML conversion compatibility | Low | High | Preserve frontmatter shape and plain Markdown body structure |
| Ambiguity around missing sprint template file | High | Medium | Replace reference with concrete in-repo examples (`SPRINT-001.md`) |

## Definition of Done
- [ ] `commands/superplan.md` updated and internally consistent.
- [ ] All acceptance criteria pass via manual verification.
- [ ] Changes stay scoped to sprint intent (no architectural expansion).
- [ ] Document is ready for immediate use in the next superplan run.
