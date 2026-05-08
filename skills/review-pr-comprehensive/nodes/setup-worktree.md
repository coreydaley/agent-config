# Node: setup-worktree

Create or switch the persistent `pr-review/` worktree at the bare clone, fetch the PR head, check it out. The worktree is **never deleted**, only switched between reviews — `cleanup-worktree` resets it to detached HEAD.

## Inputs

- `pr_number` from walker state

```bash
STATE="$PR_DIR/.walk-state.json"
PR_NUMBER=$(scripts/walk.sh get --state "$STATE" --key pr_number)
```

## Steps

1. **Resolve the bare clone root** (works whether we're inside a worktree or the bare root itself):
   ```bash
   BARE_ROOT=$(cd "$(git rev-parse --git-common-dir)" && pwd)
   WORKTREE_PATH="$BARE_ROOT/pr-review"
   ```

2. **Create the persistent worktree if it doesn't exist:**
   ```bash
   if [ ! -d "$WORKTREE_PATH" ]; then
     git -C "$BARE_ROOT" worktree add --detach pr-review
   fi
   ```

   The `--detach` is **load-bearing**: the `pr-review` worktree must never check out a named branch (`main`, etc.) because named branches can only be checked out in one worktree at a time. Per-PR branches like `pr-review-<N>` are fine because they're unique.

3. **Fetch the PR head and switch the worktree:**
   ```bash
   git -C "$BARE_ROOT" fetch upstream "pull/$PR_NUMBER/head:pr-review-$PR_NUMBER"
   git -C "$WORKTREE_PATH" checkout "pr-review-$PR_NUMBER"
   ```

   If `upstream` doesn't exist, fall back to `origin`. If neither has the PR, surface the gh error and route via `setup_failed`.

4. **Persist worktree paths** for downstream nodes:
   ```bash
   scripts/walk.sh set --state "$STATE" --key worktree_path  --value "$WORKTREE_PATH"
   scripts/walk.sh set --state "$STATE" --key bare_root      --value "$BARE_ROOT"
   scripts/walk.sh set --state "$STATE" --key worktree_branch --value "pr-review-$PR_NUMBER"
   ```

## Outputs

- `$WORKTREE_PATH` is a full checkout of the PR head
- `worktree_path`, `bare_root`, `worktree_branch` in walker state

## Outgoing edges

- **`setup_ok`** → `decide-prior`. Worktree is ready.
- **`setup_failed`** → `terminal`. Setup failed; nothing to clean up because the worktree wasn't created.

Record exactly one:

```bash
# Setup succeeded:
scripts/walk.sh transition --state "$STATE" --from setup_worktree --to decide_prior --condition setup_ok

# Setup failed (no cleanup needed):
scripts/walk.sh transition --state "$STATE" --from setup_worktree --to terminal --condition setup_failed
```

## Failure modes

- `worktree add --detach pr-review` fails because the directory exists but isn't a worktree → surface the error, route via `setup_failed`. Don't auto-delete unknown directories.
- `fetch upstream pull/<N>/head` fails (no upstream / PR doesn't exist) → try `origin` as fallback. If both fail, route via `setup_failed`.
- `checkout pr-review-<N>` fails because the branch is somehow already in another worktree → use `git worktree remove` only if the user explicitly asks. By default, surface and bail via `setup_failed`.

## Notes

- **The `pr-review/` worktree is persistent.** Don't delete it. `cleanup-worktree` only resets it to detached HEAD and deletes the per-PR branch.
- **Always `--detach`.** Named branches checked out in `pr-review/` will collide with the standard worktree setup.
