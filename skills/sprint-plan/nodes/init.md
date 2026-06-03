# Node: init

Parse arguments and flags. Handle `--help` inline.

## Inputs

- The user's arguments to the skill: `[flags] <seed prompt | path to SEED.md | path to an audit REPORT.md>`

## Steps

1. **Detect `--help`** anywhere in args. Print the help blurb (verbatim from SKILL.md) and stop. **Don't proceed to walker init.**

2. **Parse flags:**
   - `--auto` / `--full` / `--base` / `--dry` — phase-selection mode (mutually informative, see SKILL.md precedence)
   - `--tier=high|mid` — override every enabled phase's tier
   - Unknown flag → fail loudly with the offending flag.

3. **Resolve the seed.** The remaining argument is the seed source — one of:
   - **Inline text** — use it directly.
   - **A path to a SEED.md** (typically produced by `/sprint-seed`) — verify it exists.
   - **A path to an audit `REPORT.md`** (produced by an `audit-*` skill, under `~/Reports/<org>/<repo>/audits/<TS>-<name>/`) — verify it exists; treat it as the seed. Both SEED.md and audit REPORT.md are **ephemeral local seeds** — there's no Forgejo-hosted seed to fetch; the durable Forgejo object is the milestone this skill creates.

4. **Set up paths.** Two cases — reuse the seed's session folder when applicable, otherwise derive a fresh root that respects the four-root model:

   **Case A: SEED.md is inside an existing sprint session folder** (`<root>/sprints/<TS>/SEED.md`):

   ```bash
   SESSION_DIR=$(dirname "$SEED_PATH")
   REPORTS_BASE=$(dirname "$(dirname "$SESSION_DIR")")    # <root>/
   REPORT_TS=$(basename "$SESSION_DIR")                    # <TS>
   ```

   This honors the seed's chosen scoping root. A SEED.md at `~/Reports/seeds/sprints/<TS>/SEED.md` keeps SPRINT.md under `seeds/`; a SEED.md under `~/Reports/<org>/<repo>/sprints/<TS>/` stays repo-scoped.

   **Case B: inline seed text or a SEED.md path outside any session folder** — fall through to repo-derived defaults, with a `no-repo` fallback when cwd has no usable remote:

   ```bash
   REMOTE=$(git remote get-url upstream 2>/dev/null || git remote get-url origin 2>/dev/null || echo "")
   ORG_REPO=$(echo "$REMOTE" | sed 's|.*github\.com[:/]||; s|\.git$||')
   if [ -z "$ORG_REPO" ]; then
     ORG_REPO="no-repo"      # matches sprint_ledger.get_reports_base() behavior
   fi
   REPORTS_BASE="$HOME/Reports/$ORG_REPO"
   REPORT_TS=$(date +%Y-%m-%dT%H-%M-%S)
   SESSION_DIR="$REPORTS_BASE/sprints/$REPORT_TS"
   mkdir -p "$SESSION_DIR"
   ```

   Never produce a `REPORTS_BASE` with empty `$ORG_REPO` — that lands sessions at `$HOME/Reports/sprints/<TS>/` which collides across users.

5. **Initialize walker state:**
   ```bash
   STATE="$SESSION_DIR/.walk-state.json"
   scripts/walk.sh init --state "$STATE"
   ```

6. **Persist run-scoped state:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key seed_text     --value "<original seed text or SEED.md content>"
   scripts/walk.sh set --state "$STATE" --key seed_path     --value "<path to SEED.md or empty>"
   scripts/walk.sh set --state "$STATE" --key session_dir   --value "$SESSION_DIR"
   # reports_root is <root>/ given session_dir = <root>/sprints/<TS>/. Downstream
   # nodes (register) read this rather than re-deriving via dirname-dirname.
   scripts/walk.sh set --state "$STATE" --key reports_root  --value "$REPORTS_BASE"
   scripts/walk.sh set --state "$STATE" --key report_ts     --value "$REPORT_TS"
   scripts/walk.sh set --state "$STATE" --key flag_auto     --value "<true|false>"
   scripts/walk.sh set --state "$STATE" --key flag_full     --value "<true|false>"
   scripts/walk.sh set --state "$STATE" --key flag_base     --value "<true|false>"
   scripts/walk.sh set --state "$STATE" --key flag_dry      --value "<true|false>"
   scripts/walk.sh set --state "$STATE" --key flag_tier     --value "<high|mid|empty>"
   ```

7. **Identify orch/oppo names.** The orchestrator runs as Claude or Codex. Persist:
   ```bash
   scripts/walk.sh set --state "$STATE" --key orch_name --value "<claude|codex>"
   scripts/walk.sh set --state "$STATE" --key oppo_name --value "<the other>"
   ```

## Outputs

- `$SESSION_DIR/` exists; walker state initialized

## Outgoing edges

- → `orient` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from init --to orient
```

## Failure modes

- Unknown flag → bail with the offending flag echoed.
- SEED.md path doesn't exist → bail with the resolution error.
