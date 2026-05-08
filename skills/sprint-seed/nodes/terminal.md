# Node: terminal

Sink. Print a brief confirmation and stop.

## Inputs

- Walker history (for telling the user what happened)
- `session_dir` from walker state

## Steps

1. **Print a one-line summary** based on the last transition:
   - From `handoff → terminal`: usually nothing extra is needed — `handoff` already printed the path, the seed, and the next command. A simple `Done.` is enough.
   - From `discuss → terminal [user_cancel]`: "Cancelled — no SEED.md written."
   - From `ask-wrap-up → terminal [user_cancel]`: "Cancelled at wrap-up — no SEED.md written."

2. **Stop.** No transitions, no further work.

## Outputs

- Brief printed confirmation.

## Outgoing edges

None. Terminal is a sink.

## Notes

- **Don't reprint SEED.md.** `handoff` already showed it.
- **Don't suggest re-running** unless the user asks.
