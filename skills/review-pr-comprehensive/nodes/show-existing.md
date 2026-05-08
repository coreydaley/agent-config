# Node: show-existing

User picked "open existing review instead." Print the prior REVIEW.md so the user has it inline, then route to `cleanup-worktree` (the worktree was set up before this branch, so cleanup is owed).

## Inputs

- `prior_dir` from walker state

```bash
STATE="$PR_DIR/.walk-state.json"
PRIOR_DIR=$(scripts/walk.sh get --state "$STATE" --key prior_dir)
```

## Steps

1. **Find the prior REVIEW.md:** `$PRIOR_DIR/REVIEW.md`. If missing (e.g. the prior run cancelled before writing), say so and offer to fall back to `claude-review.md` or `synthesis.md` from the prior run if those exist.

2. **Print the file content inline.** Render as markdown so the user reads it directly in the conversation. Don't just point at the path.

3. **Append the absolute path** on its own line at the end:
   ```
   📄 Prior review: /full/path/to/$PRIOR_DIR/REVIEW.md
   ```

## Outputs

- The prior REVIEW.md content printed inline. No file changes.

## Outgoing edges

- → `cleanup-worktree` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from show_existing --to cleanup_worktree
```

## Notes

- **No new review files written.** This branch is "open the prior review," not "write a new one."
- **No GitHub posting.** This branch shows local artifacts only.
- **Cleanup still runs.** `setup-worktree` already created/switched the worktree, so we owe a reset before terminal. The cleanup node handles it.
