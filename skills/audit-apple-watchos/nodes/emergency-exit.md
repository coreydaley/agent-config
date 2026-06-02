# Node: emergency-exit

This audit has no emergency-exit conditions; the orient node always takes `proceed`. This node exists as a structural placeholder for graph uniformity across the audit suite. If reached, it's a bug — fail closed with an explicit error.

## Inputs

None expected — the `orient → emergency_exit` edge is never taken for apple-watchos.

## Steps

### 1. Fail closed

```bash
bail "audit-apple-watchos: emergency_exit reached but this audit has no emergency-exit conditions. This is an orchestrator or walker bug; investigate before continuing."
```

Do **not** silently write an `EMERGENCY.md` and proceed — the structural invariant is that this node is unreachable for this audit. Surfacing the bug is the correct behavior.

## Outputs

None — this node is unreachable in normal operation.

## Outgoing edges

- → `terminal` (always — single outgoing edge, kept for graph uniformity)

```bash
scripts/walk.sh transition --state "$STATE" --from emergency_exit --to terminal
```

## Failure modes

- This node was reached at all → that's the failure mode. The orient node took the `emergency` edge for an audit that has no emergency conditions. Investigate the walker / orient logic.

## Notes

- Kept for graph parity with other `audit-*` skills so the topology stays uniform (11 nodes, 12 edges). The validator requires every declared node to have an incoming edge; the `orient → emergency_exit` edge satisfies that requirement structurally even though it is never traversed.
