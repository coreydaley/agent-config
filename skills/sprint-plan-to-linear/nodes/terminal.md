# Node: terminal

Sink. Print a brief confirmation and stop.

## Steps

1. **Print a one-line summary** based on the last transition:
   - From `finalize → terminal`: nothing extra needed — `finalize` already printed the per-PR rundown. A simple `Done.` is enough.
   - From `ask-milestone-name → terminal [user_cancel]`: "Cancelled at milestone-name prompt — Linear untouched."
   - From `ask-rerun-mode → terminal [user_cancel]`: "Cancelled at re-run prompt — Linear untouched."
   - From `ask-approval → terminal [user_cancel]`: "Cancelled at approval — Linear untouched."
   - From `ask-per-match-decisions → terminal [user_cancel]`: "Cancelled mid match-walk — Linear untouched."

2. **Stop.** No transitions, no further work.

## Outputs

- Brief printed confirmation.

## Outgoing edges

None. Terminal is a sink.

## Notes

- **Don't reprint LINEAR.md.** `finalize` already pointed at the path.
- **Don't suggest re-running** unless something failed.
- **Linear is untouched** on every cancel route. The skill never makes partial mutations.
