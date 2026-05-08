# Node: verify-worktree

Phase 4: verify a pushable worktree is checked out on the right branch for each repo this sprint touches. Multi-repo: both must be set up before implementation. **Don't auto-create or auto-cd.**

## Inputs

- `repo_mode`, `repos`, `path_mode`, plus per-issue `branchName` from `context_dir`

```bash
STATE="<path>"
REPO_MODE=$(scripts/walk.sh get --state "$STATE" --key repo_mode)
REPOS=$(scripts/walk.sh get --state "$STATE" --key repos)
```

## Branch name resolution

- **Linear paths:** use the issue's `branchName` field (Linear auto-generates this, e.g. `<username>/con-1234-short-issue-slug`).
- **SPRINT.md path:** use the current branch (the user is expected to have a feature branch already; otherwise prompt for one).

## Per-repo check

For each entry in `$REPOS`:

```bash
PR_BRANCH=<resolved branch name for this repo>
EXPECTED_BARE="$HOME/Code/github.com/<org>/<repo>"

if [ "$(git branch --show-current)" = "$PR_BRANCH" ] \
   && [ "$(git rev-parse --is-bare-repository)" = "false" ]; then
  : # we're already on the right branch in a regular checkout
else
  WT_PATH=$(git -C "$EXPECTED_BARE" worktree list --porcelain \
    | awk -v b="refs/heads/$PR_BRANCH" '
        /^worktree /{p=$2}
        $0=="branch "b{print p; exit}')
  if [ -n "$WT_PATH" ]; then
    echo "Worktree exists at: $WT_PATH — cd there and re-run."
  else
    echo "No worktree for branch '$PR_BRANCH' in $EXPECTED_BARE."
    echo "Create one with:"
    echo "  git -C $EXPECTED_BARE worktree add $PR_BRANCH"
  fi
  ROUTE_TO_TERMINAL=true
fi
```

If any repo's check fails, route to `terminal` via `worktree_missing` after printing the instructions for **all** repos that need attention. The user fixes the underlying issue and re-runs.

## Multi-repo

Both worktrees must be set up before implementation begins. Verify them one at a time and report all that need attention before bailing — saves the user multiple round-trips.

## Outputs

```bash
scripts/walk.sh set --state "$STATE" --key worktree_paths --value "<JSON: repo → worktree path>"
```

## Outgoing edges

- **`worktree_ok`** → `detect-inflight`. All repos have pushable worktrees on the right branch.
- **`worktree_missing`** → `terminal`. At least one needs attention; instructions printed.

Record exactly one:

```bash
# All worktrees ready:
scripts/walk.sh transition --state "$STATE" --from verify_worktree --to detect_inflight --condition worktree_ok

# Missing — bail with instructions:
scripts/walk.sh transition --state "$STATE" --from verify_worktree --to terminal --condition worktree_missing
```

## Notes

- **Don't auto-create worktrees.** Per the user's global workflow, worktree creation is a deliberate user action.
- **Don't auto-`cd`.** The skill runs in the caller's CWD.
- **For multi-repo, surface ALL missing worktrees** in one report. The user fixes them and re-runs.
