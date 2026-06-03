# Node: init

Parse `$ARGUMENTS`, detect mode, resolve session paths, initialize walker state.

## Inputs

- The user's arguments to the skill (optional)

Mode detection:

- **Empty** → **Repo mode**. Surveys past sprints in this repo.
- **Anything else** → **Seed mode**. The text is the user's rough idea.

## Steps

1. **Detect mode** from the argument shape. If `$ARGUMENTS` is empty, default to Repo mode. Otherwise, Seed mode.

2. **Repo-mode fallback.** If mode is Repo, check the cwd has a usable git remote AND `~/Reports/<org>/<repo>/` has at least one prior sprint session. If not, downgrade mode to Seed and remember to ask the user what they want to discuss in `kickoff`. Persist `repo_fallback=true` so kickoff knows.

3. **Resolve session paths:**
   ```bash
   REMOTE=$(git remote get-url upstream 2>/dev/null || git remote get-url origin 2>/dev/null || echo "")
   ORG_REPO=$(echo "$REMOTE" | sed 's|.*github\.com[:/]||; s|\.git$||')
   REPORTS_BASE="$HOME/Reports/$ORG_REPO"
   SESSION_TS=$(date +%Y-%m-%dT%H-%M-%S)
   SESSION_DIR="$REPORTS_BASE/sprints/$SESSION_TS"
   mkdir -p "$SESSION_DIR"
   ```

   For Seed mode with no git remote, `ORG_REPO` may be empty. In that case, fall back to `$HOME/Reports/seeds/sprints/` so the SEED.md still has a home. Keep `ORG_REPO` empty (don't set it to `seeds`) — `orient` uses a non-empty `ORG_REPO` as the signal to attempt PRD auto-discovery.

4. **Initialize the walker state file:**
   ```bash
   STATE="$SESSION_DIR/.walk-state.json"
   scripts/walk.sh init --state "$STATE"
   ```

5. **Persist run-scoped state:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key mode           --value "<seed|repo>"
   scripts/walk.sh set --state "$STATE" --key repo_fallback  --value "<true|false>"
   scripts/walk.sh set --state "$STATE" --key arguments      --value "<original $ARGUMENTS>"
   scripts/walk.sh set --state "$STATE" --key org_repo       --value "<owner/repo or empty>"
   scripts/walk.sh set --state "$STATE" --key session_dir    --value "$SESSION_DIR"
   scripts/walk.sh set --state "$STATE" --key session_ts     --value "$SESSION_TS"
   ```

6. **Print a brief opening message** — detected mode, session directory.

## Outputs

- `$SESSION_DIR/` exists
- `$SESSION_DIR/.walk-state.json` exists with run-scoped fields in `extra`

## Outgoing edges

- → `orient` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from init --to orient
```

## Failure modes

- `git remote` lookup fails AND mode is Repo → downgrade to Seed mode (set `repo_fallback=true`); kickoff asks the user what to discuss instead of pulling repo history.
- `git remote` lookup fails AND mode is Seed → also fine. The user is talking through a rough idea; we don't need a repo to do that. Use `$HOME/Reports/seeds/sprints/`.
