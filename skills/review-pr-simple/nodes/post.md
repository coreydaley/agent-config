# Node: post

Execute the user's chosen posting style against GitHub via `gh`.

## Inputs

- `pr_number`, `pr_dir`, `post_style` from walker state

```bash
STATE="$PR_DIR/.walk-state.json"
PR_NUMBER=$(scripts/walk.sh get --state "$STATE" --key pr_number)
PR_DIR=$(scripts/walk.sh get --state "$STATE" --key pr_dir)
POST_STYLE=$(scripts/walk.sh get --state "$STATE" --key post_style)
```

## Comment attribution

**Every comment posted by this node must end with `*(via Claude Code)*`** so the user can distinguish AI-authored comments from their own. This applies to top-level review bodies AND each individual inline comment. See the `github` skill for the full attribution rule.

## Body composition

Pull the Summary section from `$PR_DIR/REVIEW.md` for the top-level body; that's the right summary scope for a posted review. The full table is for the user; the GitHub body should be the human-readable summary.

If posting inline, parse each finding row from REVIEW.md's Findings table and convert to a per-line comment:

```
**R001 (High · Correctness)**: <issue>

**Suggestion**: <suggestion>

*(via Claude Code)*
```

## Style dispatch

### `comment`

Top-level PR comment, no verdict (doesn't gate mergeability):

```bash
gh pr review "$PR_NUMBER" --comment --body "<summary plus findings table>

*(via Claude Code)*"
```

### `request_changes`

Post the review and mark request-changes:

```bash
gh pr review "$PR_NUMBER" --request-changes --body "<summary plus findings table>

*(via Claude Code)*"
```

### `approve`

Post the review and approve:

```bash
gh pr review "$PR_NUMBER" --approve --body "<summary plus findings table>

*(via Claude Code)*"
```

### `inline`

Inline comments anchored to each File:Line, plus a top-level summary comment. Use the `gh api` reviews endpoint:

```bash
HEAD_OID=$(/usr/bin/jq -r .headRefOid "$PR_DIR/metadata.json")
gh api "repos/{owner}/{repo}/pulls/$PR_NUMBER/reviews" \
  --method POST \
  --field commit_id="$HEAD_OID" \
  --field body="<summary>

*(via Claude Code)*" \
  --field event="COMMENT" \
  --field "comments[][path]"="path/to/file.go" \
  --field "comments[][line]"=42 \
  --field "comments[][side]"="RIGHT" \
  --field "comments[][body]"="**R001 (High · Correctness)**: <issue>

**Suggestion**: <suggestion>

*(via Claude Code)*"
```

For a range finding (`path/to/file.go:42-55`), add `start_line` and `start_side`:

```
--field "comments[][start_line]"=42
--field "comments[][start_side]"="RIGHT"
--field "comments[][line]"=55
--field "comments[][side]"="RIGHT"
```

`{owner}` and `{repo}` are interpolated by `gh api` from the current repo context.

## Steps

1. Read `$PR_DIR/REVIEW.md`, extract the Summary and the Findings table.
2. Append the attribution suffix `*(via Claude Code)*` to every body.
3. Dispatch on `$POST_STYLE` per the section above.
4. **On success**, print the URL of the posted review (the `gh pr review` output, or extract from `gh api` response).
5. **On failure**, print the gh error output verbatim. Don't retry automatically — let the user see what happened and decide.

## Outputs

- A review (and possibly inline comments) posted to GitHub
- No new file outputs

## Outgoing edges

- → `terminal` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from post --to terminal
```

## Failure modes

- `gh pr review --approve` fails because the user is the PR author: GitHub doesn't allow self-approval. Surface that error clearly and route to terminal.
- `gh api` fails on inline comments because a File:Line falls on a deleted line or outside the diff: GitHub will reject those specific comments. Surface the error, route to terminal — don't try to silently strip them.
- Network or auth failure: surface verbatim, don't retry.
