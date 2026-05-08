# Node: init

Parse arguments and flags. Handle `--help` inline.

## Inputs

- The user's arguments to the skill: `[flags] <seed prompt or path to SEED.md>`

## Steps

1. **Detect `--help`** anywhere in args. Print the help blurb (verbatim from SKILL.md) and stop. **Don't proceed to walker init.**

2. **Parse flags:**
   - `--auto` / `--full` / `--base` / `--dry` — phase-selection mode (mutually informative, see SKILL.md precedence)
   - `--tier=high|mid` — override every enabled phase's tier
   - Unknown flag → fail loudly with the offending flag.

3. **Resolve the seed.** The remaining argument is the seed prompt — either inline text or a path to a SEED.md (typically produced by `/sprint-seed`). If a path, verify it exists.

4. **Set up paths:**
   ```bash
   REMOTE=$(git remote get-url upstream 2>/dev/null || git remote get-url origin 2>/dev/null || echo "")
   ORG_REPO=$(echo "$REMOTE" | sed 's|.*github\.com[:/]||; s|\.git$||')
   REPORTS_BASE="$HOME/Reports/$ORG_REPO"
   REPORT_TS=$(date +%Y-%m-%dT%H-%M-%S)
   SESSION_DIR="$REPORTS_BASE/sprints/$REPORT_TS"
   mkdir -p "$SESSION_DIR"
   ```

   If the seed is a SEED.md path inside an existing sprint session folder, **reuse that folder** as `$SESSION_DIR` (so SEED.md and SPRINT.md live together). Don't create a new timestamp folder in that case.

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
