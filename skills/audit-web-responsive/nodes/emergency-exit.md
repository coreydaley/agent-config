# Node: emergency-exit

**Unreachable for web-responsive.** This audit has no emergency-exit condition (no equivalent of a live credential leak). The node is declared in `graph.dot` so every `/audit-*` skill shares the same canonical graph topology, but the `orient → emergency_exit` edge is never taken.

If for some reason the walker reaches this node, treat it as an orchestrator bug:

```bash
bail "audit-web-responsive: emergency_exit reached unexpectedly — no emergency conditions are defined for this audit"
```

## Inputs

None expected.

## Outputs

None.

## Outgoing edges

- → `terminal` (declared for graph consistency only; not exercised)

```bash
scripts/walk.sh transition --state "$STATE" --from emergency_exit --to terminal
```

## Failure modes

- Walker arrives here → bail. Surface as a routing bug in `orient`.
