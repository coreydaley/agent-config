# Node: verify-worktree

This skill writes code, so it has to run from a regular (non-bare) git worktree on the PR head branch. If we're not there, print the existing worktree path (or the `worktree add` command) and bail. **Never auto-create worktrees, never auto-`cd`.** The user owns those decisions.

## Inputs

- `pr_number` from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
PR_NUMBER=$(scripts/walk.sh get --state "$STATE" --key pr_number)
```

## Steps

1. **Look up the PR's head branch and head repo.**
   ```bash
   PR_HEAD=$(gh pr view "$PR_NUMBER" --json headRefName -q .headRefName)
   PR_REPO=$(gh pr view "$PR_NUMBER" --json headRepository,headRepositoryOwner \
     -q '.headRepositoryOwner.login + "/" + .headRepository.name')
   ```

2. **Are we already on the right branch in a non-bare checkout?**
   ```bash
   CUR=$(git branch --show-current 2>/dev/null || echo "")
   IS_BARE=$(git rev-parse --is-bare-repository 2>/dev/null || echo "true")
   if [ "$IS_BARE" = "false" ] && [ "$CUR" = "$PR_HEAD" ]; then
     # good — proceed
   fi
   ```
   If both checks pass, persist `pr_head` and `pr_repo` in walker state and route via `worktree_ok`.

3. **Otherwise, find an existing worktree.**
   - Discover the bare clone via `git rev-parse --git-common-dir`, falling back to `~/Code/github.com/$PR_REPO`.
   - List worktrees on the bare clone and find one whose branch is `refs/heads/$PR_HEAD`:
     ```bash
     git -C "$BARE_ROOT" worktree list --porcelain \
       | awk -v b="refs/heads/$PR_HEAD" '
           /^worktree /{p=$2}
           $0=="branch "b{print p; exit}'
     ```
   - If a worktree exists, print:
     ```
     PR head branch '$PR_HEAD' is checked out at:
       <path>
     cd there and re-run this skill.
     ```
   - If the bare clone exists but no worktree on that branch, print:
     ```
     No worktree found for branch '$PR_HEAD' in $BARE_ROOT.
     Create one and switch to it:
       git -C $BARE_ROOT worktree add $PR_HEAD
       cd $BARE_ROOT/$PR_HEAD
     ```
   - If the bare clone itself is missing, print:
     ```
     No bare clone found for $PR_REPO.
     Expected at: $HOME/Code/github.com/$PR_REPO
     Clone it per the global GitHub workflow before running this skill.
     ```
   - In all three sub-cases, route via `worktree_missing` to terminal.

4. **Persist `pr_head` and `pr_repo`** when routing on `worktree_ok` so downstream nodes don't re-shell out:
   ```bash
   scripts/walk.sh set --state "$STATE" --key pr_head --value "$PR_HEAD"
   scripts/walk.sh set --state "$STATE" --key pr_repo --value "$PR_REPO"
   ```

## Outputs

- `pr_head`, `pr_repo` in walker state (only on success)
- A clear printed message on failure pointing at the next user step

## Outgoing edges

- **`worktree_ok`** → `load-findings`. Already on PR head branch in a non-bare checkout.
- **`worktree_missing`** → `terminal`. Wrong branch, wrong repo, no worktree, or no bare clone. Clear printed instructions.

Record exactly one:

```bash
# Success:
scripts/walk.sh transition --state "$STATE" --from verify_worktree --to load_findings --condition worktree_ok

# Failure (any of the four sub-cases above):
scripts/walk.sh transition --state "$STATE" --from verify_worktree --to terminal --condition worktree_missing
```

## Failure modes

- `gh pr view` fails (bad PR / no auth) → already handled by `init`; if it surfaces here, bail via `worktree_missing` with the gh error.
- User has uncommitted changes on the right branch — that's *fine*. This skill writes code on top; we don't gate on a clean tree.

## Notes

- **Don't auto-create worktrees.** Per the user's global workflow, worktree creation is a deliberate user action.
- **Don't auto-`cd`.** The skill runs in the caller's CWD. If they're in the wrong place, we tell them where to go.
