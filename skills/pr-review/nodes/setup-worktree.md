# Node: setup-worktree

Resolve where the reviewers read the full codebase from.

- **PR mode:** create a per-PR worktree `pr-review-<N>/` at the bare clone, fetch the PR head, check it out. One worktree per PR means concurrent reviews of different PRs can't race each other over a shared checkout. The worktree is ephemeral — `cleanup-worktree` removes it (the bare clone keeps the fetched objects, so re-creating one is a checkout, not a re-download).
- **Local mode:** no worktree work at all. The reviewed state (including uncommitted changes) exists only in the user's current worktree, so that *is* the review checkout.

## Inputs

- `mode`, `pr_number` from walker state

```bash
STATE="$PR_DIR/.walk-state.review.json"
MODE=$(scripts/walk.sh get --state "$STATE" --key mode)
PR_NUMBER=$(scripts/walk.sh get --state "$STATE" --key pr_number || true)  # unset in local mode
```

## Steps — local mode

Point `worktree_path` at the current worktree and move on. Don't create anything, don't fetch anything:

```bash
WORKTREE_PATH=$(git rev-parse --show-toplevel)
scripts/walk.sh set --state "$STATE" --key worktree_path --value "$WORKTREE_PATH"
```

Do **not** set `bare_root` or `worktree_branch` — their absence is how `cleanup-worktree` knows there's nothing to clean up. Route via `setup_ok`.

## Steps — PR mode

1. **Resolve the bare clone root** (works whether we're inside a worktree or the bare root itself):
   ```bash
   BARE_ROOT=$(cd "$(git rev-parse --git-common-dir)" && pwd)
   WORKTREE_PATH="$BARE_ROOT/pr-review-$PR_NUMBER"
   ```

2. **Reap worktrees left by abandoned runs.** A review that stops at `display` never reaches `cleanup-worktree`, so its worktree survives. Only PRs that are merged or closed are safe to reap: an open one may be under review in another session right now. Never force, and never fail the run on a reap error.

   ```bash
   for wt in $(git -C "$BARE_ROOT" worktree list --porcelain | awk '/^worktree /{print $2}' | grep -E '/pr-review-[0-9]+$'); do
     n="${wt##*/pr-review-}"
     [ "$n" = "$PR_NUMBER" ] && continue                            # this run's, step 3 handles it
     [ -n "$(git -C "$wt" status --porcelain 2>/dev/null)" ] && continue
     case "$(gh pr view "$n" --json state -q .state 2>/dev/null)" in
       MERGED|CLOSED)
         git -C "$BARE_ROOT" worktree remove "$wt" 2>/dev/null &&
           git -C "$BARE_ROOT" branch -D "pr-review-$n" 2>/dev/null
         ;;
     esac
   done
   ```

   Say how many were reaped if any were, then carry on. This is the only place another run's worktree may be touched, and only once its PR is finished.

3. **Create the per-PR worktree if it doesn't exist.** If it does exist (a prior run for this PR crashed before cleanup), reuse it, but detach HEAD first so the branch can be force-updated in step 4:
   ```bash
   if [ ! -d "$WORKTREE_PATH" ]; then
     git -C "$BARE_ROOT" worktree add --detach "pr-review-$PR_NUMBER"
   else
     git -C "$WORKTREE_PATH" checkout --detach HEAD
   fi
   ```

   The `--detach` is **load-bearing**: the worktree must never check out a named branch (`main`, etc.) because named branches can only be checked out in one worktree at a time. The per-PR branch `pr-review-<N>` is checked out only after the fetch below.

4. **Fetch the PR head and check it out.** The `+` forces the branch update in case a stale `pr-review-<N>` branch survived a crashed run:
   ```bash
   git -C "$BARE_ROOT" fetch upstream "+pull/$PR_NUMBER/head:pr-review-$PR_NUMBER"
   git -C "$WORKTREE_PATH" checkout "pr-review-$PR_NUMBER"
   ```

   If `upstream` doesn't exist, fall back to `origin`. If neither has the PR, surface the gh error and route via `setup_failed`.

5. **Verify the checkout matches the reviewed snapshot.** `fetch-context` captured `diff.patch` and `head_oid` before this checkout, and the author may have pushed in between. Reviewing code that doesn't match the diff (and posting inline comments against a stale `commit_id`) is worse than failing:
   ```bash
   HEAD_OID=$(scripts/walk.sh get --state "$STATE" --key head_oid)
   ACTUAL=$(git -C "$WORKTREE_PATH" rev-parse HEAD)
   ```
   If they differ, tell the user the PR head moved since the diff was captured and route via `setup_failed` — a fresh run picks up the new head cleanly.

6. **Persist worktree paths** for downstream nodes:
   ```bash
   scripts/walk.sh set --state "$STATE" --key worktree_path  --value "$WORKTREE_PATH"
   scripts/walk.sh set --state "$STATE" --key bare_root      --value "$BARE_ROOT"
   scripts/walk.sh set --state "$STATE" --key worktree_branch --value "pr-review-$PR_NUMBER"
   ```

## Outputs

- `$WORKTREE_PATH` is a full checkout of the reviewed state (the PR head, or the user's current worktree in local mode)
- `worktree_path` in walker state; `bare_root` and `worktree_branch` too, but PR mode only

## Outgoing edges

- **`setup_ok`** → `independent-reviews`. Worktree is ready.
- **`setup_failed`** → `terminal`. Setup failed; nothing to clean up because the worktree wasn't created.

Record exactly one:

```bash
# Setup succeeded:
scripts/walk.sh transition --state "$STATE" --from setup_worktree --to independent_reviews --condition setup_ok

# Setup failed (no cleanup needed):
scripts/walk.sh transition --state "$STATE" --from setup_worktree --to terminal --condition setup_failed
```

## Failure modes

- `worktree add --detach pr-review-<N>` fails because the directory exists but isn't a worktree → surface the error, route via `setup_failed`. Don't auto-delete unknown directories.
- `fetch upstream pull/<N>/head` fails (no upstream / PR doesn't exist) → try `origin` as fallback. If both fail, route via `setup_failed`.
- `checkout pr-review-<N>` fails because the branch is somehow checked out in another worktree → another session is reviewing this same PR right now. Don't fight it: surface and bail via `setup_failed`.
- Checked-out HEAD ≠ `head_oid` (author pushed after `fetch-context`) → surface it, route via `setup_failed`, suggest re-running.
- A legacy shared `pr-review/` directory (pre-per-PR layout) may still exist at the bare root → ignore it entirely; never create, switch, or remove it.

## Notes

- **One worktree per PR.** Two concurrent reviews of *different* PRs never touch each other's checkout. Two concurrent reviews of the *same* PR still collide — the branch-checkout failure above catches that.
- **Always `--detach` before branch surgery.** Named branches checked out in a review worktree will collide with the standard worktree setup.
- **Local mode never touches the bare clone or creates branches.** The user's worktree is used read-only by the reviewers.
