# Sprint 002: superplan.md Command Improvements

## Overview

`superplan.md` is the project's primary sprint-planning command, orchestrating an 8-phase collaborative workflow between Claude and Codex. It was derived from `megaplan.md` when Phases 7 (Devil's Advocate) and 8 (Security Review) were added, but several defects were introduced during that derivation: a copy-paste artifact, mixed ledger invocation patterns, and a broken reference in both the Phase 5 Codex prompt and the Reference section.

This sprint corrects those defects and adds targeted enhancements (fresh-repo fallback, language-agnostic template, Phase 7 user summary). It also creates the missing `docs/sprints/README.md` — a file that `superplan.md` and `megaplan.md` both reference but that has never existed.

All changes are text edits to `commands/superplan.md` plus one new file.

## Guiding Principles

- Fix observed defects; do not redesign the workflow
- Prefer the smallest edit that correctly solves each problem
- Keep Gemini TOML conversion compatibility (frontmatter + Markdown body structure unchanged)
- Codex flags in Phase 5: keep `codex exec` (no `--model`/`--full-auto` flags)
- `megaplan.md`: out of scope

## P0: Must Ship

### P0-A: Create `docs/sprints/README.md`

**Goal**: Create the canonical sprint reference that `superplan.md` and `megaplan.md` both point to but that has never existed.

**Files:**
- `docs/sprints/README.md` — NEW

**Content outline:**
- Purpose of this sprint directory
- Sprint document naming convention (`SPRINT-NNN.md`, zero-padded to 3 digits)
- Standard sprint template (Overview, Use Cases, Architecture, Implementation Plan, Files Summary, Definition of Done, Risks & Mitigations, Security Considerations, Dependencies, Open Questions)
- Drafts directory convention (`drafts/SPRINT-NNN-*` intermediate files)
- Ledger file (`ledger.tsv`) — managed via `/ledger` skill

**Tasks:**
- [ ] Write `docs/sprints/README.md` following the content outline above
- [ ] Keep it minimal: naming convention + template skeleton; no process philosophy

**Acceptance:**
- File exists at `docs/sprints/README.md`
- Contains the standard sprint section headers
- `superplan.md` and `megaplan.md` can now correctly reference it

### P0-B: Bug Fixes in `commands/superplan.md`

**Goal**: Eliminate the three concrete defects that cause incorrect or misleading instructions.

**Files:**
- `commands/superplan.md`

**Tasks:**
- [ ] **File Structure section**: change "After megaplan completes" → "After superplan completes"
- [ ] **Output Checklist**: change `python3 docs/sprints/ledger.py sync` → `/ledger sync` skill
- [ ] **Ledger audit**: grep all occurrences of "ledger" in `superplan.md`; ensure every invocation uses `/ledger` skill syntax; fix any that don't
- [ ] **Phase 5 Codex exec prompt**: verify `docs/sprints/README.md` reference is accurate (now valid after P0-A); verify `CLAUDE.md` reference is appropriate; no change needed if both are correct
- [ ] **Reference section** (bottom): verify `docs/sprints/README.md` reference — no change needed if P0-A creates the file

**Acceptance:**
- `grep -n "megaplan" commands/superplan.md` returns no results in user-facing text
- `grep -n "python3.*ledger" commands/superplan.md` returns no results
- All ledger references use `/ledger` skill syntax

### P0-C: Enhancements to `commands/superplan.md`

**Goal**: Close three specific under-specifications identified during multi-agent review.

**Files:**
- `commands/superplan.md`

**Tasks:**
- [ ] **Phase 2 Step 1**: after the `ls docs/sprints/SPRINT-*.md | tail -1` block, add: "If no sprint files exist yet, start at SPRINT-001."
- [ ] **Phase 3 template**: change `path/to/file.rs` → `path/to/file.ext` (language-agnostic)
- [ ] **Phase 7 closing**: after step 4 ("Update `docs/sprints/SPRINT-NNN.md` with any revisions"), add a brief closing paragraph showing the user a summary of devil's advocate findings and what was addressed/rejected (summarized in Claude's own words, not quoting Codex output verbatim), then asking for their input before proceeding to Phase 8. Match Phase 8's style: 2-3 sentences max.

**Acceptance:**
- `grep -n "\.rs" commands/superplan.md` returns no results
- Phase 7 ends with an explicit user communication step whose wording mirrors Phase 8's summary style

## Files Summary

| File | Action | Purpose |
|------|--------|---------|
| `docs/sprints/README.md` | Create | Sprint conventions reference (P0-A) |
| `commands/superplan.md` | Modify | Fix 3 bugs + 3 enhancements (P0-B, P0-C) |

## Definition of Done

- [ ] `docs/sprints/README.md` exists and contains naming convention + standard section headers
- [ ] "After megaplan completes" replaced with "After superplan completes"
- [ ] All ledger invocations in `superplan.md` use `/ledger` skill syntax (no `python3` direct calls)
- [ ] Phase 2 has fallback note for fresh repos with no sprint files
- [ ] Phase 3 template uses `.ext` not `.rs`
- [ ] Phase 7 ends with a user-facing summary step that matches Phase 8's style (findings shown, user asked for input)
- [ ] No out-of-scope structural changes made
- [ ] **Manual end-to-end read-through**: after all edits, read `superplan.md` phase-by-phase and confirm each phase connects logically to the next
- [ ] **Regression check**: diff `superplan.md` Phases 1-6 against `megaplan.md` Phases 1-6 and confirm no unintended divergence was introduced

## Execution Order

1. Run baseline audit: `grep -n "megaplan\|python3.*ledger\|\.rs" commands/superplan.md`
2. Create `docs/sprints/README.md` (P0-A)
3. Apply P0-B bug fixes one at a time, verifying with grep after each
4. Apply P0-C enhancements
5. Run full acceptance grep checks
6. Manual phase-by-phase read-through of `superplan.md`
7. Diff `superplan.md` vs `megaplan.md` Phases 1-6 for regression check

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Edit bleeds into adjacent content | Low | Medium | Apply changes one at a time; verify with grep after each |
| Phase 7 addition is too verbose or ambiguous | Medium | Medium | Match Phase 8 style exactly; keep to 2-3 sentences |
| Gemini TOML conversion breaks | Low | Low | No frontmatter changes; body changes are plain text |
| README.md over-engineered | Low | Low | Limit to naming convention + template skeleton only |

## Security Considerations

- Text edits only (P0-B, P0-C); no scripts, no eval, no injection surface
- New Phase 7 user communication text flows into agent outputs — review wording for unintended instructions before finalizing
- New README.md is documentation only; no execution impact

## Dependencies

- SPRINT-001 (completed) — established project conventions this sprint follows

## Open Questions Resolved

| Question | Answer |
|---|---|
| Codex flags in Phase 5? | Keep `codex exec` (no flags) — user decision |
| megaplan.md in scope? | No — superplan only |
| docs/sprints/README.md: create or reference SPRINT-001.md? | Create README.md (P0-A); eliminates the flip-flop risk of pointing to SPRINT-001.md |
