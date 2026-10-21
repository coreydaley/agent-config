# Node: display

Show the plan and ask what to do with it, in one final message with no tool call after it. The transition to `ask-approval` is recorded at the start of the next turn.

## Inputs

- `plan_dir`, `display_mode` (optional, set by discuss), `attack_status`, `branch_state` from walker state
- `$PLAN_DIR/PLAN.md`

```bash
STATE="$PLAN_DIR/.walk-state.plan.json"
PLAN_DIR=$(scripts/walk.sh get --state "$STATE" --key plan_dir)
DISPLAY_MODE=$(scripts/walk.sh get --state "$STATE" --key display_mode || echo full)
```

## Steps

1. **Render the plan inline.**
   - `full` (first display, or discuss changed structure): the entire PLAN.md as markdown.
   - `delta` (discuss made small edits): only the sections that changed, each under its heading, followed by "everything else unchanged."

2. **Surface the things the reader would otherwise miss**, as short lines after the plan:
   - Branch is proposed, not created: "Branch `<name>` is proposed. pr-build creates it. Rename here if you want a different one."
   - Attack ran: "Adversarial pass: N challenges, A accepted, R rejected. Details in plan-attack.md." Attack failed: say so.
   - Ceremony is design-review: "This is design-shaped. Recommend /review-design before building."
   - Value is roughly zero: repeat the sentence from the Value section so it can't be skimmed past.

3. **Path line:**
   ```
   📄 ~/Reports/<org>/<repo>/prs/<key>/PLAN.md
   ```
   Literal path, not a variable.

4. **Close with the question in plain text**, matching the ceremony:

   > Next: **approve** (sets the plan to approved, then `/pr-build` executes it), **discuss** to change something, or **don't build** to record a no-build decision?

   For `design-review` ceremony, add: "or **design** to stop here and take it to /review-design."

5. **End the turn.** No `AskUserQuestion`, no walker transition, no other tool call after the plan is printed. Text followed by a tool call in the same turn isn't reliably rendered, and the plan is the deliverable.

## Outputs

- The plan is in the conversation
- `display_mode` reset to `full` is done by ask-approval, not here

## Outgoing edges

- → `ask-approval` (always, single outgoing edge, recorded next turn)

```bash
scripts/walk.sh transition --state "$STATE" --from display --to ask_approval
```

## Notes

- **The plan goes first, the path after.** People skim. A path first sends them to a file instead of reading what's in front of them.
- **Open questions are part of the plan.** Don't extract them into a separate quiz. The user answers them in their reply if they want to.
