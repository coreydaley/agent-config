# Node: ask-replies

Interpret the user's reply to the drafted thread replies. No `AskUserQuestion`.

## Inputs

- The user's reply

```bash
STATE="$PLAN_DIR/.walk-state.fix.json"
```

## Steps

1. **Record the deferred transition** `draft_replies → ask_replies`.

2. **Map:**

   | Reply shape | Route |
   |---|---|
   | post, pi, send them, go | `user_post` |
   | a change to any draft ("H002 shorter", "drop the last sentence on H004") | `user_edit`, carrying the change |
   | skip, don't post, I'll reply myself | `user_skip` |

   "Post, but change H002" is `user_edit`. What gets posted is always what was last shown.

3. **Ambiguous** → one-line follow-up, end the turn. Never resolve toward posting.

## Outgoing edges

- **`user_post`** → `post-replies`
- **`user_edit`** → `draft-replies`
- **`user_skip`** → `persist`

```bash
scripts/walk.sh transition --state "$STATE" --from ask_replies --to post_replies  --condition user_post
scripts/walk.sh transition --state "$STATE" --from ask_replies --to draft_replies --condition user_edit
scripts/walk.sh transition --state "$STATE" --from ask_replies --to persist       --condition user_skip
```
