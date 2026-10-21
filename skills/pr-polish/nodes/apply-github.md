# Node: apply-github

Apply the approved GitHub-side categories: title, body, thread resolutions. Then route on which local categories remain.

## Inputs

- `approved`, `proposals_path`, `pr_number`, `repo` from walker state

```bash
STATE="$PLAN_DIR/.walk-state.polish.json"
APPROVED=$(scripts/walk.sh get --state "$STATE" --key approved)
PR_NUMBER=$(scripts/walk.sh get --state "$STATE" --key pr_number)
ORG_REPO=$(scripts/walk.sh get --state "$STATE" --key repo)
```

## Steps

1. **Title and body** (whichever were approved and aren't "unchanged"):
   ```bash
   gh pr edit "$PR_NUMBER" --repo "$ORG_REPO" --title "$NEW_TITLE" --body-file "$POLISH_DIR/body.md"
   ```
   Write the proposed body to `body.md` first. One `gh pr edit` call for both when both changed.

2. **Threads.** For each approved thread (resolved-by-code, plus any ambiguous ones the user named):
   ```bash
   gh api graphql -F id="$THREAD_ID" -f query='mutation($id:ID!){ resolveReviewThread(input:{threadId:$id}){ thread{ id isResolved } } }'
   ```
   Already resolved by someone else → not an error, record it.

3. **Failure** on any call: show it verbatim and stop the GitHub work. Don't half-apply silently. Record what did land. Route on the local categories anyway so approved comment edits aren't lost, unless the failure was auth or network, in which case route `github_only` to finalize and say so.

4. **Persist:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key github_results --value "<JSON: title, body, threads: applied|unchanged|failed>"
   ```

## Outputs

- PR title, body, and threads updated on GitHub
- `github_results` in walker state

## Outgoing edges

- **`comments_approved`** → `apply-comments` (comments in the approved set, with or without commits)
- **`commits_only`** → `preflight` (commits approved, comments not)
- **`github_only`** → `finalize` (neither local category approved)

```bash
scripts/walk.sh transition --state "$STATE" --from apply_github --to apply_comments --condition comments_approved
scripts/walk.sh transition --state "$STATE" --from apply_github --to preflight      --condition commits_only
scripts/walk.sh transition --state "$STATE" --from apply_github --to finalize       --condition github_only
```

## Notes

- **PR descriptions are living documents.** Editing one is normal and expected. Posted comments are not, so this node never edits a comment, only resolves threads.
- **Resolving is reversible. Say so if asked.** The reviewer can unresolve. Still, only threads the code actually addressed.
