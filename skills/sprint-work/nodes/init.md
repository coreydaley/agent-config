# Node: init

Parse arguments and flags, validate flag combinations, init walker state. Handle `--help` inline.

## Inputs

- The user's arguments to the skill: `[<target>] [--review|--retro|--continue|--help]`

## Steps

1. **Detect `--help`.** If present anywhere in args, print the help blurb (verbatim from SKILL.md's "Help text" section) and stop. **Don't proceed to walker init.**

2. **Parse flags:**
   - `--review` → `flag_review=true`
   - `--retro` → `flag_retro=true`
   - `--continue` → `flag_continue=true`
   - Unknown flag → fail loudly with the offending flag.

3. **Validate flag combinations:**
   - `--review` and `--retro` are mutually exclusive — `--review` wins. (Surface the override.)
   - `--continue` only applies to `linear-walk`; ignored elsewhere with a note.

4. **Set up walker state** (per-run, in a temp dir since the artifact is the PR/RETRO.md, not a per-run report):
   ```bash
   STATE_BASE="${TMPDIR:-/tmp}/.claude-walker/sprint-work"
   mkdir -p "$STATE_BASE"
   STATE="$STATE_BASE/$(date +%Y-%m-%dT%H-%M-%S).walk-state.json"
   scripts/walk.sh init --state "$STATE"
   ```

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
- `gh` / `linear` not authenticated → defer detection until `resolve-target` (which actually calls them).
