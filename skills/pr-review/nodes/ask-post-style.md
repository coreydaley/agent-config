# Node: ask-post-style

External mode. The user chose "post." Ask which style and which severity floor, and treat the answer as the confirmation to execute. This node is reached from `ask-next-action`, a turn after the review was displayed, so `AskUserQuestion` is fine here.

## Inputs

- `$PR_DIR/REVIEW.md` (the content that will be posted)
- `pr_number`, `pr_author` from walker state
- Anything the user already said in their reply to display ("post Medium and above as a comment")

```bash
STATE="$PR_DIR/.walk-state.review.json"
PR_NUMBER=$(scripts/walk.sh get --state "$STATE" --key pr_number)
```

## Steps

1. **Skip what's already answered.** If the reply to display named a style or a floor, take it. Ask only for what's missing.

2. **Style**, via `AskUserQuestion`:

   > Posting style for PR #<N> (by @<author>):
   >
   > 1. Comment only: top-level review comment, no verdict
   > 2. Request changes: the review with a request-changes verdict
   > 3. Approve: the review with an approval
   > 4. Inline + comment: each finding anchored to its File:Line, plus a top-level summary
   > 5. Cancel

3. **Severity floor**, via `AskUserQuestion` (same turn is fine, it's a second question):

   > Post findings at or above:
   >
   > 1. Medium (default. Low and Nit stay local)
   > 2. High
   > 3. Low
   > 4. Everything, including Nits

   Show the counts per level from REVIEW.md next to each option so the user can see what each floor posts. A floor that posts zero findings is allowed (a summary-only comment) but say so.

4. **Persist:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key post_style --value "<comment | request_changes | approve | inline>"
   scripts/walk.sh set --state "$STATE" --key post_floor --value "<Blocker | High | Medium | Low | Nit>"
   ```
   (Skip on Cancel.)

## Outgoing edges

- **`style_chosen`** → `post`.
- **`user_cancel`** → `cleanup-worktree`. Worktree cleanup still owed.

Record exactly one:

```bash
scripts/walk.sh transition --state "$STATE" --from ask_post_style --to post             --condition style_chosen
scripts/walk.sh transition --state "$STATE" --from ask_post_style --to cleanup_worktree --condition user_cancel
```

## Notes

- **Default to the safer style when ambiguous.** "Post it" with nothing else means Comment only at the Medium floor. Comments don't gate mergeability.
- **The floor is about signal.** A teammate's PR with twelve Low/Nit findings posted inline reads as pedantry, and the two Mediums get lost. Medium-and-above is the default for a reason. Lower it deliberately.
- **Approve and Request changes are real verdicts.** They gate the PR. Pick them when that's the intent, not as a posting style.
- **The choice is the confirmation.** One decision, then execute.

## Failure modes

- User aborts mid-question → `user_cancel`.
- User asks for a style that doesn't exist ("draft review") → the gh CLI doesn't support it. Clarify and re-prompt.
