# Node: terminal

Sink node. No work, no outgoing edges. Reached via:

- `handoff → terminal` — normal completion.
- `emergency_exit → terminal` — Phase 1 halted on a live credential.
- `escalate → terminal` — verify failed; user acknowledged.

## Inputs

None.

## Steps

None — the walker reaches terminal, the skill is done.

## Outputs

None.

## Outgoing edges

None. This is a sink (`shape=doublecircle`). The walker refuses any transition out.

## Failure modes

None.
