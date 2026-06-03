# Node: ask-wrap-up

User-input gate. The discussion feels converged — confirm the user wants to
assemble the PRD now, keep working sections, or bail.

## Inputs

- Conversation state; `prd_outline` if persisted

```bash
STATE="$SESSION_DIR/.walk-state.json"
```

## Steps

Offer the three choices in one short message:

```
We've covered the main sections. Want me to:
  1. Draft it      — assemble the PRD and show it to you for review.
  2. Keep going    — there's a section or two you still want to work.
  3. Cancel        — stop here; nothing is written to the wiki.
```

Default conservative when the user is ambiguous: prefer **keep going**
(`user_continue`) over drafting. A thin section is cheap to fix now and annoying
to fix after it's on the wiki.

## Outgoing edges

- **`user_wrap_up`** → `draft`. Assemble the document.
- **`user_continue`** → `discuss`. Back to eliciting.
- **`user_cancel`** → `terminal`. Nothing written.

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
  sense convergence, but don't force it.
- **Nothing is written until `publish`.** Drafting just assembles and renders;
  the wiki isn't touched until the user approves at `ask-publish`.
