# Node: emergency-exit

**This audit has no emergency-exit conditions; the orient node always takes `proceed`. This node exists as a structural placeholder for graph uniformity across the audit suite. If reached, it's a bug — fail closed with an explicit error.**

## Inputs

None expected. If this node executes, the walker took an edge that should never be taken for this audit.

## Steps

```bash
bail "audit-apple-architecture: emergency_exit reached, but this audit has no emergency-exit conditions. This is a bug in the orient node's transition logic — investigate before re-running."
```

## Outputs

None. The skill aborts.

## Outgoing edges

- → `terminal` (only reachable if a future revision adds emergency conditions; preserved for graph uniformity)

```bash
scripts/walk.sh transition --state "$STATE" --from emergency_exit --to terminal
```

## Failure modes

- Reaching this node IS the failure mode. Bail loudly so the bug is visible.
