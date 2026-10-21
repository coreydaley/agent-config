# Node: apply-comments

Apply the approved comment edits with exact-string replacements, one at a time. Then either commit them (append regime, or no commit rewrite approved) or leave them staged for the rewrite to fold in.

## Inputs

- `approved`, `proposals_path`, `worktree`, `regime` from walker state

```bash
STATE="$PLAN_DIR/.walk-state.polish.json"
WT=$(scripts/walk.sh get --state "$STATE" --key worktree)
```

## Steps

1. **Each approved comment edit:** `Edit` with the exact `old_string` and `new_string` from `proposals.json`. One file, one edit at a time. Delete means the whole comment line goes, including its newline, and any now-orphaned blank line above a declaration is checked so formatting stays clean. Never `sed`, never bulk.

   If `old_string` no longer matches (the file moved on), record that edit as `skipped` and continue.

2. **Comment-only.** If a replacement would change anything that isn't a comment, don't apply it. Drop it with a note.

3. **Targeted tests** for touched packages only when a language treats comments as code (a doc comment that's also a directive, a `//go:` pragma). Otherwise a build is enough: `go build ./...` or the repo's equivalent. Red → revert the offending edit.

4. **Stage:** `git -C "$WT" add <files touched>`.

5. **Commit or hold:**
   - Commits **approved** (rewrite regime): leave the changes staged. apply-commits folds them into the regrouped history.
   - Commits **not approved**, or append regime: one commit.
     ```
     chore(<scope>): tighten comments

     Co-authored-by: Claude <noreply@anthropic.com>
     ```
     Then push, normal push, no force: `git -C "$WT" push origin "$BRANCH"`. In append regime this is the only way the edits reach the PR.

6. **Persist:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key comment_results --value "<JSON: applied, skipped, dropped, commit sha or held>"
   ```

## Outputs

- Edited comment lines, staged or committed and pushed
- `comment_results` in walker state

## Outgoing edges

- **`commits_approved`** → `preflight`
- **`no_commits`** → `finalize`

```bash
scripts/walk.sh transition --state "$STATE" --from apply_comments --to preflight --condition commits_approved
scripts/walk.sh transition --state "$STATE" --from apply_comments --to finalize  --condition no_commits
```

## Failure modes

- Hook fails on the chore commit → don't `--no-verify`. Show it, leave the edits staged, route to finalize with the state recorded.
- Push rejected → show it, don't force, record `pushed=false`.

## Notes

- **Only lines this branch added or changed.** A stale comment two functions up is not this PR's problem.
- **The rules are in one place.** `lib/code-hygiene.md`. This node applies decisions analyze made against it and doesn't re-litigate.
