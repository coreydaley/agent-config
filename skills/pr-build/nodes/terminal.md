# Node: terminal

Sink. The node that routed here already printed the outcome.

## Steps

1. Arriving from `finalize`: nothing further.
2. Arriving from `setup-worktree`, `detect-inflight`, or `verify`: one line stating why the run stopped and that nothing was pushed. verify's `user_blocked` route also appends a PLAN.md Log line before transitioning, so the plan records where the build stopped.

## Outgoing edges

None.
