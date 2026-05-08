# Node: terminal

Sink node. No work, no outgoing edges. Reached only via `summarize`.

## Inputs

None — by the time the walker arrives here, the skill is already created (or cancelled), and `summarize` has printed the hand-off message.

## Steps

None. This node is a pure terminator. The walker stops here.

## Outputs

None.

## Outgoing edges

None — terminal nodes have no outgoing edges. The walker enforces this:
attempting to transition out of a `shape=doublecircle` node raises an error.

## Failure modes

If the walker arrives here in a state inconsistent with the user's
expectations (e.g., the user thought they were iterating but somehow
landed in terminal), the walker's history (`scripts/walk.sh history`)
reveals the route taken. Re-run `/skill-creator` from scratch rather
than trying to back up — graphs are unidirectional by design.
