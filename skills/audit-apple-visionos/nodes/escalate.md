# Node: escalate

`audit-verify.sh` reported that one or more required artifacts are missing or malformed. Surface the failure to the user, show what's missing, and ask whether to retry, accept the degraded result, or abort.

## Inputs

- `$AUDIT_DIR/.verify.log` (the failed verify output)
- Walker state: `audit_dir`, `verify_output`, `codex_status`, `da_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
VERIFY_OUTPUT=$(scripts/walk.sh get --state "$STATE" --key verify_output)
```

## Steps

### 1. Tell the user what's missing

Print the verify output verbatim. Don't try to silently "fix" the gap by writing a placeholder file — that's the failure mode this whole restructure exists to prevent.

```
⚠️ audit-apple-security verification failed.

<verify_output>

The audit is incomplete. Required artifacts are missing or malformed.
```

### 2. Ask the user

Use `AskUserQuestion` with three options:

1. **Retry the missing phase** — orchestrator goes back to the failed phase and re-runs (write claude.md, re-launch codex, etc.). Implementation: this node does NOT have outgoing back-edges to mid-pipeline nodes; the user choosing "retry" should re-invoke the skill or manually re-run the failed step. Document this in the conversation; do not silently re-walk.
2. **Accept degraded result** — proceed to terminal anyway. The hand-off will be marked **DEGRADED**.
3. **Abort** — proceed to terminal anyway. No hand-off; AUDIT_DIR is left for inspection.

### 3. Record the user's choice

```bash
scripts/walk.sh set --state "$STATE" --key escalate_choice --value "<retry|accept|abort>"
```

## Outputs

- User informed of the verify failure
- `escalate_choice` recorded in walker state

## Outgoing edges

- **`user_acknowledge`** → `terminal` (all three user choices route here; the choice content lives in walker state for inspection)

```bash
scripts/walk.sh transition --state "$STATE" --from escalate --to terminal --condition user_acknowledge
```

## Failure modes

- User unavailable (non-interactive run) → default to `accept`, print the verify output to stdout so the run record shows the degraded state.

## Notes

- This node deliberately doesn't have back-edges to mid-pipeline nodes. The walker pattern keeps state machines clean; retry is an out-of-band re-invocation, not a graph edge. The user is told this explicitly.
