# Node: apply-title-body

Apply the approved title/body changes via `gh pr edit`, and resolve any approved review threads via `gh api graphql`. Per-PR, sequential. If anything fails, surface and stop — don't half-apply across PRs.

## Inputs

- `pr_set`, `proposals_path`, `tbt_decisions`, `ambiguous_decisions` from walker state

```bash
STATE="<path>"
PR_SET=$(scripts/walk.sh get --state "$STATE" --key pr_set)
PROPOSALS=$(scripts/walk.sh get --state "$STATE" --key proposals_path)
TBT_DECISIONS=$(scripts/walk.sh get --state "$STATE" --key tbt_decisions)
AMBIGUOUS=$(scripts/walk.sh get --state "$STATE" --key ambiguous_decisions)
HAS_CLEANUP=$(scripts/walk.sh get --state "$STATE" --key has_cleanup)
```

## Steps

For each PR (in `pr_set` order):

### Title and body

```bash
gh pr edit "$PR" --title "$NEW_TITLE" --body "$(cat <<'EOF'
$NEW_BODY
EOF
)"
```

Skip the title or body update if the user said "skip" for that specific item under Pick mode.

### Thread resolution

For each thread the user approved for resolution (likely-resolved-by-code OR user-picked-resolve under ambiguous):

```bash
gh api graphql -f query='
  mutation($id: ID!) {
    resolveReviewThread(input: {threadId: $id}) {
      thread { id isResolved }
    }
  }' -F id="$THREAD_ID"
```

### Failure handling

If any `gh pr edit` or `resolveReviewThread` mutation fails:

- Surface the error verbatim.
- **Stop the loop.** Don't continue with other PRs in the set — the user needs to see the failure and decide.
- Route to `summarize` via `no_cleanup` (skipping the cleanup gate). The summary will reflect what was applied vs failed.

## Outputs

- Updated PRs on GitHub (title, body, resolved threads)
- A list of "what was applied" persisted for `summarize`:
  ```bash
  scripts/walk.sh set --state "$STATE" --key tbt_results --value "<JSON: per-PR what changed>"
  ```

## Outgoing edges

- **`has_cleanup`** → `ask-cleanup`. Cleanup proposals exist (and weren't auto-skipped by `analyze`).
- **`no_cleanup`** → `summarize`. No cleanup proposals (or analyze auto-skipped them).

Record exactly one:

```bash
# Has cleanup — go to Prompt 2:
scripts/walk.sh transition --state "$STATE" --from apply_title_body --to ask_cleanup --condition has_cleanup

# No cleanup — wrap up:
scripts/walk.sh transition --state "$STATE" --from apply_title_body --to summarize --condition no_cleanup
```

## Failure modes

- `gh pr edit` rejects body (size limits) → surface and stop.
- Thread already resolved by someone else → not an error; record as "already resolved" and continue.
- Auth / network failure → stop the loop, route to `summarize` with partial results.
