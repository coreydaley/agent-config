# Node: ask-wrap-up

Offer to move to drafting, keep discussing, or cancel.

## Steps

```
Ready to draft the Overview doc and repo description?
  1. Draft it    — assemble and show everything for review.
  2. Keep going  — more to discuss.
  3. Cancel      — abandon, nothing created.
```

## Outgoing edges

- **`user_wrap_up`** → `draft`
- **`user_continue`** → `discuss`
- **`user_cancel`** → `terminal`

```bash
scripts/walk.sh transition --state "$STATE" --from ask_wrap_up --to draft    --condition user_wrap_up
scripts/walk.sh transition --state "$STATE" --from ask_wrap_up --to discuss  --condition user_continue
scripts/walk.sh transition --state "$STATE" --from ask_wrap_up --to terminal --condition user_cancel
```
