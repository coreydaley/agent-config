# Node: emergency-exit

This audit has no emergency-exit conditions; the `orient` node always takes the `proceed` edge. This node exists as a structural placeholder for graph uniformity across the audit suite. **If reached, it's a bug — fail closed with an explicit error.**

## Inputs

- Walker state: `audit_dir`

## Steps

```bash
bail "audit-architecture: emergency-exit reached, but architecture has no emergency-exit conditions. This is a bug in the orient node's transition logic. Inspect $AUDIT_DIR/.walk-state.json and re-run."
```

## Outputs

None — this node fails closed.

## Outgoing edges

- → `terminal` (only reachable if the bail above is somehow bypassed; never taken in normal operation)

```bash
scripts/walk.sh transition --state "$STATE" --from emergency_exit --to terminal
```

## Failure modes

- Reaching this node at all is the failure mode. Architecture is purely advisory; there is no live-credential or other "halt the audit" trigger.
