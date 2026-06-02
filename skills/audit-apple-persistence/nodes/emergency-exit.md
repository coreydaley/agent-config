# Node: emergency-exit

**Apple persistence has no emergency-exit trigger.** This node exists only for graph uniformity with the other `/audit-*` skills. The `orient → emergency_exit` edge is never taken in this audit.

If reached (e.g. by a future change that adds a persistence-specific emergency condition), follow the same structural pattern as `/audit-apple-security`:

1. Write `$AUDIT_DIR/EMERGENCY.md` describing the trigger and required actions.
2. Halt before Phase 2 — produce no reviewer artifacts.
3. Transition to `terminal`.

## Inputs

None — this node is currently unreachable in `/audit-apple-persistence`.

## Steps

If somehow reached:

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
cat > "$AUDIT_DIR/EMERGENCY.md" <<EOF
# EMERGENCY EXIT — apple-persistence — $(date -u +%Y-%m-%dT%H:%M:%SZ)

## Trigger

<trigger description — currently no defined trigger exists>

## Required actions

<actions>

Re-run \`/audit-apple-persistence\` once resolved.
EOF
```

## Outputs

- `$AUDIT_DIR/EMERGENCY.md` (only if the node is reached)

## Outgoing edges

- → `terminal` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from emergency_exit --to terminal
```

## Failure modes

- None — node is structurally unreachable in the current audit. If a future change makes it reachable, ensure `audit-verify.sh` short-circuits on `EMERGENCY.md` presence (it already does).

## Notes

- The persistence audit's "always proceed past orient" semantics are encoded in `orient.md` step 2 (`EMERGENCY=0` unconditionally). If you add a real emergency condition, update both `orient.md` and this file together.
