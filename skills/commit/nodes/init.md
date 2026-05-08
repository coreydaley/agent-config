# Node: init

Set up the walker state file. This skill doesn't write to `~/Reports/` (no per-PR or per-sprint scope), so the state file lives in a temp dir that gets cleaned up by the OS.

## Steps

1. **Resolve the state-file location:**
   ```bash
   STATE_BASE="${TMPDIR:-/tmp}/.claude-walker/commit"
   mkdir -p "$STATE_BASE"
   STATE="$STATE_BASE/$(date +%Y-%m-%dT%H-%M-%S).walk-state.json"
   ```

2. **Initialize the walker state file:**
   ```bash
   scripts/walk.sh init --state "$STATE"
   ```

3. **Persist any run-scoped state.** None needed at init — `build-plan` produces everything downstream nodes need. Skip the `set` calls.

## Outputs

- `$STATE` exists

## Outgoing edges

- → `build-plan` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from init --to build_plan
```

## Notes

- **Walker is overkill here, but consistent with the rest of the suite.** The state file is small and disposable. If a session crashes mid-commit, the resume story is "look at `git log` and decide what's left" — the walker doesn't add resilience for this skill.
- **Don't write to `~/Reports/`.** Commit isn't a workflow that produces a per-run artifact worth keeping; the artifact is the commit history itself.
