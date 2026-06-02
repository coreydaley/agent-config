# Node: emergency-exit

**Unreachable for `audit-apple-localization`.** Localization issues are never urgent in a "halt before Phase 2" sense — there is no equivalent of a live-credential leak. The node exists in the graph only for uniformity with the canonical audit state machine.

If the walker ever lands here for this skill, it's a bug: `orient` should always take the `proceed` edge. Bail loudly:

```bash
bail "emergency_exit reached for apple-localization — this should never happen; orient took the wrong edge"
```

## Inputs

None — this node should not be reached.

## Steps

None — bail per above.

## Outputs

None.

## Outgoing edges

- → `terminal` (graph defines it for uniformity, but `bail` exits before transitioning)

## Failure modes

- Reaching this node at all is the failure mode.
