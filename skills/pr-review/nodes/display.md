# Node: display

Print REVIEW.md inline so the user reads it now, then close the turn with the next-action question that matches the mode and ownership. The transition to `ask-next-action` is recorded next turn.

## Inputs

- `pr_dir`, `mode`, `ownership` from walker state
- `$PR_DIR/REVIEW.md`

```bash
STATE="$PR_DIR/.walk-state.review.json"
PR_DIR=$(scripts/walk.sh get --state "$STATE" --key pr_dir)
MODE=$(scripts/walk.sh get --state "$STATE" --key mode)
OWNERSHIP=$(scripts/walk.sh get --state "$STATE" --key ownership)
```

## Steps

1. **Output the full contents of `$PR_DIR/REVIEW.md` as inline text in your response.** Render it as markdown so the user can read it directly. Don't just reference the file path.

2. **Append the absolute path on its own line** so it can be handed to `/pr-fix`:
   ```
   📄 Saved to: /full/path/to/REVIEW.md
   ```
   Use the literal absolute path, not the `$PR_DIR` variable.

3. **Close the same message with the next-action question in plain text.** Per `lib/pr-discipline.md` § Show the Artifact Before Any Question Dialog, review content is never followed by an `AskUserQuestion`. The question depends on whose PR it is:

   **Own** (PR or local mode):
   > Next: **fix** (hands this REVIEW.md to `/pr-fix` for triage against the plan), **discuss** the findings first, or **nothing** for now?

   **External** (PR mode):
   > Next: **post** to GitHub (I'll ask the style and the severity floor), **discuss** the findings first, or **nothing** for now?

   Own mode never offers post. We don't post reviews on our own PRs. External mode never offers fix. It isn't our branch.

4. **End your turn immediately after that question. No tool call after outputting the review.** Not the walker transition, not `AskUserQuestion`. Record `display → ask_next_action` at the start of the NEXT turn.

## Outputs

- The user has the REVIEW.md inline in this conversation.

## Outgoing edges

- → `ask-next-action` (always, single outgoing edge, recorded next turn)

```bash
scripts/walk.sh transition --state "$STATE" --from display --to ask_next_action
```

## Notes

- **Print the full file, not a summary.** The user is about to decide what to do with it.
- **The path goes after the content, not before.** People skim. A path first sends them to a file instead of the review in front of them.
