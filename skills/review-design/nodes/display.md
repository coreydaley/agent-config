# Node: display

Put the report in front of the user as the final message of the turn, then stop. The report is the deliverable, and text followed by a tool call in the same turn is not reliably rendered. See `lib/pr-discipline.md` § Show the Artifact Before Any Question Dialog.

## Inputs

- `session_dir`, `grounded`, `prior_review` from walker state
- `$SESSION_DIR/REVIEW.md`

```bash
STATE="$SESSION_DIR/.walk-state.review-design.json"
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
```

## Steps

1. **Record the transition to `terminal` first.** Terminal does no work, so nothing is lost by closing the walk before the report is printed, and it means no tool call follows the report.

   ```bash
   scripts/walk.sh transition --state "$STATE" --from display --to terminal
   ```

2. **Print `REVIEW.md` inline**, the whole file as markdown.

3. **Name the hand-off** in one or two plain-text lines under the report, matched to the verdict:
   - Build or Build with changes: "Ready for `/pr-plan`, which reads the design as a source."
   - Rework: "Revise the design, carry accepted and deferred items into its Accepted Risks and Follow-ups sections, and re-run. Prior run comparison is automatic under the same slug."
   - Don't build: repeat the one sentence from the verdict that says why.
   - Any verdict, when Out of altitude is non-empty: "Presentation items are listed under Out of altitude. This run did not write into the design."
   Ungrounded: add "Re-run with `--repo` to verify the mechanism claims."

4. **End the turn.** No `AskUserQuestion`, no further tool call. If the user wants to discuss findings, that is a normal conversation, not a node.

## Outputs

- The report is in the conversation

## Outgoing edges

- → `terminal` (always, single outgoing edge, recorded in step 1)

## Notes

- **Report first, path and hand-offs after.** People skim. A path first sends them to a file instead of reading what is in front of them.
- **Don't summarize the report.** The verdict paragraph is already the summary. Print the file.
