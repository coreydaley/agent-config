# Node: cleanup-worktree

Reset the persistent `pr-review/` worktree to detached HEAD and delete the per-PR branch. The directory itself stays — only the branch is removed. This node is the single sink before terminal for all post-setup paths.

## Inputs

- `worktree_path`, `bare_root`, `worktree_branch` from walker state

```bash
STATE="$PR_DIR/.walk-state.json"
WORKTREE_PATH=$(scripts/walk.sh get --state "$STATE" --key worktree_path)
BARE_ROOT=$(scripts/walk.sh get --state "$STATE" --key bare_root)
WORKTREE_BRANCH=$(scripts/walk.sh get --state "$STATE" --key worktree_branch)
```

## Steps

```bash
git -C "$WORKTREE_PATH" checkout --detach HEAD
git -C "$BARE_ROOT" branch -D "$WORKTREE_BRANCH"
```

The detached HEAD is **load-bearing**: it avoids conflicts with any named branch (e.g. `main`) that might be checked out in another worktree. Per-PR branches are unique, so deleting them is safe.

If either command fails (e.g., the branch was already deleted, the worktree was manually nuked), surface the error but **continue** to terminal anyway. Cleanup is best-effort; the user can deal with leftover state manually.

## Outputs

- `pr-review/` worktree in detached HEAD state
- `pr-review-<N>` branch deleted from the bare clone

## Outgoing edges

- → `terminal` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from cleanup_worktree --to terminal
```

## Notes

- **Don't `worktree remove`.** The persistent `pr-review/` directory stays. Only the branch goes.
- **Don't `--force` the branch delete.** If `branch -D` fails, that's a signal — surface it.
- **This node always runs after setup-worktree completed.** Paths that bail before setup-worktree (e.g., `setup_failed`) go directly to terminal without passing through here.
