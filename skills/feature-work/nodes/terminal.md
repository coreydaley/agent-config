# Node: terminal

Sink. Print a brief confirmation and stop.

## Steps

1. **Print a one-line summary** based on the last transition:
   - From `summarize → terminal` (normal completion): nothing extra needed; `summarize` already printed the rundown + punch list. A simple `Done.` is enough.
   - From `verify-worktree → terminal [worktree_missing]`: "Stopped — feature-branch worktree(s) not ready. Re-run after cloning the missing repo / resolving the `git worktree add` error above."
   - From `detect-inflight → terminal [nothing_to_do]`: "Nothing to do — every sub-issue already has a commit on `<feature/<slug>>`. The branch is ready for you to merge."
   - From `validate-success → terminal [blocked]`: "Stopped at a test failure I couldn't resolve on `<sub-issue>`. See the test output above; fix and re-run /feature-work."

2. **Stop.** No transitions, no further work.

## Outputs

- Brief printed confirmation.

## Outgoing edges

None. Terminal is a sink.

## Notes

- **Don't reprint summaries.** `summarize` already printed what the user needs.
- **Don't suggest next commands** unless they weren't already suggested upstream.
- **No extra git here.** The commits and pushes happened in `commit-push` (or the per-sub-issue loop). Terminal is a pure stop — don't merge, don't re-push, don't close anything.
