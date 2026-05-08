# Node: ask-approval

Approve / discuss / cancel. Same gate pattern as the other approval nodes in this suite.

## Inputs

- The plan rendered by `show-plan` (in conversation)

```bash
STATE="<path>"
```

## Steps

Use `AskUserQuestion`:

> 1. **Approve & implement** — start coding
> 2. **Discuss / edit first** — open conversation; iterate before approving
> 3. **Cancel** — stop without coding

Persist:

```bash
scripts/walk.sh set --state "$STATE" --key approval_choice --value "<approve|discuss|cancel>"
```

## Outputs

- `approval_choice` in walker state

## Outgoing edges

- **`user_approve`** → `implement`. Start coding.
- **`user_discuss`** → `discuss-plan`. Iterate.
- **`user_cancel`** → `terminal`. Stop.

Record exactly one:

```bash
# Approve:
scripts/walk.sh transition --state "$STATE" --from ask_approval --to implement --condition user_approve

# Discuss:
scripts/walk.sh transition --state "$STATE" --from ask_approval --to discuss_plan --condition user_discuss

# Cancel:
scripts/walk.sh transition --state "$STATE" --from ask_approval --to terminal --condition user_cancel
```

## Notes

- **Default to "Discuss / edit first" when ambiguous.** Cheap to talk; harder to undo a hasty implementation.
- **The choice is the gate.** No "are you sure?" follow-up.
