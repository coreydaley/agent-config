# Node: terminal

Sink. Print a brief confirmation and stop.

## Inputs

- Walker history (for telling the user what happened)
- `pr_dir` from walker state

## Steps

1. **Print a one-line summary** of how the run ended. Look at the walker's last transition to know which terminal route was taken:
   - From `post → terminal`: "Posted review to PR #<N>." Include the URL if available.
   - From `show-existing → terminal`: "Showed prior review from `<prior_dir>/REVIEW.md`."
   - From `confirm-prior-review → terminal [user_cancel]`: "Cancelled — no review run."
   - From `ask-next-action → terminal [user_nothing]`: "Review saved at `$PR_DIR/REVIEW.md` — no further action taken."
   - From `ask-post-style → terminal [user_cancel]`: "Review saved at `$PR_DIR/REVIEW.md` — posting cancelled."
2. **Point at the artifacts** if any were produced this run:
   ```
   Artifacts:
     $PR_DIR/REVIEW.md           the review
     $PR_DIR/diff.patch          the diff
     $PR_DIR/metadata.json       PR metadata snapshot
     $PR_DIR/ci-status.txt       CI status at review time
   ```
3. **Stop.** No transitions, no further work.

## Outputs

- Brief printed summary to the user.

## Outgoing edges

None. Terminal is a sink.

## Notes

- **Don't suggest re-running** unless the user asks. The terminal node is meant to be a clean exit; suggestions belong in the action gates upstream.
- **Don't print the full REVIEW.md again** — `display` already did that, and the user has it in context.
