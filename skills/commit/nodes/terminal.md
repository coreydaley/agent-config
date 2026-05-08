# Node: terminal

Sink. Print a brief confirmation and stop.

## Steps

1. **Print a one-line summary** based on the last transition:
   - From `show-result → terminal`: nothing extra needed — `show-result` already printed `git log`. A simple `Done.` is enough.
   - From `build-plan → terminal [no_groups]`: "Nothing to commit." (or the verbatim planner error if the planner exited non-zero).

2. **Stop.** No transitions, no further work.

## Outputs

- Brief printed confirmation.

## Outgoing edges

None. Terminal is a sink.

## Notes

- **Don't push.** This skill never pushes — that's always a separate manual action.
- **Don't suggest next commands.** The user invoked `/commit`; they know what's next.
