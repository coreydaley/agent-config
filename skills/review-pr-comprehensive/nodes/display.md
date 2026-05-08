# Node: display

Print REVIEW.md inline so the user reads it now, then transition to `ask-next-action` for the post/discuss/nothing decision.

## Inputs

- `pr_dir` from walker state
- `$PR_DIR/REVIEW.md`

```bash
STATE="$PR_DIR/.walk-state.json"
PR_DIR=$(scripts/walk.sh get --state "$STATE" --key pr_dir)
```

## Steps

1. **Output the full contents of `$PR_DIR/REVIEW.md` as inline text in your response.** Render it as markdown so the user can read it directly in the conversation. **Don't** just reference the file path and ask them to open it.

2. **Append the absolute path on its own line** at the end so the user can copy it directly to a follow-up session (e.g. to hand the findings to `/review-address-feedback`):
   ```
   📄 Saved to: /full/path/to/$PR_DIR/REVIEW.md
   ```
   Use the literal absolute path, not the `$PR_DIR` variable.

## Outputs

- The user has the REVIEW.md inline in this conversation.

## Outgoing edges

- → `ask-next-action` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from display --to ask_next_action
```

## Notes

- **Print the full file, not a summary.** The user is going to be asked what to do next; they need the full context first.
- **The path goes after the content, not before.** People skim — putting the path first makes them tab out to read the file rather than scan the inline content.
