# Node: emergency-exit

**Design has no emergency-exit conditions.** This node exists in the graph for topological uniformity across all `/audit-*` skills, but the `orient → emergency_exit` edge is never taken from `audit-design`. The node is unreachable in practice.

If you somehow arrive here (graph bug, manual state edit), write a minimal placeholder `EMERGENCY.md` noting the unexpected entry and transition to `terminal`.

## Inputs

- `$AUDIT_DIR` from walker state

## Steps

### 1. Note the unexpected entry

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
cat > "$AUDIT_DIR/EMERGENCY.md" <<EOF
# EMERGENCY EXIT — design — $(date -u +%Y-%m-%dT%H:%M:%SZ)

## Trigger

This node is unreachable under normal walks of audit-design. Arrival here
indicates a graph or state-machine bug, not a real emergency condition.

The design audit has no live-credential / runtime-blocker class of
finding that justifies halting before Phase 2. If you intended to run a
security audit, use /audit-apple-security or /audit-web-security.

## Required actions

1. Investigate why orient -> emergency_exit was taken; the design
   audit's orient node should always emit "proceed".
2. Re-run /audit-design once the underlying bug is resolved.
EOF
```

### 2. Transition to terminal

## Outputs

- `$AUDIT_DIR/EMERGENCY.md` written (placeholder only)

## Outgoing edges

- → `terminal` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from emergency_exit --to terminal
```

## Failure modes

- N/A — this is the bug-recovery placeholder itself.

## Notes

- `audit-verify.sh` short-circuits on `EMERGENCY.md` presence; the audit reports as "emergency-exited" rather than incomplete.
