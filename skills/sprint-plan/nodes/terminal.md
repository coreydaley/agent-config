# Node: terminal

Sink. Print a brief confirmation and stop.

## Steps

1. **Print a one-line summary** based on the last transition:
   - From `register → terminal`: nothing extra; `register` already printed the rundown. Simple `Done.` is enough.
   - From `dry-exit → terminal`: "Dry run complete. See preview above."
   - From `ask-spike → terminal [user_cancel]`: "Cancelled at spike prompt — SPRINT.md left as-is at `<path>`, not registered."
   - From `ask-approval → terminal [user_cancel]`: "Cancelled at approval — SPRINT.md left as-is at `<path>`, not registered."

2. **Stop.** No transitions, no further work.

## Outputs

- Brief printed confirmation.

## Outgoing edges

None. Terminal is a sink.

## Notes

- **Don't reprint summaries.** `register` (and `dry-exit`) already printed.
- **SPRINT.md and intent.md stay on disk** even on cancel. The user can use them manually if they want, register later via `/sprints --add`, or delete the session folder.
- **Don't merge, don't push, don't comment.** This skill produces planning artifacts only.
