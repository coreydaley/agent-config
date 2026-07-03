# Node: init

Parse arguments, detect help mode, and set up the walker state file. This skill's per-run artifacts live under `~/Reports/<org>/<repo>/blog-posts/<slug>/`, but that path depends on the slug (derived in `orient`), so the **walker state file** itself lives in a temp dir.

## Inputs

- `$ARGUMENTS` — the post topic (free text). May contain `--help` / `-h`.

## Steps

1. **Detect help mode.** If `$ARGUMENTS` is exactly `--help` or `-h` (or empty with a help intent), this is help mode — do **not** create a state file or run any work. Print the Help blurb from `SKILL.md` verbatim and route `init → terminal` via `help`.

2. **Resolve the state-file location** (real runs only):
   ```bash
   STATE_BASE="${TMPDIR:-/tmp}/.claude-walker/create-blog-post"
   mkdir -p "$STATE_BASE"
   STATE="$STATE_BASE/$(date +%Y-%m-%dT%H-%M-%S).walk-state.json"
   ```

3. **Initialize the walker state file:**
   ```bash
   scripts/walk.sh init --state "$STATE"
   ```

4. **Persist the topic** for downstream nodes:
   ```bash
   scripts/walk.sh set --state "$STATE" --key topic --value "<the raw topic text>"
   ```

   Nothing else is known yet — `orient` derives the slug, paths, and conventions.

## Outputs

- `$STATE` exists (real runs) with `topic` set.
- Help mode: nothing written; help text printed.

## Outgoing edges

- **`run`** → `orient`. A real run with a topic.
- **`help`** → `terminal`. `--help` / `-h` was passed; help text already printed.

Record exactly one:

```bash
# Real run:
scripts/walk.sh transition --state "$STATE" --from init --to orient --condition run

# Help mode (no state file needed; omit --state if none was created):
scripts/walk.sh transition --state "$STATE" --from init --to terminal --condition help
```

## Notes

- **Keep `$STATE` in a variable for the whole run.** Every downstream node needs it.
- The walker is consistent with the rest of the skill fleet; for this skill its main payoff is resume support — a crashed run's state file records which phase was reached.
