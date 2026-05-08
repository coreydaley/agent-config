# Node: ask-approval

The plan is on screen. Ask the user to approve, discuss, or cancel.

## Inputs

- `match_count` from walker state — to decide which approval-with-matches branch to take

```bash
STATE="$SESSION_DIR/.walk-state.json"
MATCH_COUNT=$(scripts/walk.sh get --state "$STATE" --key match_count)
```

## Steps

Use `AskUserQuestion`:

> 1. **Approve & post** — create the milestone and issues as proposed
> 2. **Discuss / edit first** — open conversation; iterate until ready
> 3. **Cancel** — don't post anything

For "Approve & post", the route depends on whether matches exist:

- If `match_count > 0` → route via `user_approve_with_matches` to `ask-per-match-decisions` (the user still needs to decide what to do with each match before any creation happens).
- If `match_count == 0` → route via `user_approve_no_matches` directly to `create-milestone`.

Persist:

```bash
scripts/walk.sh set --state "$STATE" --key approval_choice --value "<approve|discuss|cancel>"
```

## Outgoing edges

- **`user_approve_with_matches`** → `ask-per-match-decisions`. Approve, but matches need triage first.
- **`user_approve_no_matches`** → `create-milestone`. Approve, no matches to handle.
- **`user_discuss`** → `discuss-plan`. Iterate before deciding.
- **`user_cancel`** → `terminal`. Don't create anything.

Record exactly one:

```bash
# Approve with matches:
scripts/walk.sh transition --state "$STATE" --from ask_approval --to ask_per_match_decisions --condition user_approve_with_matches

# Approve, no matches:
scripts/walk.sh transition --state "$STATE" --from ask_approval --to create_milestone --condition user_approve_no_matches

# Discuss:
scripts/walk.sh transition --state "$STATE" --from ask_approval --to discuss_plan --condition user_discuss

# Cancel:
scripts/walk.sh transition --state "$STATE" --from ask_approval --to terminal --condition user_cancel
```

## Notes

- **Default to "Discuss / edit first" when ambiguous.** Creating Linear issues is recoverable but disruptive — N issues land on the team's board.
- **The choice is the gate.** No "are you sure?" follow-up.
