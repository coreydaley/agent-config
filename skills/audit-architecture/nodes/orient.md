# Node: orient

Phase 1 of the framework. **Architecture has no Phase 1 tooling** — it's a pure-LLM audit. This node is effectively a no-op: it stamps `STATUS.md` to record that no automated tooling ran, performs a brief survey for the orchestrator's situational awareness, and transitions straight to `independent_reviews`. There are also no emergency-exit conditions; the `emergency` edge exists for graph uniformity across the audit suite but is never taken.

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only)

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
```

## Steps

### 1. Record the no-tooling state

```bash
cat > "$AUDIT_DIR/tooling-raw/STATUS.md" <<EOF
# Tooling Status — architecture

Architecture is a pure-LLM audit. No automated tooling runs in Phase 1.
This directory exists for layout uniformity with other /audit-* skills;
Phase 2 reviewers (Claude + Codex) work directly from source.
EOF
```

### 2. Survey

In conversational text (not a persisted file), note:

- Resolved scope (`$PROJECT_CWD`) and top-level layout
- Whether this looks like an agent-config repo (presence of `commands/`,
  `skills/`, `agents/`, `prompts/`, `scripts/`) vs. a general codebase
- Dependency direction or import hotspots where visible from a quick scan
- Any obvious framework / build system markers (`Package.swift`,
  `pyproject.toml`, `go.mod`, `package.json`, `Makefile`)

**Read at least 5 representative files before generalizing any pattern**
— do not generalize from top-level directory structure alone. This is for
the orchestrator's situational awareness, not a persisted artifact.

### 3. Persist run-scoped state

```bash
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "0"
```

## Outputs

- `$AUDIT_DIR/tooling-raw/STATUS.md` documents the no-tooling state
- Walker state has `emergency_exit=0`

## Outgoing edges

- **`proceed`** → `independent_reviews`. Always taken for architecture.
- **`emergency`** → `emergency_exit`. **Never taken for architecture.**
  Architecture has no emergency-exit conditions; this edge exists only
  for structural uniformity with the canonical audit graph.

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- `$AUDIT_DIR/tooling-raw/` not writable → orchestrator bug; bail. `init` should have created it.
