# Node: emergency-exit

**Performance audits have no emergency-exit conditions.** This node is a structural placeholder so the graph topology stays uniform across every `/audit-*` skill. The `orient → emergency_exit` edge is never taken for apple-performance; orient always emits `proceed`.

## When this node runs

Effectively never. If it does run (the orchestrator took the `emergency` edge by mistake, or a future variant of orient introduces a halt condition), write a minimal `EMERGENCY.md` describing what triggered and transition to `terminal`.

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
cat > "$AUDIT_DIR/EMERGENCY.md" <<EOF
# EMERGENCY EXIT — apple-performance — $(date -u +%Y-%m-%dT%H:%M:%SZ)

This node fired unexpectedly. Performance audits have no defined
emergency-exit conditions. The audit has halted before Phase 2; no
reviewer artifacts will be produced.

If this was reached in error, re-run /audit-apple-performance.
EOF
```

## Outputs

- `$AUDIT_DIR/EMERGENCY.md` written
- No reviewer artifacts produced

## Outgoing edges

- → `terminal` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from emergency_exit --to terminal
```

## Notes

- `audit-verify.sh` handles the case where `EMERGENCY.md` exists — its presence short-circuits the artifact gate.
