# Node: emergency-exit

**Not reachable in this audit.** App Store Review has no emergency-exit condition — App Review rejection is a sprint blocker (surfaced via the Submission Blocker tier in REPORT.md), not a "now" event. The node exists for graph uniformity with the other `/audit-*` skills; the `orient → emergency_exit` edge is never taken here.

If this node is ever reached (orchestrator bug), write a stub `EMERGENCY.md` noting the unexpected transition and halt.

## Inputs

- `$AUDIT_DIR` from walker state

## Steps

### 1. Write a stub EMERGENCY.md

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
cat > "$AUDIT_DIR/EMERGENCY.md" <<EOF
# UNEXPECTED EMERGENCY EXIT — apple-app-store-review — $(date -u +%Y-%m-%dT%H:%M:%SZ)

This audit has no emergency-exit conditions defined, but the walker
transitioned here anyway. This indicates an orchestrator bug. No
reviewer artifacts were produced for this run.
EOF
```

## Outputs

- `$AUDIT_DIR/EMERGENCY.md` (stub, only if this node is reached in error)

## Outgoing edges

- → `terminal` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from emergency_exit --to terminal
```

## Failure modes

- This node should not be reached in normal operation. Reaching it is itself the failure.
