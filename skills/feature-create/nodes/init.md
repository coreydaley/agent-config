# Node: init

Resolve the repo, set up the working folder, capture any rough-idea argument,
initialize walker state.

A feature is a **Forgejo issue in the cwd repo**, so this skill needs a repo. It
resolves `<owner>/<repo>` from the cwd's git remote (prefers `upstream`, falls
back to `origin`).

## Inputs

- Optional positional: a rough one-line idea for the feature (`$ARGUMENTS`). The
  feature is shaped interactively regardless; the arg just seeds the kickoff.

## Steps

1. **Capture any rough-idea argument** (everything that isn't `--help`):
   ```bash
   SEED_IDEA="<the positional text, or empty>"
   ```

2. **Resolve the repo:**
   ```bash
   REMOTE=$(git remote get-url upstream 2>/dev/null || git remote get-url origin 2>/dev/null || echo "")
   ORG_REPO=$(echo "$REMOTE" | sed 's|.*github\.com[:/]||; s|.*mac-mini.example:3000/||; s|\.git$||')
   ```

   **Bail if `$ORG_REPO` is empty** (cwd has no usable remote): "No repo
   resolved — run `/feature-create` inside the project checkout. A feature is
   tracked as a Forgejo issue in the repo." Do not proceed.

3. **Set up the working folder.** A feature gets its own area under the repo's
   reports tree:
   ```bash
   SESSION_TS=$(date +%Y-%m-%dT%H-%M-%S)
   SESSION_DIR="$HOME/Reports/$ORG_REPO/features/$SESSION_TS"
   mkdir -p "$SESSION_DIR"
   ```
   The local `FEATURE.md` written here (in `draft`) is an ephemeral working copy
   of the issue body; the **Forgejo issue** is the durable record.

4. **Initialize the walker state file:**
   ```bash
   STATE="$SESSION_DIR/.walk-state.json"
   scripts/walk.sh init --state "$STATE"
   ```

5. **Persist run-scoped state:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key org_repo    --value "$ORG_REPO"
   scripts/walk.sh set --state "$STATE" --key session_dir --value "$SESSION_DIR"
   scripts/walk.sh set --state "$STATE" --key session_ts  --value "$SESSION_TS"
   scripts/walk.sh set --state "$STATE" --key seed_idea    --value "$SEED_IDEA"
   ```

6. **Print a brief opening line** — the resolved repo and that we're about to
   orient. (The real opening message is `kickoff`'s job.)

## Outputs

- `$SESSION_DIR/` exists with `.walk-state.json`
- `org_repo`, `session_dir`, `session_ts`, `seed_idea` in walker state

## Outgoing edges

- → `orient` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from init --to orient
```

## Failure modes

- No repo resolves → bail (step 2); a feature needs a repo to be an issue in.
- `tea` / Forgejo not reachable → not fatal here; `orient`'s label fetch and
  `create-issue` handle Forgejo errors. init only needs the repo + local dir.
