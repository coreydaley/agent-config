# Node: terminal

Sink. Print a brief confirmation and stop.

## Steps

1. **Print a one-line summary** based on the last transition:
   - From `summarize → terminal` (normal path): nothing extra needed; `summarize` already printed the rundown. A simple `Done.` is enough.
   - From `render-plan-and-exit → terminal` (`--review`): "Review printed."
   - From `write-retro → terminal` (`--retro`): "Retro saved at `<path>`. Sprint marked complete in ledger."
   - From `verify-merged → terminal [user_cancel]`: "Cancelled — retro not written."
   - From `verify-worktree → terminal [worktree_missing]`: "Stopped — worktree(s) not ready. Re-run after creating them."
   - From `detect-inflight → terminal [nothing_to_do]`: "Nothing to do — every targeted issue is already closed."
   - From `validate-success → terminal [blocked]`: "Stopped at a test failure I couldn't resolve on `<issue>`. See the test output above; fix and re-run /sprint-work."

2. **Stop.** No transitions, no further work.

## Outputs

- Brief printed confirmation.

## Outgoing edges

None. Terminal is a sink.

## Notes

- **Don't reprint summaries.** `summarize` (and `render-plan-and-exit` and `write-retro`) already printed what the user needs.
- **Don't suggest next commands** unless they weren't already suggested upstream.
- **No extra git here.** The commit and push happened in `commit-push` (or the per-issue loop); terminal is a pure stop. Don't merge, don't re-push.
