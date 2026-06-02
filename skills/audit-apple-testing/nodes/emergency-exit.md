# Node: emergency-exit

Apple testing has **no emergency-exit conditions**. This node is retained on the graph only for shape uniformity with the other `/audit-*` skills — the `orient → emergency_exit` edge is never taken by this audit, so the runtime never reaches this node.

## Inputs

None. (Never reached.)

## Steps

None. If this node is somehow entered, write a stub `EMERGENCY.md` documenting that it was reached unexpectedly and stop:

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
cat > "$AUDIT_DIR/EMERGENCY.md" <<EOF
# UNEXPECTED EMERGENCY EXIT — apple-testing — $(date -u +%Y-%m-%dT%H:%M:%SZ)

Reached the emergency_exit node, but audit-apple-testing has no
emergency-exit conditions. This indicates an orchestrator bug.
Re-run the audit; if it recurs, file an issue.
EOF
```

## Outputs

- `$AUDIT_DIR/EMERGENCY.md` (only if this node is somehow reached)

## Outgoing edges

- → `terminal` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from emergency_exit --to terminal
```

## Failure modes

- The node is reached at all → that's the failure. Document and route to terminal.

## Notes

- `audit-verify.sh` short-circuits successfully on `EMERGENCY.md` presence; the audit will be marked complete with no Phase 2+ artifacts, which is the right behavior given the orchestrator detected a bug.
