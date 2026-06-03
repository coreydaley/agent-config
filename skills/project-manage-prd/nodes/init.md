# Node: init

Resolve the repo, set up the working folder, initialize walker state.

A PRD's home is a **repository's Forgejo wiki**, so this skill needs a repo. It
resolves `<owner>/<repo>` from the cwd's git remote (prefers `upstream`, falls
back to `origin`).

## Inputs

- Optional `<owner>/<repo>` to override the cwd-derived repo.
- Optional `--from-review <path>` — a **findings doc** to work through in revise
  mode (typically a fresh `audit-prd` `REPORT.md` handed off immediately). It
  seeds the *discussion*; it is **not** the PRD source (the PRD always comes
  live from the wiki in `orient`). Never auto-discovered — only used when
  explicitly passed.

## Steps

1. **Parse args + resolve the repo:**
   ```bash
   ARG="$ARGUMENTS"
   # Optional --from-review <path> (findings to work through; not the PRD source).
   FINDINGS_PATH=$(printf '%s' "$ARG" | sed -n 's/.*--from-review[[:space:]]*\([^[:space:]]*\).*/\1/p')
   ARG=$(printf '%s' "$ARG" | sed 's/--from-review[[:space:]]*[^[:space:]]*//' | xargs)
   if printf '%s' "$ARG" | grep -qE '^[^/]+/[^/]+$'; then
     ORG_REPO="$ARG"
   else
     REMOTE=$(git remote get-url upstream 2>/dev/null || git remote get-url origin 2>/dev/null || echo "")
     ORG_REPO=$(echo "$REMOTE" | sed 's|.*github\.com[:/]||; s|.*mac-mini.example:3000/||; s|\.git$||')
   fi
   ```

   **Bail if `$ORG_REPO` is empty** (cwd has no usable remote and no override
   was given): "No repo resolved — run `/project-manage-prd` inside the project
   checkout, or pass `<owner>/<repo>`. A PRD lives on a repo's Forgejo wiki." Do
   not proceed.

2. **Set up the working folder.** PRD authoring isn't a sprint, so it gets its
   own area under the repo's reports tree:
   ```bash
   SESSION_TS=$(date +%Y-%m-%dT%H-%M-%S)
   SESSION_DIR="$HOME/Reports/$ORG_REPO/prd/$SESSION_TS"
   mkdir -p "$SESSION_DIR"
   ```
   The local `PRD.md` written here is a working draft; the wiki page is the
   durable record.

3. **Initialize the walker state file:**
   ```bash
   STATE="$SESSION_DIR/.walk-state.json"
   scripts/walk.sh init --state "$STATE"
   ```

4. **Persist run-scoped state:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key org_repo      --value "$ORG_REPO"
   scripts/walk.sh set --state "$STATE" --key session_dir   --value "$SESSION_DIR"
   scripts/walk.sh set --state "$STATE" --key session_ts    --value "$SESSION_TS"
   scripts/walk.sh set --state "$STATE" --key findings_path --value "$FINDINGS_PATH"   # may be empty
   ```
   If `$FINDINGS_PATH` is set but the file doesn't exist, warn and continue with
   it empty (the review pass still works; it just won't pre-load findings).

5. **Print a brief opening line** — the resolved repo and that we're about to
   orient. (The real opening message is `kickoff`'s job.)

## Outputs

- `$SESSION_DIR/` exists with `.walk-state.json`
- `org_repo`, `session_dir`, `session_ts` in walker state

## Outgoing edges

- → `orient` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from init --to orient
```

## Failure modes

- No repo resolves and no override → bail (see step 1); a PRD needs a wiki home.
- `tea` / Forgejo not reachable → not fatal here; `orient`'s PRD fetch and
  `publish` handle Forgejo errors. init only needs the repo name + local dir.
