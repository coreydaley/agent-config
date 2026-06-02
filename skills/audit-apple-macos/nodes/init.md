# Node: init

Resolve scope, create `$AUDIT_DIR` via `lib/audit-runner.sh init`, initialize walker state. **Until `audit-runner.sh init` runs, there is no `$AUDIT_DIR` — every subsequent node depends on this.**

## Inputs

- `$ARGUMENTS` — optional scope path. If empty, scope is the current working directory. If provided, must be a path that exists on disk.
- Current git remote (`upstream` if configured, else `origin`). Drives the `<org>/<repo>` portion of `$AUDIT_DIR`. Falls back to `local/<basename>` if no remote.

## Steps

### 1. Parse arguments

```bash
SCOPE="${ARGUMENTS:-$(pwd)}"
if [ ! -d "$SCOPE" ]; then
  bail "audit-apple-macos: scope path does not exist: $SCOPE"
fi
```

If `$ARGUMENTS` is `--help` or `-h`, SKILL.md handles it before this node runs.

### 2. Run audit-runner.sh init — the structural anchor

This is **not optional**. The script resolves `$AUDIT_DIR`, creates it under `~/Reports/<org>/<repo>/audits/<TS>-apple-macos/`, creates `tooling-raw/`, and writes `MANIFEST.json`. Its stdout is the absolute path of `$AUDIT_DIR`.

```bash
AUDIT_DIR=$(bash ~/.claude/lib/audit-runner.sh init apple-macos "$SCOPE")
test -n "$AUDIT_DIR" && test -d "$AUDIT_DIR" \
  || bail "audit-runner.sh init failed — refusing to continue without an AUDIT_DIR"
```

The `MANIFEST.json` written by `audit-runner.sh` is the receipt that this node ran. Downstream nodes (`audit-codex.sh`, `audit-verify.sh`) read it. If the file is absent, those scripts refuse to run.

### 3. Initialize the walker state file

`$AUDIT_DIR` is also where the walker state lives, so a single audit run's full record (manifest + tooling-raw + intermediate reviews + REPORT.md + walker state) sits under one directory.

```bash
STATE="$AUDIT_DIR/.walk-state.json"
scripts/walk.sh init --state "$STATE"
```

### 4. Persist run-scoped variables

```bash
scripts/walk.sh set --state "$STATE" --key audit_dir    --value "$AUDIT_DIR"
scripts/walk.sh set --state "$STATE" --key audit_name   --value "apple-macos"
scripts/walk.sh set --state "$STATE" --key project_cwd  --value "$(jq -r .project_cwd "$AUDIT_DIR/MANIFEST.json")"
scripts/walk.sh set --state "$STATE" --key scope        --value "$SCOPE"
```

Subsequent nodes read these via `scripts/walk.sh get` rather than re-deriving them.

### 5. Print an opening line

Tell the user the scope, the resolved `$AUDIT_DIR`, and that Phase 1 is about to run.

## Outputs

- `$AUDIT_DIR` exists under `~/Reports/<org>/<repo>/audits/<TS>-apple-macos/`
- `$AUDIT_DIR/MANIFEST.json` exists with `audit_name`, `scope`, `project_cwd`, `started_at`
- `$AUDIT_DIR/tooling-raw/` exists (empty for now)
- `$AUDIT_DIR/.walk-state.json` exists with run-scoped variables in `extra`

## Outgoing edges

- → `orient` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from init --to orient
```

## Failure modes

- Scope path doesn't exist → bail with the path.
- `audit-runner.sh init` returns non-zero or empty stdout → bail. Without `$AUDIT_DIR` everything downstream is unwritable; there is no degraded fallback.
- `~/Reports/` not writable → `audit-runner.sh` fails on `mkdir -p`. Bail with the system error.
