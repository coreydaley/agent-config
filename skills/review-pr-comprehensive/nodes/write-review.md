# Node: write-review

Write the final `REVIEW.md` from the (post-devil's-advocate) synthesis. This is the artifact the user reads and the source for posted GitHub content.

## Inputs

- `pr_dir`, `pr_number`, `pr_title`, `base_branch`, `report_ts` from walker state
- `$PR_DIR/synthesis.md` (with devil's-advocate updates incorporated)
- `$PR_DIR/metadata.json` (for author, dates, etc.)
- `$PR_DIR/ci-status.txt`

```bash
STATE="$PR_DIR/.walk-state.json"
PR_DIR=$(scripts/walk.sh get --state "$STATE" --key pr_dir)
PR_NUMBER=$(scripts/walk.sh get --state "$STATE" --key pr_number)
```

## Steps

Write `$PR_DIR/REVIEW.md`:

```markdown
# Code Review: PR #<N> — <Title>

**Author**: <author> | **Base**: <base branch> | **Date**: <date>

## Summary

[1 paragraph overall assessment — ready to merge, needs changes, or blocked?]

## CI Status

[pass / fail / pending — key checks]

## Findings

| ID | Severity | Category | File:Line | Issue | Suggestion |
|----|----------|----------|-----------|-------|------------|
[All SR-prefix Blocker/High/Medium findings — main table]

## Nits

[Low/Nit findings in a separate section to keep the main table clean]

## What's Well Done

[2-4 bullets on what the PR does right — required, not optional]

---
*Reviewed by Claude + Codex — synthesized from independent analyses.*
*Intermediate files: $PR_DIR/*
```

## Required: "What's Well Done" section

This section is **required**, not optional. Even on PRs with serious problems, find 2-4 things the author got right (test structure, named function, useful comment, sensible default). Reviews that read as "everything is wrong" are unhelpful and the author tunes them out.

## ID Suppression and attribution

- **SR-prefix IDs appear in REVIEW.md.** They're fine here — REVIEW.md is the user-facing artifact, and the IDs help during discussion ("about SR003...").
- **CR / CX prefixes don't appear in REVIEW.md.** Those are internal to synthesis.
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

- synthesis.md is empty (both reviewers found nothing) → REVIEW.md still gets written, with "No findings" in the Findings section and the What's Well Done section based on a brief positive assessment of the diff. Don't skip — the user expects a REVIEW.md to read.
