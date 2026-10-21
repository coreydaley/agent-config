# Node: ask-approval

Interpret the user's reply to display's closing question and route. No `AskUserQuestion`. The question was already asked in plain text and the user answers in their own words.

## Inputs

- The user's reply
- `plan_dir`, `ceremony` from walker state

```bash
STATE="$PLAN_DIR/.walk-state.plan.json"
```

## Steps

1. **Record the deferred transition** `display → ask_approval` first thing this turn.

2. **Reset `display_mode`** to `full` so a later re-display after discussion starts from a clean default (discuss sets `delta` when appropriate):
   ```bash
   scripts/walk.sh set --state "$STATE" --key display_mode --value full
   ```

3. **Map the reply:**

   | Reply shape | Route |
   |---|---|
   | approve, ship it, mis, looks good, go | `user_approve` |
   | any question, pushback, correction, answer to an open question, "rename the branch to X" | `user_discuss` |
   | don't build, not worth it, skip this, no-build | `user_no_build` |
   | "design" / take it to review-design (design-review ceremony) | `user_no_build`, with the reason recorded as "routed to design review" |

   A reply that approves *and* changes something ("approve, but drop the e2e test") is `user_discuss`: make the edit, re-display the delta, and let the next reply approve the plan as it actually reads. Approval applies to what's on screen.

4. **Ambiguous** → ask a one-line plain-text follow-up and end the turn. Never resolve ambiguity toward approve.

5. **Persist the choice** for finalize:
   ```bash
   scripts/walk.sh set --state "$STATE" --key approval_choice --value "<approve|no_build>"
   scripts/walk.sh set --state "$STATE" --key no_build_reason --value "<user's reason, one line>"   # no_build only
   ```

## Outputs

- `approval_choice` (and `no_build_reason`) in walker state

## Outgoing edges

- **`user_approve`** → `finalize`
- **`user_discuss`** → `discuss`
- **`user_no_build`** → `finalize`

Record exactly one:

```bash
scripts/walk.sh transition --state "$STATE" --from ask_approval --to finalize --condition user_approve
scripts/walk.sh transition --state "$STATE" --from ask_approval --to discuss  --condition user_discuss
scripts/walk.sh transition --state "$STATE" --from ask_approval --to finalize --condition user_no_build
```

## Notes

- **Default to discuss.** Talking is cheap. An approved plan that the user didn't quite mean is a wasted build.
- **The reply is the gate.** No "are you sure?" after an approve.
