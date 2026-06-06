# Node: ask-wrap-up

User-input gate. The discussion feels converged — confirm the user wants to
assemble the issue body now, keep working, or bail.

## Inputs

- Conversation state; `feature_outline` if persisted

```bash
STATE="$SESSION_DIR/.walk-state.json"
```

## Steps

Offer the three choices in one short message:

```
That covers the feature. Want me to:
  1. Draft it    — assemble the issue body and show it to you for review.
  2. Keep going  — there's a dimension or two you still want to work.
  3. Cancel      — stop here; no issue is created.
```

Default conservative when the user is ambiguous: prefer **keep going**
(`user_continue`) over drafting. A thin spec is cheap to fix now and annoying to
fix after the issue is filed.

## Outgoing edges

- **`user_wrap_up`** → `draft`. Assemble the body.
- **`user_continue`** → `discuss`. Back to eliciting.
- **`user_cancel`** → `terminal`. Nothing created.

Record exactly one:

```bash
scripts/walk.sh transition --state "$STATE" --from ask_wrap_up --to draft    --condition user_wrap_up
# or
scripts/walk.sh transition --state "$STATE" --from ask_wrap_up --to discuss  --condition user_continue
# or
scripts/walk.sh transition --state "$STATE" --from ask_wrap_up --to terminal --condition user_cancel
```

## Notes

- **The offer is yours; the call is the user's.** Make the wrap-up offer when you
  sense convergence; don't force it.
- **Nothing is filed until `create-issue`.** Drafting just assembles and renders;
  Forgejo isn't touched until the user approves at `ask-create`.
