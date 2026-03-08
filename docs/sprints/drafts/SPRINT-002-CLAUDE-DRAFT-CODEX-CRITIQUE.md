# Critique of `SPRINT-002-CLAUDE-DRAFT.md` (Codex)

## Findings (Ordered by Severity)

### High
1. **Reintroduces a non-existent reference (`docs/sprints/README.md`)**
   - Claude proposes adding a Phase 3 line to follow `docs/sprints/README.md`, but that file does not exist in this repository.
   - This would create a new broken instruction in the primary planning command.
   - Fix: reference an existing source of truth (for example `docs/sprints/SPRINT-001.md`), or remove the reference entirely and keep the inlined template as canonical.

2. **Misses project-structure path corrections in Codex command prompts**
   - `superplan.md` Phase 5 currently tells Codex to use `CLAUDE.md` and `docs/sprints/README.md` in its prompt text.
   - In this repo, conventions are in `agents/claude/CLAUDE.md`, and sprint template guidance is not in `docs/sprints/README.md`.
   - Claude's plan does not include fixing these prompt paths, which leaves execution guidance inconsistent and potentially wrong.
   - Fix: update prompt text in Phase 5 to point to existing files used by this project.

### Medium
3. **Scope is too narrow relative to intent success criteria**
   - Intent asks for internal consistency, correct tools/patterns, no copy-paste artifacts, and clearer under-specified phases.
   - The draft addresses six edits, but skips broader consistency checks (Phase 1-6 parity with `megaplan.md`, checklist/file-structure alignment audit, and prompt/tooling normalization).
   - Fix: add a baseline audit phase and explicit acceptance criteria for full command consistency, not only listed spot fixes.

4. **Ledger consistency fix is partial**
   - It patches the checklist line but does not explicitly require full-document normalization of ledger invocation language.
   - Fix: grep/audit all ledger mentions in `superplan.md` and enforce one pattern (`/ledger ...` skill).

5. **Open question on Codex flags is left unresolved**
   - The sprint intent explicitly surfaced this as a decision point.
   - Deferring the decision reduces sprint decisiveness and risks ending with unchanged inconsistency between `megaplan` and `superplan`.
   - Fix: make an explicit decision in the sprint plan and encode it in acceptance criteria.

### Low
6. **"No other content changed" DoD criterion is unnecessarily restrictive**
   - This can block needed wording fixes discovered during implementation.
   - Fix: replace with "No out-of-scope structural changes" while allowing adjacent clarity edits.

## What Works Well
1. Correctly identifies two concrete defects already visible in `superplan.md` (copy text + ledger checklist mismatch).
2. Keeps implementation lightweight and focused on in-place text edits.
3. Adds useful fresh-repo fallback logic for sprint numbering.
4. Improves template language neutrality (`.rs` to `.ext`).

## Recommended Reframe

### P0 (Must Ship)
1. Fix stale/broken references across all relevant sections (`CLAUDE.md` path, missing sprint README reference, megaplan artifact text).
2. Normalize ledger usage to `/ledger` skill wording everywhere.
3. Resolve and apply the Codex flags decision (`--model`/`--full-auto`) consistently.
4. Add a full consistency pass for phases, file structure block, and output checklist.

### P1 (If Capacity Allows)
1. Add extra UX refinements (for example Phase 7 user-facing summary symmetry).
2. Consider parallel hygiene fix in `megaplan.md` only if direct inconsistency is discovered during parity review.

## Suggested Edits to Claude Draft
1. Replace the proposed `docs/sprints/README.md` addition with an existing-file reference.
2. Add explicit Phase 5 prompt-path corrections (`agents/claude/CLAUDE.md` etc.).
3. Add an implementation task for whole-document ledger phrase normalization.
4. Decide Codex command flag policy in the draft now (do not defer).
5. Relax the "no other content changed" DoD guardrail.

## Final Assessment
Claude's draft is directionally good and pragmatic, but it misses two high-impact correctness issues and under-scopes consistency validation. With those corrections, it can cleanly meet the sprint intent.
