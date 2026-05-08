# Node: ask-wrap-up

Gate the discuss-skill loop. The user decides whether to keep iterating, move on, or bail.

## Inputs

- Walker state keys captured by `discuss-skill` (`skill_name`, `skill_summary`,
  `freedom_level`, `suspected_pattern`, etc.).

## Steps

1. **Print a one-paragraph recap** of what's been captured so far. Keep it
   tight — one sentence each for what the skill does, the trigger phrases,
   suspected pattern, and any open uncertainties. The recap helps the user
   see whether the conversation has converged.

2. **Ask the gate question** via `AskUserQuestion`:

   > Ready to wrap up the discussion and pick a pattern?
   >
   > - **continue** — keep discussing; there's still something fuzzy
   > - **done** — captured enough; move on to pattern selection
   > - **cancel** — stop; don't create the skill

3. **Record exactly one transition** based on the answer (see Outgoing edges).

## Outputs

- No new state keys; this node is a pure gate.

## Outgoing edges

- **`user_continue`** → `discuss_skill`. Loop back for another round.
- **`user_done`** → `decide_pattern`. Conversation has converged.
- **`user_cancel`** → `summarize`. Bail without scaffolding anything.

Record exactly one:

```bash
scripts/walk.sh transition --state "$STATE" --from ask_wrap_up --to discuss_skill   --condition user_continue
# or
scripts/walk.sh transition --state "$STATE" --from ask_wrap_up --to decide_pattern  --condition user_done
# or
scripts/walk.sh transition --state "$STATE" --from ask_wrap_up --to summarize       --condition user_cancel
```

## Failure modes

- **Recap is wrong.** If the user says the recap doesn't match what they
  meant, treat that as `user_continue` and re-enter `discuss-skill` to
  correct course. Do not edit the state file directly.
