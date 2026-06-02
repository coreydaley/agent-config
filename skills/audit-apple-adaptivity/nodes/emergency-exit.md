# Node: emergency-exit

This audit has no emergency-exit conditions; the `orient` node always takes the `proceed` edge. This node exists as a structural placeholder for graph uniformity across the audit suite. **If reached, it's a bug** — fail closed with an explicit error.

## Inputs

None — this node should never be entered.

## Steps

```bash
bail "audit-apple-adaptivity: emergency_exit node was reached, but this audit has no emergency-exit conditions. This is a walker bug — investigate before continuing."
```

## Outputs

None.

## Outgoing edges

- → `terminal` (always — single outgoing edge, present for graph uniformity)

```bash
scripts/walk.sh transition --state "$STATE" --from emergency_exit --to terminal
```

## Failure modes

- Reaching this node at all is the failure mode. The orient node's logic must never set `EMERGENCY=1` for this audit.
