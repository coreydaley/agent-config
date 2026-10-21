# Node: ask-triage

Interpret the user's reply to the triage table. No `AskUserQuestion`.

## Inputs

- The user's reply
- `triage_path` from walker state

```bash
STATE="$PLAN_DIR/.walk-state.fix.json"
```

## Steps

1. **Record the deferred transition** `display → ask_triage`.

2. **Map the reply:**

   | Reply shape | Route |
   |---|---|
   | approve, go, mis, looks right, fix those | `user_approve` |
   | any change to an action or class, an answer to a Discuss item, "drop X", "also fix Y" | `user_adjust`, carrying the exact adjustments to triage |
   | stop, later, not now | `user_stop` |

   "Approve, but SR005 is a defer" is `user_adjust`. Triage applies it, display re-shows, the next reply approves what's on screen.

   Approve with Discuss items still open → treat as `user_adjust` and ask for the answers in one line. Nothing marked `discuss` reaches apply.

3. **On approve:** flip TRIAGE.md's `Status: Proposed` to `Status: Approved` and stamp the time. This is what resume mode checks for.

4. **Ambiguous** → one-line plain-text follow-up, end the turn. Never resolve toward approve.

## Outgoing edges

- **`user_approve`** → `apply`
- **`user_adjust`** → `triage`
- **`user_stop`** → `finalize`

```bash
scripts/walk.sh transition --state "$STATE" --from ask_triage --to apply    --condition user_approve
scripts/walk.sh transition --state "$STATE" --from ask_triage --to triage   --condition user_adjust
scripts/walk.sh transition --state "$STATE" --from ask_triage --to finalize --condition user_stop
```

## Notes

- **The approved table is the fix list.** apply does exactly those `fix` rows and nothing else. A fix that turns out to need more than the row says goes back to the user, not into the diff.
