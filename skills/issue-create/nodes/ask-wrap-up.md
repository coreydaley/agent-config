# Node: ask-wrap-up

User-input gate. The body feels covered — confirm the user wants to assemble it
now, keep working, or bail.

## Inputs

- Conversation state; `issue_type`, `issue_outline` if persisted

```bash
STATE="$SESSION_DIR/.walk-state.json"
```

## Steps

Offer the three choices in one short message:

```
That covers the <type>. Want me to:
  1. Draft it    — assemble the issue body and show it to you for review.
  2. Keep going  — there's a detail or two you still want to nail down.
  3. Cancel      — stop here; no issue is created.
```

Default conservative when the user is ambiguous: prefer **keep going**
(`user_continue`) over drafting — for a bug especially, a fuzzy repro is cheap to
sharpen now and useless to chase after filing.

## Outgoing edges

- **`user_wrap_up`** → `draft`. Assemble the body.
- **`user_continue`** → `gather`. Back to eliciting.
- **`user_cancel`** → `terminal`. Nothing created.

Record exactly one:

```bash
scripts/walk.sh transition --state "$STATE" --from ask_wrap_up --to draft    --condition user_wrap_up
# or
scripts/walk.sh transition --state "$STATE" --from ask_wrap_up --to gather   --condition user_continue
# or
scripts/walk.sh transition --state "$STATE" --from ask_wrap_up --to terminal --condition user_cancel
```

## Notes

- **The offer is yours; the call is the user's.** Make the wrap-up offer when you
  sense the template is covered; don't force it.
- **Nothing is filed until `create-issue`.** Drafting and the priority aid both come
  first; GitHub isn't touched until the user approves at `ask-create`.
