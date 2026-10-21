# Node: apply-commits

Rewrite the branch history to the approved groups and force-push with a lease. Rewrite regime only, after preflight passed.

## Inputs

- `worktree`, `base_ref`, `branch`, `proposals_path` from walker state
- Staged comment edits from apply-comments, if any

```bash
STATE="$PLAN_DIR/.walk-state.polish.json"
WT=$(scripts/walk.sh get --state "$STATE" --key worktree)
BASE_REF=$(scripts/walk.sh get --state "$STATE" --key base_ref)
BRANCH=$(scripts/walk.sh get --state "$STATE" --key branch)
```

## Steps

1. **Safety tag** so the old history is one command away:
   ```bash
   git -C "$WT" tag "pr-polish-backup-$(date +%Y%m%dT%H%M%S)" HEAD
   ```
   finalize prints the tag and how to restore from it.

2. **Soft reset** to the base, so every change on the branch (plus the staged comment edits) becomes staged-uncommitted:
   ```bash
   git -C "$WT" reset --soft "$BASE_REF"
   ```

3. **Recommit per approved group**, foundational first:
   ```bash
   git -C "$WT" restore --staged .
   git -C "$WT" add <explicit files for this group>
   git -C "$WT" commit -F - <<'EOF' > /tmp/pr-polish-commit.out 2>&1; EXIT=$?
   <type>(<scope>): <summary>

   <why, only when the summary doesn't say it>

   Refs #123
   Co-authored-by: Claude <noreply@anthropic.com>
   EOF
   ```
   Rules per `lib/code-hygiene.md`. `Refs #N` only when an original commit in the group had it. Trailers carried, never invented. Exit status read directly, `git log -1` confirmed per commit. Hook failure → stop, leave the tree as it is, route to finalize with the partial state and the backup tag named.

   After the last group, `git -C "$WT" status --porcelain` must be empty. Anything left unstaged means a file was missed from every group. Stop and surface rather than dropping it.

4. **Force-push with a lease:**
   ```bash
   git -C "$WT" push --force-with-lease origin "$BRANCH" > /tmp/pr-polish-push.out 2>&1; EXIT=$?
   ```
   Rejected → someone pushed since preflight. Don't retry, never `--force`. Say so. The local branch is rewritten and divergent. finalize prints both recovery paths (re-run polish after fetching, or `git reset --hard origin/<branch>` to discard the rewrite).

5. **Persist:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key commit_results --value "<JSON: groups committed, pushed true|false, backup tag>"
   ```

## Outputs

- Rewritten history, pushed (or not)
- A local backup tag of the pre-rewrite HEAD
- `commit_results` in walker state

## Outgoing edges

- → `finalize` (always, single outgoing edge, success or failure)

```bash
scripts/walk.sh transition --state "$STATE" --from apply_commits --to finalize
```

## Constraints

- **`--force-with-lease` only.** Never `--force`.
- **Never after human review.** preflight re-checked. If somehow a human comment appears between preflight and here, the lease rejection is the last line of defense, and it holds.
- **Never `--no-verify`, never `--amend`.**
- **Never push to any ref but the PR's head branch.**
- **Never merge.**
