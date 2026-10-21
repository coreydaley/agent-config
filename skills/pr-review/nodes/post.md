# Node: post

Execute the user's chosen posting style against GitHub via `gh`. Always routes to `cleanup-worktree` after, success or fail — the worktree reset is owed regardless.

## Inputs

- `pr_number`, `pr_dir`, `post_style`, `post_floor`, `head_oid` from walker state

```bash
STATE="$PR_DIR/.walk-state.review.json"
PR_NUMBER=$(scripts/walk.sh get --state "$STATE" --key pr_number)
PR_DIR=$(scripts/walk.sh get --state "$STATE" --key pr_dir)
POST_STYLE=$(scripts/walk.sh get --state "$STATE" --key post_style)
POST_FLOOR=$(scripts/walk.sh get --state "$STATE" --key post_floor)
HEAD_OID=$(scripts/walk.sh get --state "$STATE" --key head_oid)
```

## Comment attribution

**Every comment posted by this node must end with `*(via Claude Code)*`** so the user can distinguish AI-authored comments from their own. This applies to top-level review bodies AND each individual inline comment. See the `gh` skill for the full attribution rule.

## Body composition

The top-level body is, in order: the Summary section from `$PR_DIR/REVIEW.md`, the findings at or above `post_floor` (from `ask-post-style`, default Medium, so Low and Nit stay local unless the user lowered the floor), and the What's Well Done section when REVIEW.md has one. For the `inline` style the top-level body is Summary (+ What's Well Done) only — the findings at or above the floor arrive as inline comments instead of a duplicate table. Findings below the floor are never posted in any style. Say in the body how many were held back ("3 Low/Nit findings kept local") so the author knows the review isn't the whole picture.

If posting inline, parse each SR-prefix finding from REVIEW.md's Findings table and convert to a per-line comment:

```
**SR001 (High · Correctness)**: <issue>

**Suggestion**: <suggestion>

*(via Claude Code)*
```

## Style dispatch

### `comment`

Top-level PR comment, no verdict (doesn't gate mergeability):

```bash
gh pr review "$PR_NUMBER" --comment --body "<summary + findings table + what's well done>

*(via Claude Code)*"
```

### `request_changes`

```bash
gh pr review "$PR_NUMBER" --request-changes --body "<summary + findings table + what's well done>

*(via Claude Code)*"
```

### `approve`

```bash
gh pr review "$PR_NUMBER" --approve --body "<summary + findings table + what's well done>

*(via Claude Code)*"
```

### `inline`

Inline comments anchored to each File:Line, plus a top-level summary body. Build the payload as a JSON file and post it with `--input` — do **not** compose the comments array with repeated `--field "comments[][...]"` flags, which don't reliably group fields into array elements and scramble multi-comment reviews. Construct the JSON with `jq` (or the Write tool), never by hand-interpolating finding text into a JSON string — bodies contain backticks, quotes, and newlines that must be escaped properly.

Payload shape (`$PR_DIR/review-payload.json`):

```json
{
  "commit_id": "<head_oid>",
  "event": "COMMENT",
  "body": "<summary + what's well done>\n\n*(via Claude Code)*",
  "comments": [
    {
      "path": "path/to/file.go",
      "line": 42,
      "side": "RIGHT",
      "body": "**SR001 (High · Correctness)**: <issue>\n\n**Suggestion**: <suggestion>\n\n*(via Claude Code)*"
    },
    {
      "path": "path/to/file.go",
      "start_line": 42,
      "start_side": "RIGHT",
      "line": 55,
      "side": "RIGHT",
      "body": "<range finding — start_line/line span the range>"
    }
  ]
}
```

Post it:

```bash
gh api "repos/{owner}/{repo}/pulls/$PR_NUMBER/reviews" \
  --method POST \
  --input "$PR_DIR/review-payload.json"
```

`{owner}` and `{repo}` are interpolated by `gh api` from the current repo context. The payload file stays in `$PR_DIR` as part of the run's audit trail.

## Steps

1. Read `$PR_DIR/REVIEW.md`, extract the Summary, the findings at or above `$POST_FLOOR`, and What's Well Done if present.
2. Append the attribution suffix `*(via Claude Code)*` to every body.
3. Dispatch on `$POST_STYLE` per the section above.
4. **On success**, print the URL of the posted review.
5. **On failure**, print the gh error output verbatim. Don't retry automatically.

## Outputs

- A review (and possibly inline comments) posted to GitHub
- `$PR_DIR/review-payload.json` (inline style only)

## Outgoing edges

- → `cleanup-worktree` (always — single outgoing edge, success or fail)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from post --to cleanup_worktree
```

## Failure modes

- `gh pr review --approve` or `--request-changes` fails because the user is the PR author → GitHub allows neither verdict on your own PR (422). Surface that error clearly and route to cleanup.
- `gh api` fails on inline comments because a File:Line falls outside the diff → GitHub rejects the **entire review request** (422) — the reviews POST is atomic, so nothing posts, including the valid comments and the summary body. Surface the error, route to cleanup. Don't try to silently strip the offending comments.
- Network or auth failure → surface verbatim, don't retry, route to cleanup.
