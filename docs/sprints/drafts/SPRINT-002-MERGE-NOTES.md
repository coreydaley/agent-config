# Sprint 002 Merge Notes

## Claude Draft Strengths
- Correctly identified the core bugs (megaplan artifact, ledger checklist inconsistency)
- Right call on Phase 2 fallback for fresh repos
- Good scoping: text edits only, no architectural changes
- `.rs` → `.ext` fix is valid

## Codex Draft Strengths
- Identified two HIGH-severity issues Claude missed:
  1. `docs/sprints/README.md` doesn't exist — my Phase 3 addition would have added a broken reference
  2. Phase 5 Codex exec prompt references both `docs/sprints/README.md` (missing) and `CLAUDE.md` (exists at `agents/claude/CLAUDE.md`, not root)
- Correctly flagged that ledger audit should be whole-document, not just the one checklist line
- Identified the "no other content changed" DoD criterion as too restrictive

## Valid Critiques Accepted
1. **HIGH**: Do NOT add `docs/sprints/README.md` reference to Phase 3 — file doesn't exist; would introduce a broken instruction. Instead: P1, create the file.
2. **HIGH**: Fix Phase 5 Codex exec prompt paths: `docs/sprints/README.md` → `docs/sprints/SPRINT-001.md` (existing example), and leave `CLAUDE.md` as-is (it's generic — most projects have it at root, and target projects using this command may well have it there)
3. **MEDIUM**: Audit ALL ledger mentions across the file (not just the one checklist line)
4. **LOW**: Relax "no other content changed" DoD criterion

## Critiques Rejected (with reasoning)
- **Codex flags (--model/--full-auto)**: Codex recommended adding them; user explicitly said keep `codex exec` simple. User decision wins.
- **Reference to `agents/claude/CLAUDE.md` in Phase 1**: The file says "Read `CLAUDE.md` for project conventions". This is generic and correct for any target project. The fact that THIS repo has it at a different path is a repo-specific quirk. Keep `CLAUDE.md` generic.
- **`CLAUDE.md` in Reference section**: Same reasoning — leave as generic `CLAUDE.md`.

## Interview Refinements Applied
- Codex flags: keep `codex exec` (user said "keep it simple")
- megaplan.md: out of scope (user said superplan only)

## Final Decisions
1. Fix: "After megaplan completes" → "After superplan completes" (File Structure)
2. Fix: Output Checklist ledger line → use `/ledger sync` skill notation
3. Fix: Phase 5 Codex exec prompt: `docs/sprints/README.md` → `docs/sprints/SPRINT-001.md`
4. Fix: Reference section: `docs/sprints/README.md` → `docs/sprints/SPRINT-001.md`
5. Enhancement: Phase 2 Step 1 fallback for fresh repos
6. Enhancement: Phase 3 template `.rs` → `.ext`
7. Enhancement: Phase 7 ends with user-facing summary (analogous to Phase 8)
8. Enhancement: Full ledger audit — check all occurrences, not just checklist line
9. Drop: Phase 3 README.md reference addition (would introduce broken ref)
10. P1: Create `docs/sprints/README.md` with sprint conventions (satisfies the canonical reference)
