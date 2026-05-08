# Node: apply-comments

Apply approved comment edits via the `Edit` tool — exact-string replacement, one file/edit at a time. Stage the changed files. If commits are also approved, they roll into the cleanup commit; otherwise a single `chore: tighten comments` commit captures the changes.

## Inputs

- `proposals_path`, `cleanup_decisions`, `do_commits` from walker state
- The comment-cleanup proposals from `analyze`

```bash
STATE="<path>"
PROPOSALS=$(scripts/walk.sh get --state "$STATE" --key proposals_path)
CLEANUP_DECISIONS=$(scripts/walk.sh get --state "$STATE" --key cleanup_decisions)
DO_COMMITS=$(scripts/walk.sh get --state "$STATE" --key do_commits)
```

## Steps

1. **For each approved comment edit:**
   - Use the `Edit` tool with the exact `old_string` and `new_string` from the proposal.
   - One file, one edit at a time. Never bulk ranges, never `sed`.
   - If a proposal type is **strip entirely**, the new_string is empty (or the line is fully removed — match the proposal's specifics).

2. **Stage the changed files:**
   ```bash
   git add <list-of-files-touched>
   ```

3. **Decide on a wrapper commit.** If `do_commits=true`, the staged changes will roll into the next `apply-commits` reset+recommit cycle — **don't commit here**. The reset would discard a separate commit anyway. If `do_commits=false`, create a single `chore: tighten comments` commit:

   ```bash
   git commit -m "$(cat <<'EOF'
   chore(<scope>): tighten review-added comments
   
   Co-authored-by: Claude <noreply@anthropic.com>
   EOF
   )"
   ```

   Skip the `Addresses <LINEAR-ID>` trailer here — comment tightening isn't an issue resolution.

4. **Persist results:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key comment_results --value "<JSON: applied/skipped/failed per edit>"
   ```

## Outputs

- Edited comment lines in the working tree
- Either staged changes (when `do_commits=true`) or a single tighten-comments commit (when `do_commits=false`)
- `comment_results` in walker state

## Outgoing edges

- **`do_commits`** → `preflight-cleanup`. Commits are approved; head into history rewrite.
- **`no_commits`** → `summarize`. Comments were the only cleanup; we're done.

Record exactly one:

```bash
# Continue to commit cleanup:
scripts/walk.sh transition --state "$STATE" --from apply_comments --to preflight_cleanup --condition do_commits

# Comments-only — wrap up:
scripts/walk.sh transition --state "$STATE" --from apply_comments --to summarize --condition no_commits
```

## Failure modes

- An `Edit` fails because the `old_string` no longer matches (someone else changed the file in the meantime, or the comment was already edited) → record the failure for that specific edit, continue with the rest.
- A staging command fails → surface error, stop, route to `summarize` with partial results.

## Notes

- **Never edit business logic.** Comment-only edits, period. If the analysis flagged something that isn't a comment, drop it.
- **Never touch lines outside `git diff <base>..HEAD`.** Existing comments are out of scope.
- **Single-edit-at-a-time** is by design — review hygiene says batch operations against unverified files are dangerous.
