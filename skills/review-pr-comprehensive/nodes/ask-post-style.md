# Node: ask-post-style

User chose "post." Ask which style and treat the choice as the confirmation to execute.

## Inputs

- `$PR_DIR/REVIEW.md` (the content that will be posted)
- `pr_number` from walker state

```bash
STATE="$PR_DIR/.walk-state.json"
PR_NUMBER=$(scripts/walk.sh get --state "$STATE" --key pr_number)
```

## Steps

Use `AskUserQuestion`. Frame as a single decision so the choice itself is the confirm:

> Posting style for PR #<N>:
>
> 1. Comment only — top-level PR comment with the summary, no verdict
> 2. Request changes — post the review and mark as request-changes
> 3. Approve — post the review and approve
> 4. Inline + comment — anchor each finding to its exact File:Line, plus a top-level summary comment
> 5. Cancel — don't post, stop here

Persist the user's choice for the `post` node:

```bash
scripts/walk.sh set --state "$STATE" --key post_style --value "<comment | request_changes | approve | inline>"
```

(Skip the `set` if the user picked Cancel.)

## Outgoing edges

- **`style_chosen`** → `post`. User picked one of options 1-4.
- **`user_cancel`** → `cleanup-worktree`. User picked Cancel (worktree cleanup still owed).

Record exactly one:

```bash
# Style chosen — proceed to post:
scripts/walk.sh transition --state "$STATE" --from ask_post_style --to post --condition style_chosen

# Cancel:
scripts/walk.sh transition --state "$STATE" --from ask_post_style --to cleanup_worktree --condition user_cancel
```

## Notes

- **Default to safer styles when ambiguous.** If the user said "post it" without specifying, prefer "Comment only" over Approve / Request changes — comments don't gate the PR's mergeability.
- **The choice is the confirmation.** One decision, then execute.

## Failure modes

- User aborts mid-question → treat as `user_cancel`.
- User asks for a style that doesn't exist (e.g. "draft review") → the gh CLI doesn't support draft top-level reviews; clarify and re-prompt.
