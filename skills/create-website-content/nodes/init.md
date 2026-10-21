# Node: init

Parse arguments, detect help mode, and set up the walker state file. The run's
artifacts live under `~/Reports/<org>/<repo>/site-pages/<slug>/`, but the slug
is derived in `orient`, so the **walker state file** lives in a temp dir.

## Steps

1. **Help mode.** If `$ARGUMENTS` is `--help` or `-h`, print the Help blurb
   from `SKILL.md` verbatim and route `init → terminal` via `help`. No state
   file, no work.

2. **State file** (real runs only):
   ```bash
   STATE_BASE="${TMPDIR:-/tmp}/.claude-walker/create-website-content"
   mkdir -p "$STATE_BASE"
   STATE="$STATE_BASE/$(date +%Y-%m-%dT%H-%M-%S).walk-state.json"
   scripts/walk.sh init --state "$STATE"
   ```

3. **Persist the request:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key request --value "<the raw arguments>"
   ```
   If the page type isn't clear from the arguments (answer / help / compare /
   landing / site), infer it in `orient`; ask the user only if two types fit
   equally well.

## Outgoing edges

```bash
scripts/walk.sh transition --state "$STATE" --from init --to orient --condition run
# or, help mode:
scripts/walk.sh transition --state "$STATE" --from init --to terminal --condition help
```

Keep `$STATE` in a variable for the whole run.
