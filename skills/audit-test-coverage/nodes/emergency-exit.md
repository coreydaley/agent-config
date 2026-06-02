# Node: emergency-exit

**Placeholder.** The test-coverage audit has no emergency-exit condition. The `orient` node never takes the `emergency` edge to this node in normal operation; the node exists only because the canonical audit graph is shared across all `/audit-*` skills.

If for any reason the walker reaches this node, write a one-line `EMERGENCY.md` noting the unexpected entry and transition to `terminal`. The walker will exit; `audit-verify.sh` short-circuits to success on `EMERGENCY.md` presence so verify won't fail loudly — but this is an anomaly worth investigating.

## Inputs

- Walker state: `audit_dir`

## Steps

### 1. Write a placeholder EMERGENCY.md

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
cat > "$AUDIT_DIR/EMERGENCY.md" <<EOF
# UNEXPECTED EMERGENCY EXIT — test-coverage — $(date -u +%Y-%m-%dT%H:%M:%SZ)

The test-coverage audit does not define emergency-exit conditions, but
the walker reached the emergency_exit node. This indicates either a
manual transition or a bug. No Phase 2+ artifacts will be produced.

Investigate the walker state in $AUDIT_DIR/.walk-state.json.
EOF
```

### 2. Transition to terminal

```bash
scripts/walk.sh transition --state "$STATE" --from emergency_exit --to terminal
```

## Outputs

- `$AUDIT_DIR/EMERGENCY.md` written (placeholder)

## Outgoing edges

- → `terminal` (always — single outgoing edge)

## Failure modes

- None expected; this node should not normally be reached.

## Notes

- This node is structurally required because the canonical graph shared across all `/audit-*` skills includes the `orient → emergency_exit` edge. `orient` for test-coverage simply never takes that edge.
