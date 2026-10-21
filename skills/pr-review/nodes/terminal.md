# Node: terminal

Sink. Print a brief confirmation and stop.

## Inputs

- Walker history (for telling the user what happened)
- `pr_dir` from walker state

## Steps

1. **Print a one-line summary** based on the last transition:
   - From `cleanup-worktree → terminal` (after `post`): "Posted review to PR #<N>." Include the URL if available.
   - From `cleanup-worktree → terminal` (after `ask-next-action [user_nothing]`): "Review saved at `$PR_DIR/REVIEW.md` — no further action taken."
   - From `cleanup-worktree → terminal` (after `ask-post-style [user_cancel]`): "Review saved at `$PR_DIR/REVIEW.md` — posting cancelled."
   - From `setup-worktree → terminal [setup_failed]`: "Worktree setup failed. See error above."

2. **Point at the artifacts** (only when artifacts were produced this run):
   ```
   Artifacts:
     $PR_DIR/REVIEW.md            the final review
     $PR_DIR/synthesis.md         deduplicated, calibrated findings
     $PR_DIR/devils-advocate.md   the devil's-advocate challenge
     $PR_DIR/adjudication.md      a ruling per challenge
     $PR_DIR/review-independent.md independent-reviewer, dimensions
     $PR_DIR/review-adversarial.md adversarial-reviewer, dimensions
     $PR_DIR/canon-independent.md independent-reviewer, Google eng-practices (--canon only)
     $PR_DIR/canon-adversarial.md adversarial-reviewer, Google eng-practices (--canon only)
     $PR_DIR/diff.patch           the diff
     $PR_DIR/intent.md            author intent: plan (own mode), PR description, linked issues
     $PR_DIR/google-principles.md canon rubric snapshot (--canon only)
     $PR_DIR/metadata.json        PR metadata snapshot
     $PR_DIR/ci-status.txt        CI status at review time
     $PR_DIR/commit-log.txt       branch commits (local mode only)
     $PR_DIR/review-payload.json  posted inline-review payload (inline posts only)
   ```

   Omit lines whose file wasn't produced this run.

3. **Stop.** No transitions, no further work.

## Outputs

- Brief printed summary to the user.

## Outgoing edges

None. Terminal is a sink.

## Notes

- **Don't suggest re-running** unless the user asks.
- **Don't print the full REVIEW.md again** — `display` already did that.
- **Worktree is already cleaned** (or wasn't set up). Don't re-run cleanup commands here.
