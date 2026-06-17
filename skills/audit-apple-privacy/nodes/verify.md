# Node: verify

The hard gate. Run `lib/audit-verify.sh` to check that every required artifact exists, is non-empty, and contains table rows where expected. **The orchestrator cannot honestly claim the audit is done unless this exits 0.**

## Inputs

- `$AUDIT_DIR` from walker state
- All artifacts written by prior nodes

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Steps

### 1. Run audit-verify.sh

```bash
bash ~/.claude/lib/audit-verify.sh "$AUDIT_DIR" 2>&1 | tee "$AUDIT_DIR/.verify.log"
VERIFY_EXIT=${PIPESTATUS[0]}
scripts/walk.sh set --state "$STATE" --key verify_exit --value "$VERIFY_EXIT"
```

The script:

- Confirms `MANIFEST.json` exists (audit-runner ran)
- Requires `claude.md`, `synthesis.md`, `REPORT.md` non-empty
- Warns (without failing) if `devils-advocate.md` is missing — a skipped devil's-advocate pass is allowed
- Confirms `claude.md`, `synthesis.md`, `devils-advocate.md` (where present) contain markdown table rows
- Short-circuits with success if `EMERGENCY.md` is present (emergency-exit path)
- On success, stamps `completed_at` into `MANIFEST.json`

### 2. Capture the verify output for the handoff

The handoff message will include the verify summary verbatim. Persist its full output:

```bash
scripts/walk.sh set --state "$STATE" --key verify_output --value "$(cat "$AUDIT_DIR/.verify.log")"
```

## Outputs

- `$AUDIT_DIR/MANIFEST.json` updated with `completed_at` (on success)
- `$AUDIT_DIR/.verify.log` written
- Walker state has `verify_exit` and `verify_output` set

## Outgoing edges

- **`ok`** → `handoff`. `audit-verify.sh` exited 0.
- **`incomplete`** → `escalate`. Verify reported one or more required artifacts missing or malformed.

```bash
if [ "$VERIFY_EXIT" -eq 0 ]; then
  scripts/walk.sh transition --state "$STATE" --from verify --to handoff --condition ok
else
  scripts/walk.sh transition --state "$STATE" --from verify --to escalate --condition incomplete
fi
```

## Failure modes

- `audit-verify.sh` not found / not executable → bail; the user needs to run `make all` in agent-config.
- `MANIFEST.json` missing → orchestrator skipped `init`; this is a hard bug, not a degraded run. Bail and surface.

## Notes

- **Never bypass this gate.** If verify fails, the answer is to escalate or to re-run the missing phase, NOT to claim the audit is done. The gate is the entire point of the skill restructure.
