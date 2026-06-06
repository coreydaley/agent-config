# Node: terminal

Sink. Print a brief confirmation and stop.

## Steps

1. **Print a one-line summary** based on the last transition:
   - From `handoff → terminal`: nothing extra; `handoff` already printed the
     rundown. A simple `Done.` is enough.
   - From `ask-approval → terminal [user_cancel]`: "Cancelled at approval —
     no sub-issues created. PLAN.md left on disk at `<path>`."

2. **Stop.** No transitions, no further work.

## Outputs

- Brief printed confirmation.

## Outgoing edges

None. Terminal is a sink.

## Notes

- **Don't reprint summaries.** `handoff` already printed on the success path.
- **PLAN.md and intent.md stay on disk** even on cancel. The user can use
  them manually, or delete the session folder.
- **Don't create issues, don't comment, don't push.** On the cancel path,
  this skill leaves Forgejo untouched; on the success path, `create-issues`
  already did the mutations and `handoff` reported them.
