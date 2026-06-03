# Node: init

Parse arguments and flags, validate flag combinations, init walker state. Handle `--help` inline.

## Inputs

- The user's arguments to the skill: `[<target>] [--review|--retro|--continue|--help]`

## Steps

1. **Detect `--help`.** If present anywhere in args, print the help blurb (verbatim from SKILL.md's "Help text" section) and stop. **Don't proceed to walker init.**

2. **Parse flags:**
   - `--review` → `flag_review=true`
   - `--retro` → `flag_retro=true`
   - `--continue` → accepted but a **no-op** (continue-through is now the default for `forgejo-walk`). Don't error on it.
   - Unknown flag → fail loudly with the offending flag.

3. **Validate flag combinations:**
   - `--review` and `--retro` are mutually exclusive — `--review` wins. (Surface the override.)
   - Normal runs are **autonomous**: once the target resolves, the skill works through every issue to completion without approval gates or "keep going?" prompts. It only stops at a genuine wall (unresolvable target, missing bare clone, unresolvable test failure on a single issue) or when there's nothing to do.

4. **Set up walker state.** At init time, `$SESSION_DIR` isn't known yet — it gets resolved by `resolve-target` / `load-context`. So init creates a transient state file under `$TMPDIR`. Once `session_dir` is known and stored, downstream callers can resume from `$SESSION_DIR/.work-state.json` if they have it (durable across reboots and `$TMPDIR` cleanup).

   ```bash
   STATE_BASE="${TMPDIR:-/tmp}/.claude-walker/sprint-work"
   mkdir -p "$STATE_BASE"
   STATE="$STATE_BASE/$(date +%Y-%m-%dT%H-%M-%S).walk-state.json"
   scripts/walk.sh init --state "$STATE"
   ```

   When `resolve-target` / `load-context` resolve `session_dir`, they should additionally **mirror the walker state** to `$SESSION_DIR/.work-state.json` so a `$TMPDIR` cleanup mid-sprint doesn't lose iteration history. The mirror is best-effort: copy on every persist after `session_dir` becomes available, and use it for resume on next-run if the `$TMPDIR` copy is gone.

5. **Persist run-scoped state:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key target_args   --value "<target portion of $ARGUMENTS>"
   scripts/walk.sh set --state "$STATE" --key flag_review   --value "<true|false>"
   scripts/walk.sh set --state "$STATE" --key flag_retro    --value "<true|false>"
   scripts/walk.sh set --state "$STATE" --key flag_continue --value "<true|false>"
   ```

## Outputs

- `$STATE` exists; flag values persisted

## Outgoing edges

- → `resolve-target` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from init --to resolve_target
```

## Failure modes

- Unknown flag → bail before walker init with a clear error.
- `tea` not authenticated (no default login) → defer detection until `resolve-target` (which actually calls it).
