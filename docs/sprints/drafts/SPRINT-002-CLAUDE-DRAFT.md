# Sprint 002: superplan.md Command Improvements

## Overview

`superplan.md` is the project's primary sprint-planning command, orchestrating an 8-phase collaborative workflow between Claude and Codex. It was derived from `megaplan.md` when phases 7 (Devil's Advocate) and 8 (Security Review) were added, but several artifacts and inconsistencies were introduced during that derivation.

This sprint corrects those issues: one copy-paste artifact ("megaplan" in the File Structure comment), one internal inconsistency (ledger invocation method), and several under-specified phase descriptions that could cause Claude to produce lower-quality outputs when running the command.

All changes are text edits to a single file. No new files are created.

## Use Cases

1. **Bug fix — copy-paste artifact**: The File Structure section says "After megaplan completes" instead of "After superplan completes". This is incorrect branding that could confuse users.
2. **Bug fix — ledger inconsistency**: Phase 8 correctly uses the `/ledger sync` skill, but the Output Checklist line reads `python3 docs/sprints/ledger.py sync` — the direct script path. The skill invocation is the canonical pattern used everywhere else in the project.
3. **Enhancement — Phase 3 template reference**: `megaplan.md` instructs Claude to "Follow the standard sprint template from `docs/sprints/README.md`" before showing the template. `superplan.md` dropped this guidance, reducing context for Claude.
4. **Enhancement — Phase 2 sprint numbering fallback**: No instruction for when `docs/sprints/SPRINT-*.md` doesn't exist yet (fresh repo). Claude should default to `SPRINT-001`.
5. **Enhancement — Phase 3 template language-agnosticism**: The draft template shows `path/to/file.rs` — a Rust-specific extension. This repo is shell/Markdown; the template should use `path/to/file.ext`.
6. **Enhancement — Phase 7 user communication**: Phase 8 explicitly shows the user a summary of security findings. Phase 7 does not show the user anything after processing the devil's advocate critique. Symmetry and best practice suggest a brief user summary after Phase 7 as well.

## Architecture

No new files. All changes are in-place edits to `commands/superplan.md`.

Change summary by section:
- **File Structure comment** (1 word change)
- **Output Checklist** (1 line change)
- **Phase 2 Step 1** (add 1 sentence fallback)
- **Phase 3 header** (add 1 line reference to README.md)
- **Phase 3 template** (1 occurrence: `.rs` → `.ext`)
- **Phase 7 closing** (add 1 paragraph user-facing summary step)

## Implementation Plan

### Phase 1: Bug Fixes (~40%)

**Files:**
- `commands/superplan.md`

**Tasks:**
- [ ] Fix File Structure section: "After megaplan completes" → "After superplan completes"
- [ ] Fix Output Checklist: `python3 docs/sprints/ledger.py sync` → `/ledger sync` skill

### Phase 2: Phase Enhancements (~60%)

**Files:**
- `commands/superplan.md`

**Tasks:**
- [ ] Phase 2 Step 1: add note "If no sprint files exist yet, use SPRINT-001"
- [ ] Phase 3: add line "Follow the standard sprint template from `docs/sprints/README.md`:" before the template block
- [ ] Phase 3 template: change `path/to/file.rs` → `path/to/file.ext`
- [ ] Phase 7: add closing paragraph after step 4 instructing Claude to show the user a brief summary of devil's advocate findings and what was addressed

## Files Summary

| File | Action | Purpose |
|------|--------|---------|
| `commands/superplan.md` | Modify | Apply all 6 improvements |

## Definition of Done

- [ ] "After megaplan completes" replaced with "After superplan completes"
- [ ] Output Checklist ledger line uses `/ledger sync` skill notation
- [ ] Phase 2 has fallback for fresh repos
- [ ] Phase 3 references `docs/sprints/README.md` before the template
- [ ] Phase 3 template uses `.ext` not `.rs`
- [ ] Phase 7 ends with a user-facing summary step analogous to Phase 8's summary step
- [ ] No other content changed (verify via diff)
- [ ] `megaplan.md` is NOT modified (out of scope)

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Edit bleeds into adjacent content | Low | Medium | Each change is small and targeted; verify diff after |
| Phase 7 addition makes the phase too verbose | Low | Low | Keep the addition to 2-3 sentences |
| Gemini TOML conversion breaks on new content | Low | Low | Changes are all within markdown body; no frontmatter changes |

## Security Considerations

- Text edits only; no scripts, no eval, no injection surface
- Content flows into agent system prompts — review new Phase 7 text for unintended instructions

## Dependencies

- SPRINT-001 (completed) — established project conventions this sprint follows

## Open Questions

1. Should Phase 5 codex command include `--model gpt-5.2 --full-auto` flags to match megaplan? Decision deferred to interview.
2. Should megaplan.md receive the `.rs` → `.ext` fix as well? Treating it as out-of-scope unless user says otherwise.
