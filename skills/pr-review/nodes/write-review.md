# Node: write-review

Write the final `REVIEW.md` from the (post-devil's-advocate) synthesis. This is the artifact the user reads and the source for posted GitHub content.

## Who does this

The orchestrator. This is transcription: `synthesis.md` into the REVIEW.md layout. No finding is added, dropped, reworded, or re-graded here. If something in the synthesis looks wrong, it stays, and the place to say so is `discuss` with the user.

## Inputs

- `pr_dir`, `pr_number`, `pr_title`, `base_branch`, `report_ts` from walker state
- `$PR_DIR/synthesis.md` (with devil's-advocate updates incorporated)
- `$PR_DIR/metadata.json` (for author, dates, etc.)
- `$PR_DIR/intent.md` (for the Intent & Scope section's issue numbers)
- `$PR_DIR/ci-status.txt`

```bash
STATE="$PR_DIR/.walk-state.review.json"
PR_DIR=$(scripts/walk.sh get --state "$STATE" --key pr_dir)
PR_NUMBER=$(scripts/walk.sh get --state "$STATE" --key pr_number || true)  # unset in local mode
```

## Steps

Write `$PR_DIR/REVIEW.md`. Header line by mode:

- PR mode: `# Code Review: PR #<N> — <Title>` with `**Author**: <author> | **Base**: <base branch> | **Date**: <date>`
- Local mode: `# Code Review: <branch> vs <base> (local)` with `**Head**: <short SHA><, +uncommitted changes if dirty> | **Base**: <base> | **Date**: <date>` — the reviewed state must be unambiguous from the header. CI Status section reads "n/a (local review)".

```markdown
# Code Review: PR #<N> — <Title>

**Author**: <author> | **Base**: <base branch> | **Date**: <date>

## Summary

[1 paragraph overall assessment — ready to merge, needs changes, or blocked?]

## Intent & Scope

[Carried from synthesis: what the PR description and linked GitHub
issues (with numbers) say the change is for, whether the diff
delivers it, and any intent gaps. Omit the section only when
intent.md had neither a description nor issues.]

## CI Status

[pass / fail / pending — key checks]

## Findings

| ID | Severity | Category | File:Line | Issue | Suggestion | Evidence |
|----|----------|----------|-----------|-------|------------|----------|
[All SR-prefix Blocker/High/Medium findings — main table. Evidence
carries the supporting detail from synthesis, including `canon:
<principle>` tags when the canon pass ran]

## Nits

[Low/Nit findings in a separate section to keep the main table clean]

## What's Well Done

[Only when the canon pass ran (`--canon`): the synthesis Praise
section, file:line-anchored. Omit the section entirely otherwise.]

---
*Reviewed by independent and adversarial reviewers — synthesized from separate analyses.*
*Intermediate files: $PR_DIR/*
```

## "What's Well Done" is canon-only

The section exists when `--canon` ran and the synthesis Praise section has anchored entries. Without canon there's no anchored praise to draw from, and unanchored praise is filler the author tunes out. Omit the section rather than invent bullets. The Summary paragraph can still say the change is sound when it is.

## ID Suppression and attribution

- **SR-prefix IDs appear in REVIEW.md.** They're fine here — REVIEW.md is the user-facing artifact, and the IDs help during discussion ("about SR003...").
- **IR / AR / IG / AG prefixes don't appear in REVIEW.md.** Those are internal to synthesis. (`canon: <principle>` tags in Evidence do carry through — they're rubric traceability, not reviewer attribution.)
- **Comment attribution suffix** (`*(via Claude Code)*`) is added by `post` when actually sending content to GitHub, not here.

## Outputs

- `$PR_DIR/REVIEW.md`

## Outgoing edges

- → `display` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from write_review --to display
```

## Failure modes

- synthesis.md is empty (no review found anything) → REVIEW.md still gets written, with "No findings" in the Findings section and a Summary that says so. Don't skip — the user expects a REVIEW.md to read.
