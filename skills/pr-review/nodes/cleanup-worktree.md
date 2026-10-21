# Node: cleanup-worktree

Remove the per-PR worktree `pr-review-<N>/` and delete its branch. The bare clone keeps the fetched objects, so a future re-review of the same PR re-creates the worktree cheaply (checkout, not re-download). This node is the single sink before terminal for all post-review paths (post, discuss-then-nothing, posting cancelled). Setup failure never reaches here — no worktree state existed yet on that path.

## Inputs

- `mode`, `worktree_path`, `bare_root`, `worktree_branch` from walker state

```bash
STATE="$PR_DIR/.walk-state.review.json"
MODE=$(scripts/walk.sh get --state "$STATE" --key mode)
WORKTREE_PATH=$(scripts/walk.sh get --state "$STATE" --key worktree_path)
BARE_ROOT=$(scripts/walk.sh get --state "$STATE" --key bare_root || true)             # unset in local mode
WORKTREE_BRANCH=$(scripts/walk.sh get --state "$STATE" --key worktree_branch || true) # unset in local mode
```

## Steps

**Local mode: this node is a strict no-op.** `worktree_path` is the *user's own worktree* — removing or detaching anything there would clobber their checkout. If `MODE=local` (equivalently: the `bare_root`/`worktree_branch` gets above came back empty), run no git commands and transition straight to terminal.

PR mode:

```bash
git -C "$BARE_ROOT" worktree remove "$WORKTREE_PATH"
git -C "$BARE_ROOT" branch -D "$WORKTREE_BRANCH"
```

`worktree remove` refuses if the worktree has local modifications — that means something wrote to a checkout the reviewers were told is read-only. Surface that loudly rather than forcing; the user decides whether to inspect or `git worktree remove --force` it themselves.

If either command fails (e.g., the branch was already deleted, the worktree was manually nuked), surface the error but **continue** to terminal anyway. Cleanup is best-effort; the user can deal with leftover state manually.

## Outputs

- `pr-review-<N>/` worktree removed
- `pr-review-<N>` branch deleted from the bare clone

## Outgoing edges

- → `terminal` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from cleanup_worktree --to terminal
```

## Notes

- **Remove only this run's worktree** (`worktree_path` from state, always the per-PR `pr-review-<N>/`). Never touch other `pr-review-*` worktrees here — they belong to other runs, and reaping the finished ones is `setup-worktree`'s job, where the PR state is checked first. Never touch a legacy shared `pr-review/` directory if one still exists.
- **Don't `--force` anything.** A dirty worktree or a failing branch delete is a signal — surface it.
- **This node always runs after setup-worktree completed.** Paths that bail before setup-worktree (e.g., `setup_failed`) go directly to terminal without passing through here.
- **Never run the git commands in local mode.** The worktree path is the user's working copy, not a review worktree.
