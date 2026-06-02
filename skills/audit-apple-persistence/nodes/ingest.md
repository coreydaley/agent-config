# Node: ingest

Invoke `/plane-audit-ingest` against this audit's `$AUDIT_DIR`. Parses
the just-verified `REPORT.md` into Plane-shaped work-item files under
`$AUDIT_DIR/work-items/` plus an `INGEST.md` manifest. Audit-scoped only
— does NOT touch the project work-items pool (promotion is the separate
`/plane-audit-promote` step, run manually).

This node runs **after** `verify` passes, so REPORT.md is guaranteed to
exist and be non-empty. Ingest failures are non-fatal — the audit
artifacts are still good; only the plane-side post-processing failed.
The hand-off message will note the status.

## Inputs

- Walker state: `audit_dir`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Steps

### 1. Honor the opt-out env var

```bash
if [ "${PLANE_INGEST_SKIP:-0}" = "1" ]; then
  scripts/walk.sh set --state "$STATE" --key ingest_status --value "skipped"
  scripts/walk.sh set --state "$STATE" --key ingest_log --value "skipped via PLANE_INGEST_SKIP=1"
  scripts/walk.sh transition --state "$STATE" --from ingest --to handoff
  exit 0
fi
```

### 2. Run plane-audit-ingest

```bash
INGEST_SCRIPT="$HOME/.claude/skills/plane-audit-ingest/scripts/ingest.py"
if [ ! -f "$INGEST_SCRIPT" ]; then
  scripts/walk.sh set --state "$STATE" --key ingest_status --value "unavailable"
  scripts/walk.sh set --state "$STATE" --key ingest_log --value "plane-audit-ingest script not found at $INGEST_SCRIPT"
else
  INGEST_LOG="$AUDIT_DIR/.ingest.log"
  if python3 "$INGEST_SCRIPT" "$AUDIT_DIR" > "$INGEST_LOG" 2>&1; then
    scripts/walk.sh set --state "$STATE" --key ingest_status --value "ok"
  else
    scripts/walk.sh set --state "$STATE" --key ingest_status --value "failed"
  fi
  scripts/walk.sh set --state "$STATE" --key ingest_log --value "$(cat "$INGEST_LOG")"
fi
```

## Outputs

- `$AUDIT_DIR/work-items/*.md` — one per finding (on success)
- `$AUDIT_DIR/INGEST.md` — manifest (on success)
- `$AUDIT_DIR/.ingest.log` — captured stdout/stderr
- Walker state: `ingest_status` ∈ {ok, failed, skipped, unavailable}, `ingest_log`

## Outgoing edges

- → `handoff` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from ingest --to handoff
```

## Failure modes

Non-fatal by design:

- **Parse error / unknown audit-name** → `ingest_status=failed`, log
  captured. Handoff message includes a "Plane ingest failed" note;
  audit is still useful via `/plane-audit-ingest <audit-dir>` rerun
  after the parser is fixed.
- **plane-audit-ingest script missing** → `ingest_status=unavailable`.
  Likely means `make all` wasn't run in agent-config. Same handoff
  note; same fallback.

## Notes

- This node is **the only auto-Plane step**. Promotion into the
  project pool (`/plane-audit-promote`) stays manual on purpose so
  the user can review the audit-scoped work items first.
- The opt-out env var `PLANE_INGEST_SKIP=1` exists for cases where
  the user is iterating on the audit's REPORT.md format and doesn't
  want repeated ingestions polluting the work-items dir.
