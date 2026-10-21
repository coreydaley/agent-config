# Node: open-pr

Push the branch to origin and open a draft PR, or push new commits to a PR that already exists. The only network writes in the skill, and they happen only after the user approved the body.

## Inputs

- `worktree`, `branch`, `repo`, `default_branch`, `remote_default`, `pr_number`, `plan_dir` from walker state
- `$PLAN_DIR/pr-body.md`

```bash
STATE="$PLAN_DIR/.walk-state.build.json"
WT=$(scripts/walk.sh get --state "$STATE" --key worktree)
BRANCH=$(scripts/walk.sh get --state "$STATE" --key branch)
ORG_REPO=$(scripts/walk.sh get --state "$STATE" --key repo)
DEFAULT=$(scripts/walk.sh get --state "$STATE" --key default_branch)
PR_NUMBER=$(scripts/walk.sh get --state "$STATE" --key pr_number || true)
```

## Steps

1. **Where does the branch go?** Always to origin. Never to `upstream`, even with write access there.
   ```bash
   ORIGIN_URL=$(git -C "$WT" remote get-url origin)
   ORIGIN_OWNER=$(echo "$ORIGIN_URL" | sed -E 's#.*[:/]([^/]+)/[^/]+(\.git)?$#\1#')
   HAS_UPSTREAM=$(git -C "$WT" remote get-url upstream >/dev/null 2>&1 && echo true || echo false)
   ```
   - `HAS_UPSTREAM=true`: origin is the fork. Push there, PR head is `<ORIGIN_OWNER>:<BRANCH>`, PR repo is `$ORG_REPO` (the upstream repo, per `lib/paths.py org-repo`).
   - `HAS_UPSTREAM=false`: origin is the repo. Push there, plain `gh pr create` on `$ORG_REPO`, no `--head` owner prefix.

2. **Title and body file.**
   ```bash
   TITLE=$(sed -n '1s/^# //p' "$PLAN_DIR/pr-body.md")
   sed '1,2d' "$PLAN_DIR/pr-body.md" > "$PLAN_DIR/.pr-body.txt"
   ```

3. **Push.**
   ```bash
   git -C "$WT" push -u origin "$BRANCH" > "$PLAN_DIR/.push.out" 2>&1; EXIT=$?
   ```
   Non-zero → show the output, stop. A rejected push (remote has commits we don't) is not something to force through. Say so and route to finalize with `pr_result=push_failed`.

4. **Existing PR** (`PR_NUMBER` set): the push updated it. Replace the title and body:
   ```bash
   gh pr edit "$PR_NUMBER" --repo "$ORG_REPO" --title "$TITLE" --body-file "$PLAN_DIR/.pr-body.txt"
   ```
   `pr_result=pushed`. Don't undraft, don't request reviewers.

5. **New PR.**
   ```bash
   HEAD_ARG=$([ "$HAS_UPSTREAM" = true ] && echo "$ORIGIN_OWNER:$BRANCH" || echo "$BRANCH")
   gh pr create --draft \
     --repo "$ORG_REPO" \
     --head "$HEAD_ARG" \
     --base "$DEFAULT" \
     --title "$TITLE" \
     --body-file "$PLAN_DIR/.pr-body.txt" > "$PLAN_DIR/.create.out" 2>&1; EXIT=$?
   ```
   Success prints the URL. Record:
   ```bash
   scripts/walk.sh set --state "$STATE" --key pr_url    --value "<url>"
   scripts/walk.sh set --state "$STATE" --key pr_number --value "<N>"
   scripts/walk.sh set --state "$STATE" --key pr_result --value "opened"
   ```
   Failure → show the output. The branch is pushed, so the user can create the PR by hand with the same title and body-file. `pr_result=create_failed`.

## Outputs

- Branch pushed to origin
- Draft PR created, or existing PR updated
- `pr_url`, `pr_number`, `pr_result` in walker state

## Outgoing edges

- → `finalize` (always, single outgoing edge, including on failure so the state gets recorded)

```bash
scripts/walk.sh transition --state "$STATE" --from open_pr --to finalize
```

## Notes

- **Always `--draft`.** The user marks the PR ready for review when the pre-review procedure is done (pr-review, pr-fix), never this skill.
- **No reviewers, no assignees, no labels.** Those are the user's calls on GitHub.
- **No issue writes.** `Closes #N` in the body links the source issue and closes it on merge.
- **One push.** No follow-up pushes, no force.
