# Node: ask-post-style

User chose "post." Ask which style, and treat the choice as the confirmation to execute.

## Inputs

- `$PR_DIR/REVIEW.md` (the content that will be posted)
- `pr_number` from walker state (for the confirmation message)

```bash
STATE="$PR_DIR/.walk-state.json"
PR_NUMBER=$(scripts/walk.sh get --state "$STATE" --key pr_number)
```

## Steps

Use `AskUserQuestion`. Frame it as a single decision so the choice is itself the confirm:

> Posting style for PR #<N>:
>
> 1. Comment only — top-level PR comment with the summary, no verdict
> 2. Request changes — post the review and mark as request-changes
> 3. Approve — post the review and approve
> 4. Inline + comment — anchor each finding to its exact File:Line, plus a top-level summary comment
> 5. Cancel — don't post, stop here

Persist the user's choice for the `post` node to use:

```bash
scripts/walk.sh set --state "$STATE" --key post_style --value "<comment | request_changes | approve | inline>"
```

(Skip the `set` if the user picked Cancel.)

## Outgoing edges

- **`style_chosen`** → `post`. User picked one of options 1–4.
- **`user_cancel`** → `terminal`. User picked Cancel.

Record exactly one:

```bash
# Style chosen — proceed to post:
scripts/walk.sh transition --state "$STATE" --from ask_post_style --to post --condition style_chosen

# Cancel:
scripts/walk.sh transition --state "$STATE" --from ask_post_style --to terminal --condition user_cancel
```

## Notes

- **Default to safer styles when ambiguous.** If the user's intent is unclear (e.g. they asked "post it" without specifying), prefer "Comment only" over "Approve" or "Request changes" — comments don't gate the PR's mergeability.
- **The choice is the confirmation.** Don't add a separate "are you sure?" prompt after this. One decision, then execute.

## Failure modes

- User aborts in the middle: treat as `user_cancel`.
- User asks for a style that doesn't exist (e.g. "draft review"): the `gh` CLI doesn't support draft top-level reviews; clarify and re-prompt.
