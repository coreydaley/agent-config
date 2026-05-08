# Node: terminal

Sink. Print a brief confirmation and stop.

## Steps

1. **Print a one-line summary** based on the last transition:
   - From `summarize → terminal`: nothing extra needed — `summarize` already printed the per-PR rundown. A simple `Done.` is enough.
   - From `confirm-closed → terminal [user_cancel]`: "Cancelled — no changes applied."
   - From `ask-title-body → terminal [user_cancel]`: "Cancelled at title/body prompt — no changes applied."

2. **Stop.** No transitions, no further work.

## Outputs

- Brief printed confirmation.

## Outgoing edges

None. Terminal is a sink.

## Notes

- **Don't merge.** The skill never merges. The user clicks Merge in GitHub.
- **Don't suggest next commands.** `summarize` already pointed at the next step (click Merge, or address warnings).
- **Don't reprint the per-PR summary** — `summarize` already did.
