# Node: terminal

Sink. Print a brief confirmation and stop.

## Steps

1. **Print a one-line summary** based on the last transition:
   - From `finalize → terminal`: nothing extra needed — `finalize`
     already printed the per-issue rundown. A simple `Done.` is enough.
   - From `ask-approval → terminal [user_cancel]`: "Cancelled at
     approval — Forgejo untouched."

2. **Stop.** No transitions, no further work.

## Outputs

- Brief printed confirmation.

## Outgoing edges

None. Terminal is a sink.

## Notes

- **Don't reprint FORGEJO.md.** `finalize` already pointed at the path.
- **Don't suggest re-running** unless something failed.
- **Forgejo is untouched** on the cancel route. The skill never makes
  partial mutations before `create-issues`.
