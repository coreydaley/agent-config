# Node: init

Parse arguments, set up the state file, prepare for the discussion.

## Inputs

- `$ARGUMENTS` — optional `--help` / `-h` flag, or a free-text seed
  describing the skill the user wants to build (e.g.
  `/skill-creator a wrapper around the foo CLI`).

## Steps

1. **Help mode:** if `$ARGUMENTS` contains `--help` or `-h`, print the help blurb
   from `SKILL.md` verbatim and stop. Do not initialize state, do not call the
   walker, do not write any files.

2. **Pick a state file location.** Skill-creator produces no per-run report
   tree, so state lives under a temp directory:
   ```bash
   TS=$(date -u +%Y-%m-%dT%H-%M-%S)
   STATE_DIR="${TMPDIR:-/tmp}/.claude-walker/skill-creator"
   mkdir -p "$STATE_DIR"
   STATE="$STATE_DIR/$TS.walk-state.json"
   ```

3. **Initialize the walker.**
   ```bash
   scripts/walk.sh init --state "$STATE"
   ```

4. **Capture the seed prompt** (if `$ARGUMENTS` is non-empty after stripping
   help flags) into walker state:
   ```bash
   scripts/walk.sh set --state "$STATE" --key seed_prompt --value "$ARGUMENTS"
   ```
   This lets `discuss-skill` open with the user's framing instead of starting
   from a cold question.

5. **Resolve the agent-config skills directory** and stash it:
   ```bash
   AGENT_CONFIG="$HOME/Code/github.com/coreydaley/agent-config"
   scripts/walk.sh set --state "$STATE" --key agent_config_dir --value "$AGENT_CONFIG"
   scripts/walk.sh set --state "$STATE" --key skills_dir --value "$AGENT_CONFIG/skills"
   ```

## Outputs

- Walker state file at `$STATE` with `current_node = init`.
- `seed_prompt`, `agent_config_dir`, `skills_dir` in walker `extra`.

## Outgoing edges

Single outgoing edge — no condition needed.

```bash
scripts/walk.sh transition --state "$STATE" --from init --to discuss_skill
```

## Failure modes

- **`agent-config` directory missing:** if `$AGENT_CONFIG` doesn't exist, surface
  the path to the user and stop. Do not guess an alternate location.
- **Walker init fails:** the walker prints the underlying error. Surface it
  unchanged; do not retry silently.
