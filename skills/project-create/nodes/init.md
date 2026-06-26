# Node: init

Initialize walker state. No GitHub calls yet — everything is local until `create`.

## Steps

```bash
SESSION_TS=$(date +%Y-%m-%dT%H-%M-%S)
SESSION_DIR="$TMPDIR/.claude-walker/project-create/$SESSION_TS"
mkdir -p "$SESSION_DIR"
STATE="$SESSION_DIR/.walk-state.json"
scripts/walk.sh init --state "$STATE"
scripts/walk.sh set --state "$STATE" --key session_dir --value "$SESSION_DIR"
scripts/walk.sh set --state "$STATE" --key session_ts  --value "$SESSION_TS"
```

Print a one-line opener: "Let's shape a new project."

## Outgoing edges

- → `discuss` (always)

```bash
scripts/walk.sh transition --state "$STATE" --from init --to discuss
```
