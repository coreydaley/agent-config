# Node: ask-open

Interpret the user's reply to display's question. No `AskUserQuestion`. The question was asked in plain text and the answer comes in the user's own words.

## Inputs

- The user's reply

```bash
STATE="$PLAN_DIR/.walk-state.build.json"
```

## Steps

1. **Record the deferred transition** `display → ask_open` first.

2. **Map the reply:**

   | Reply shape | Route |
   |---|---|
   | open, push, go, mis, looks good, ship it | `user_open` |
   | any change to the title or body ("drop the Not in this PR section", "call it X") | `user_edit`, carrying the requested change to draft-pr-body |
   | stop, not yet, leave it local, I'll open it | `user_stop` |

   "Open, but change X" is `user_edit`. The change lands, the body re-displays, the next reply opens. What gets pushed is always something the user has seen.

3. **Ambiguous** → one-line plain-text follow-up, end the turn. Never resolve toward pushing.

4. **Persist:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key open_choice --value "<open|stop>"
   scripts/walk.sh set --state "$STATE" --key edit_request --value "<the user's words>"   # user_edit only
   ```

## Outgoing edges

- **`user_open`** → `open-pr`
- **`user_edit`** → `draft-pr-body`
- **`user_stop`** → `finalize`

```bash
scripts/walk.sh transition --state "$STATE" --from ask_open --to open_pr       --condition user_open
scripts/walk.sh transition --state "$STATE" --from ask_open --to draft_pr_body --condition user_edit
scripts/walk.sh transition --state "$STATE" --from ask_open --to finalize      --condition user_stop
```

## Notes

- **Stop is a clean exit.** Commits stay on the branch, PLAN.md says `building`, finalize prints how to open later. Nothing is lost.
