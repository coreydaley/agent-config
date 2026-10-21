# Node: post-replies

Post the approved replies, one per thread. Threads are left open for the reviewer to resolve.

## Inputs

- `pr_number`, `repo`, `fix_dir` from walker state
- `$FIX_DIR/replies.md`, `$FIX_DIR/pr-threads.json`

```bash
STATE="$PLAN_DIR/.walk-state.fix.json"
PR_NUMBER=$(scripts/walk.sh get --state "$STATE" --key pr_number)
ORG_REPO=$(scripts/walk.sh get --state "$STATE" --key repo)
```

## Steps

1. **Inline threads.** Reply to the thread's first comment by database ID:
   ```bash
   gh api "repos/$ORG_REPO/pulls/$PR_NUMBER/comments/<databaseId>/replies" \
     -f body="$(cat <<'EOF'
   <the approved reply text>

   *(via Claude Code)*
   EOF
   )" > /tmp/pr-fix-reply.out 2>&1; EXIT=$?
   ```
   Record each result. A failure on one thread doesn't stop the others.

2. **Top-level review replies** (`HR` and `BR` findings) and the bot summary comment: a PR comment.
   ```bash
   gh pr comment "$PR_NUMBER" --repo "$ORG_REPO" --body-file <file>
   ```

3. **Don't resolve threads.** The reviewer resolves when they're satisfied. If the user explicitly asked to resolve fixed threads in their reply to ask-replies, do it for `fixed` outcomes only, via the `resolveReviewThread` GraphQL mutation, and say which.

4. **Write `$FIX_DIR/replied.json`:** `[{thread_id, comment_id, posted: true|false, error}]`.

## Outputs

- Replies on the PR
- `$FIX_DIR/replied.json`

## Outgoing edges

- → `persist` (always, single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from post_replies --to persist
```

## Failure modes

- A reply 404s (thread deleted) → record, continue.
- Rate limited → record what posted, stop, tell the user which threads remain. Don't retry in a loop.

## Notes

- **Post exactly what was approved.** No last-second wording changes.
- **Never edit a posted reply afterward.** Posted is immutable. A correction is a new reply.
