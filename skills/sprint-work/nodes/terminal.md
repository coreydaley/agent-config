# Node: terminal

Sink. Print a brief confirmation and stop.

## Steps

1. **Print a one-line summary** based on the last transition:
   - From `summarize → terminal` (normal path): nothing extra needed; `summarize` already printed the rundown. A simple `Done.` is enough.
   - From `render-plan-and-exit → terminal` (`--review`): "Review printed."
   - From `write-retro → terminal` (`--retro`): "Retro saved at `<path>`. Sprint marked complete in ledger."
   - From `verify-merged → terminal [user_cancel]`: "Cancelled — retro not written."
   - From `verify-worktree → terminal [worktree_missing]`: "Stopped — worktree(s) not ready. Re-run after creating them."
   - From `detect-inflight → terminal [user_exit]`: "Exited — see suggested follow-on skill above."
   - From `ask-approval → terminal [user_cancel]`: "Cancelled at approval — no implementation done."
   - From `validate-success → terminal [user_blocked]`: "Stopped to fix before PR. Re-run /sprint-work when ready."

2. **Stop.** No transitions, no further work.

## Outputs

- Brief printed confirmation.

## Outgoing edges

None. Terminal is a sink.

## Notes

- **Don't reprint summaries.** `summarize` (and `render-plan-and-exit` and `write-retro`) already printed what the user needs.
- **Don't suggest next commands** unless they weren't already suggested upstream.
- **Don't merge, don't push, don't undraft.** Per the global git rule and skill's own rules.
