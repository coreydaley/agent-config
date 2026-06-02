# Node: emergency-exit

**Placeholder node.** Web accessibility audits have no emergency-exit conditions — the `orient` node always takes the `proceed` edge. This node exists only so the canonical state machine stays uniform across all `/audit-*` skills.

If the orchestrator somehow reaches this node, treat it as a bug and bail loudly with a message asking the user to file an issue against `audit-web-accessibility`. Do not write `EMERGENCY.md`.

## Outgoing edges

- → `terminal` (the graph wires this edge, but it should never be traversed in practice)

```bash
scripts/walk.sh transition --state "$STATE" --from emergency_exit --to terminal
```
