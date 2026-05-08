# Node: replies

Draft, confirm, and post the chosen replies on GitHub. Drafts are always shown to the user before any `gh` call.

## Inputs

- `pr_number`, `pr_repo`, `reply_style`, `mode`, `session_dir` from walker state
- Addressed list from `$SESSION_DIR/addressed.json`
- Mode A only: `$SESSION_DIR/pr-comments.json` and `$SESSION_DIR/pr-threads.json` for thread mapping

```bash
STATE="$SESSION_DIR/.walk-state.json"
PR_NUMBER=$(scripts/walk.sh get --state "$STATE" --key pr_number)
REPLY_STYLE=$(scripts/walk.sh get --state "$STATE" --key reply_style)
MODE=$(scripts/walk.sh get --state "$STATE" --key mode)
```

## Comment attribution

**Every comment posted by this node must end with `*(via Claude Code)*`** so the user can distinguish AI-authored comments from their own. This applies to per-thread replies AND the summary comment. See the `github` skill for the full attribution rule.

## Reply tone

Terse, factual, no IDs, no preamble. Examples:

- *"Switched to a context-aware timeout — the goroutine now exits when the parent ctx cancels."*
- *"Added bounds check; fuzz tests cover the empty and overflow cases."*
- *"Won't fix — this matches the documented behavior in `pkg/foo/README.md`. Happy to discuss if you'd like a different contract."*

No internal review IDs (`R001`, `SR042`, etc.). Describe each fix in its own terms.

## Matching findings to threads

- **Mode A**: each finding already carries `comment_id` and `thread_id`.
- **Mode B**: match on `file + line`. Exact match only. If the file has shifted since the review, do **not** auto-match — show unmatched findings to the user and let them pick a thread manually (or drop the reply).

## Drafting

Build drafts in memory based on `reply_style`:

- `per_thread`: one reply per addressed finding (`fixed`, or `won't-fix` with a meaningful reason).
- `summary`: one top-level comment in changelog form, listing what changed without IDs.
- `both`: per-thread + summary.

Display all drafts to the user before any posting. Let them approve / edit / drop each individually. Only post what the user explicitly approves.

## Posting

### Per-thread reply (preferred for findings tied to a specific comment)

```bash
gh api "repos/{owner}/{repo}/pulls/$PR_NUMBER/comments/$COMMENT_ID/replies" \
  --method POST \
  --field body="<reply text>

*(via Claude Code)*"
```

Capture the resulting comment URL for `ADDRESSED.md`.

### Top-level summary comment

```bash
gh pr comment "$PR_NUMBER" --body "<summary text>

*(via Claude Code)*"
```

## After posting

Track which threads got a reply (for `ask-resolve-threads` to use):

```bash
scripts/walk.sh set --state "$STATE" --key replied_threads_path --value "$SESSION_DIR/replied-threads.json"
# Write the JSON: list of {thread_id, comment_url, finding_id}.
```

If the user dropped every draft (nothing actually got posted), set:
```bash
scripts/walk.sh set --state "$STATE" --key any_posted --value "false"
```

Otherwise:
```bash
scripts/walk.sh set --state "$STATE" --key any_posted --value "true"
```

## Outputs

- Replies and/or summary comment posted to GitHub (when approved)
- `$SESSION_DIR/replied-threads.json` (when applicable)
- `any_posted` flag in walker state

## Outgoing edges

- **`posted`** → `ask-resolve-threads`. At least one reply landed.
- **`no_post`** → `persist`. User dropped all drafts, or matching failed for everything in Mode B.

Record exactly one:

```bash
# Something posted:
scripts/walk.sh transition --state "$STATE" --from replies --to ask_resolve_threads --condition posted

# Nothing posted:
scripts/walk.sh transition --state "$STATE" --from replies --to persist --condition no_post
```

## Failure modes

- `gh` rejects a per-thread reply (thread auto-resolved between load and post, or comment deleted) → surface the error, mark that draft as failed in `replied-threads.json` with the gh stderr verbatim, continue with the rest. If *every* draft fails, route via `no_post`.
- Network or auth failure → surface verbatim, don't retry. If nothing posted, route via `no_post`.
- Mode B with shifted lines → unmatched findings get no reply; user already saw them in the matching step.
