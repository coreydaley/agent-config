# Node: init

Resolve the PRD source, fetch its content, create `$AUDIT_DIR` via
`lib/prd-runner.sh init`, initialize walker state. **Until `prd-runner.sh
init` runs, there is no `$AUDIT_DIR` and no staged PRD — every subsequent
node depends on this.**

## Inputs

- `$ARGUMENTS` — the PRD source. Exactly one of:
  - a path to a local markdown file (loose file or vault note), or
  - `--wiki <owner>/<repo>:<PageName>` for a Forgejo wiki page.
- For the `file` case, the file's git repo (if any) drives `<org>/<repo>`;
  a loose/vault file falls back to `prd/<slug>`. For the `--wiki` case,
  `<org>/<repo>` is the wiki's owning repo.

If `$ARGUMENTS` is `--help` or `-h`, SKILL.md handles it before this node.

## Steps

### 1. Run prd-runner.sh init — the structural anchor

This is **not optional**. The script fetches the PRD into
`$AUDIT_DIR/prd-source.md`, resolves `<org>/<repo>`, creates `$AUDIT_DIR`
under `~/Reports/<org>/<repo>/audits/<TS>-prd/`, creates `tooling-raw/`,
and writes `MANIFEST.json` (with `project_cwd = $AUDIT_DIR` so codex is
pointed at the directory holding the PRD copy). Its stdout is the absolute
path of `$AUDIT_DIR`.

```bash
# Local file:
AUDIT_DIR=$(bash ~/.claude/lib/prd-runner.sh init "$ARGUMENTS")
# …or Forgejo wiki:
# AUDIT_DIR=$(bash ~/.claude/lib/prd-runner.sh init --wiki "$OWNER/$REPO:$PAGE")

test -n "$AUDIT_DIR" && test -d "$AUDIT_DIR" \
  || bail "prd-runner.sh init failed — refusing to continue without an AUDIT_DIR"
test -s "$AUDIT_DIR/prd-source.md" \
  || bail "prd-runner.sh staged no PRD content — refusing to continue"
```

The `MANIFEST.json` it writes is the receipt that this node ran. Downstream
nodes (`audit-codex.sh`, `audit-verify.sh`) read it. If absent, those
scripts refuse to run.

### 2. Initialize the walker state file

```bash
STATE="$AUDIT_DIR/.walk-state.json"
scripts/walk.sh init --state "$STATE"
```

### 3. Persist run-scoped variables

Read them from the manifest so later nodes don't re-derive them.

```bash
M="$AUDIT_DIR/MANIFEST.json"
scripts/walk.sh set --state "$STATE" --key audit_dir        --value "$AUDIT_DIR"
scripts/walk.sh set --state "$STATE" --key audit_name       --value "prd"
scripts/walk.sh set --state "$STATE" --key project_cwd      --value "$(jq -r .project_cwd "$M")"
scripts/walk.sh set --state "$STATE" --key source_kind      --value "$(jq -r .source_kind "$M")"
scripts/walk.sh set --state "$STATE" --key source_ref       --value "$(jq -r .source_ref "$M")"
scripts/walk.sh set --state "$STATE" --key prd_title        --value "$(jq -r .prd_title "$M")"
scripts/walk.sh set --state "$STATE" --key companion_kind   --value "$(jq -r .companion_kind "$M")"
scripts/walk.sh set --state "$STATE" --key companion_target --value "$(jq -r .companion_target "$M")"
```

### 4. Print an opening line

Tell the user the resolved source (kind + ref), the PRD title, the resolved
`$AUDIT_DIR`, and that orientation is about to run.

## Outputs

- `$AUDIT_DIR` exists under `~/Reports/<org>/<repo>/audits/<TS>-prd/`
- `$AUDIT_DIR/prd-source.md` holds the fetched PRD (the unit of audit)
- `$AUDIT_DIR/MANIFEST.json` exists with source metadata + companion target
- `$AUDIT_DIR/.walk-state.json` exists with run-scoped variables

## Outgoing edges

- → `orient` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from init --to orient
```

## Failure modes

- No argument / unrecognized source → bail with usage.
- Local file doesn't exist → `prd-runner.sh` bails with the path.
- Wiki page not found, or no Forgejo token in tea config → `prd-runner.sh`
  bails with the API message; surface it. (See the `forgejo` skill for token
  setup.)
- `~/Reports/` not writable → `prd-runner.sh` fails on `mkdir -p`. Bail.
