# Node: ask-approval

The proposed sub-issue breakdown is on screen. This is the **one** approval
gate. Ask the user to create, discuss, or cancel.

## Inputs

- None beyond the rendered breakdown from `show-plan`.

```bash
STATE="$SESSION_DIR/.walk-state.json"
```

## Steps

Use `AskUserQuestion`:

> 1. **Create the sub-issues** — file each task as a self-assigned issue and
>    link the feature as blocked by each
> 2. **Discuss / edit first** — open conversation; iterate on the breakdown
>    until ready
> 3. **Cancel** — don't create anything

Persist:

```bash
scripts/walk.sh set --state "$STATE" --key approval_choice --value "<approve|discuss|cancel>"
```

## Outputs

- The user's choice in walker state.

## Outgoing edges

- **`user_approve`** → `create-issues`. Create the sub-issues as proposed.
- **`user_discuss`** → `discuss-plan`. Iterate before deciding.
- **`user_cancel`** → `terminal`. Don't create anything; PLAN.md stays on disk.

Record exactly one:

```bash
# Approve:
scripts/walk.sh transition --state "$STATE" --from ask_approval --to create_issues --condition user_approve

# Discuss:
scripts/walk.sh transition --state "$STATE" --from ask_approval --to discuss_plan --condition user_discuss

# Cancel:
scripts/walk.sh transition --state "$STATE" --from ask_approval --to terminal --condition user_cancel
```

## Notes

- **Default to "Discuss / edit first" when ambiguous.** Creating sub-issues
  is recoverable but disruptive — N issues land on the board and link the
  feature.
- **The choice is the gate.** No "are you sure?" follow-up.
- **Cancel doesn't delete PLAN.md.** It stays on disk; the user can use it
  manually or re-run later.
