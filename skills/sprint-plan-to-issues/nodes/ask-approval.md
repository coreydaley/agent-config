# Node: ask-approval

The plan is on screen. Ask the user to approve, discuss, or cancel.

## Inputs

- None beyond the rendered plan from `show-plan`.

```bash
STATE="$SESSION_DIR/.walk-state.json"
```

## Steps

Use `AskUserQuestion`:

> 1. **Approve & create** — create the milestone and issues as proposed
> 2. **Discuss / edit first** — open conversation; iterate until ready
> 3. **Cancel** — don't create anything

Persist:

```bash
scripts/walk.sh set --state "$STATE" --key approval_choice --value "<approve|discuss|cancel>"
```

## Outgoing edges

- **`user_approve`** → `create-issues`. Create the issues as proposed
  (the milestone already exists).
- **`user_discuss`** → `discuss-plan`. Iterate before deciding.
- **`user_cancel`** → `terminal`. Don't create anything.

Record exactly one:

```bash
# Approve:
scripts/walk.sh transition --state "$STATE" --from ask_approval --to create_milestone --condition user_approve

# Discuss:
scripts/walk.sh transition --state "$STATE" --from ask_approval --to discuss_plan --condition user_discuss

# Cancel:
scripts/walk.sh transition --state "$STATE" --from ask_approval --to terminal --condition user_cancel
```

## Notes

- **Default to "Discuss / edit first" when ambiguous.** Creating issues
  is recoverable but disruptive — N issues land in the repo.
- **The choice is the gate.** No "are you sure?" follow-up.
