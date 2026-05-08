# Node: write-iteration-review

Write the iteration's final `REVIEW.md` from the (post-devils-advocate) synthesis. This is the artifact `address` consumes. Single outgoing edge to `address` if there are addressable findings, otherwise to `decide`.

## Inputs

- `iter_dir`, `pr_dir`, `current_iter` from walker state
- `$ITER_DIR/synthesis.md` (with devils-advocate updates incorporated)

```bash
STATE="$PR_DIR/.walk-state.json"
ITER_DIR=$(scripts/walk.sh get --state "$STATE" --key iter_dir)
PR_DIR=$(scripts/walk.sh get --state "$STATE" --key pr_dir)
CURRENT_ITER=$(scripts/walk.sh get --state "$STATE" --key current_iter)
```

## Steps

Write `$ITER_DIR/REVIEW.md`:

```markdown
# Self-Review: iteration <N> — <TS>

## Summary

[1 paragraph: what shape is this iteration — mostly cosmetic / mix of real
issues / single deal-breaker / nothing of concern.]

## Findings

| ID | Severity | Category | File:Line | Issue | Suggestion |
|----|----------|----------|-----------|-------|------------|
[All SR-prefix Blocker/High/Medium findings — main table]

## Nits

[Low/Nit findings in a separate section to keep the main table clean]

## What's Well Done

[2-4 bullets on what the diff gets right — required, not optional. Even on
iterations with serious problems, find specific things the author got
right. Reviews that read as "everything is wrong" are unhelpful.]

---
*Reviewed by Claude + Codex — synthesized from independent reviewers,
attacked by Codex devils-advocate, incorporated by orchestrator.*
*Intermediate files: $ITER_DIR/{claude,codex}-review.md, synthesis.md, devils-advocate.md*
```

## ID Suppression and downstream contract

- **SR-prefix IDs appear in REVIEW.md** — they're fine here, REVIEW.md is internal to this skill (consumed by `address`, not posted to GitHub).
- **CR / CX prefixes don't appear in REVIEW.md** — those are scoped to synthesis input.
- **No internal IDs leak into code, commits, or PR comments.** That's `address`'s job to enforce when it applies fixes (mirrors the ID Suppression Rule from `SPRINT-WORKFLOW.md`).

## "What's Well Done" is required

This section is **required**, not optional. Even when the iteration finds real problems, identify 2-4 specific things the diff gets right (test structure, named function, useful comment, sensible default, careful edge-case handling). Required-positive-feedback is a property of healthy review — and on the loop's later iterations as the diff improves, this section gets longer naturally.

## Outputs

- `$ITER_DIR/REVIEW.md`

## Outgoing edges

Two outgoing edges. Pick based on whether REVIEW.md has anything `address` can act on:

- **`addressable`** → `address`. REVIEW.md has at least one finding the agent can act on without user input (most findings).
- **`no_addressable`** → `decide`. REVIEW.md is empty, OR every finding requires user judgment (ambiguous root cause, design call, conflict with another finding the user must arbitrate).

When in doubt, route to `address`. The address node will re-evaluate per finding and escalate the ones it can't resolve, which is safer than skipping the address pass entirely.

Record the transition (pick exactly one):

```bash
# If addressable:
scripts/walk.sh transition --state "$STATE" --from write_iteration_review --to address --condition addressable

# If no_addressable:
scripts/walk.sh transition --state "$STATE" --from write_iteration_review --to decide --condition no_addressable
```

## Failure modes

- synthesis.md is empty (both reviewers found nothing) → REVIEW.md still gets written, with "No findings" in the Findings section and a brief positive assessment in What's Well Done. Route via `no_addressable` to `decide`.
- All synthesis findings have status hints from devils-advocate that they require user judgment → `no_addressable`. The user will see them at `escalate`.
