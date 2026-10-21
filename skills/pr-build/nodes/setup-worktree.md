# Node: setup-worktree

Find or create the worktree for the plan's branch and make sure it's a clean place to build. All later nodes operate on `$WT` by absolute path, never on the shell's cwd.

## Inputs

- `repo_root`, `branch`, `branch_proposed`, `default_branch`, `base_sha` from walker state

```bash
STATE="$PLAN_DIR/.walk-state.build.json"
ROOT=$(scripts/walk.sh get --state "$STATE" --key repo_root)
BRANCH=$(scripts/walk.sh get --state "$STATE" --key branch)
DEFAULT=$(scripts/walk.sh get --state "$STATE" --key default_branch)
```

## Steps

1. **Classify the layout.**
   ```bash
   IS_BARE=$(git -C "$ROOT" rev-parse --is-bare-repository)
   HAS_UPSTREAM=$(git -C "$ROOT" remote get-url upstream >/dev/null 2>&1 && echo true || echo false)
   ```
   - Bare clone (`IS_BARE=true`): the standard layout. Worktrees live at `$ROOT/<branch>/`. Steps 2 to 4.
   - Regular clone (`IS_BARE=false`, with or without an upstream): the clone is the workspace. Step 5.

2. **Resolve the base ref fresh.** When an `upstream` remote exists, origin is a fork and its default branch is stale by construction, so always fetch the canonical one:
   ```bash
   REMOTE=$([ "$HAS_UPSTREAM" = true ] && echo upstream || echo origin)
   git -C "$ROOT" fetch "$REMOTE" "$DEFAULT" --quiet
   BASE_REF="$REMOTE/$DEFAULT"
   ```
   Sanity check: `git -C "$ROOT" log -1 --format=%ad "$BASE_REF"` should be recent. If the plan pinned a `base_sha` and the fresh base has moved past it, that's expected. Note it for the summary. Don't rebase existing work here.

3. **Existing worktree for the branch?**
   ```bash
   WT=$(git -C "$ROOT" worktree list --porcelain | awk -v b="refs/heads/$BRANCH" '/^worktree /{p=$2} $0=="branch "b{print p}')
   ```
   - **Found**: confirm it's actually on `$BRANCH` (`git -C "$WT" branch --show-current`). Wrong branch → bail with the path, the user untangles it. Then check cleanliness (step 6).
   - **Not found** → step 4.

4. **Create it.** Ask first with `AskUserQuestion` (nothing has been displayed yet this turn, so a dialog is fine): "No worktree for `<branch>`. Create at `<ROOT>/<branch>` from `<BASE_REF>`? (create / cancel)". On create:
   ```bash
   if git -C "$ROOT" rev-parse --verify "refs/heads/$BRANCH" >/dev/null 2>&1 \
      || git -C "$ROOT" rev-parse --verify "refs/remotes/origin/$BRANCH" >/dev/null 2>&1; then
     git -C "$ROOT" worktree add "$ROOT/$BRANCH" "$BRANCH"        # branch exists locally or on origin
   else
     git -C "$ROOT" worktree add -b "$BRANCH" "$ROOT/$BRANCH" "$BASE_REF"   # brand new, from the fresh base
   fi
   WT="$ROOT/$BRANCH"
   ```
   Explicit path argument always, so slash-bearing branch names don't get misread. Failure (branch checked out elsewhere, path collision) → print the error verbatim, route `worktree_missing`.

   When `branch_proposed=true` and the branch was just created, the proposal is now real. finalize drops the `(proposed)` marker from PLAN.md.

5. **Regular clone.** `WT="$ROOT"`. If `git branch --show-current` isn't `$BRANCH`: dirty tree → ask stash / cancel. Then `git checkout "$BRANCH"` if it exists (never `-B`, it resets the pointer) or `git checkout -b "$BRANCH" "$BASE_REF"` if it doesn't. Cancel → `worktree_missing`.

6. **Clean?** `git -C "$WT" status --porcelain`. Dirty → show it and ask keep / stash / cancel. Keep means the user knows what's there and implement builds on top. Stash uses `git -C "$WT" stash push -u -m "pr-build auto-stash <TS>"` and the summary reminds them. Cancel → `worktree_missing`.

7. **Persist:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key worktree   --value "$WT"
   scripts/walk.sh set --state "$STATE" --key base_ref   --value "$BASE_REF"
   scripts/walk.sh set --state "$STATE" --key remote_default --value "$REMOTE"
   ```

## Outputs

- A worktree at `$WT` on `$BRANCH`, clean or knowingly kept dirty
- `worktree`, `base_ref`, `remote_default` in walker state

## Outgoing edges

- **`worktree_ok`** → `detect-inflight`
- **`worktree_missing`** → `terminal` (user cancelled, or creation failed. Diagnostics already printed)

```bash
scripts/walk.sh transition --state "$STATE" --from setup_worktree --to detect_inflight --condition worktree_ok
scripts/walk.sh transition --state "$STATE" --from setup_worktree --to terminal        --condition worktree_missing
```

## Notes

- **Never `git checkout` a different branch inside an existing bare-clone worktree.** One worktree per branch. That's the whole point of the layout.
- **Never base on a fork's default branch.** When `upstream` exists, `origin/main` only moves when someone syncs it.
- **A `pr-review-<N>/` worktree is never a build target.** Those belong to pr-review and are read-only by convention. If the found worktree path matches that pattern, bail.
