# Node: init

Parse the feature-issue argument, init walker state. Handle `--help` inline. **This skill has no flags other than `--help`.**

## Inputs

- The user's arguments to the skill: `<feature-issue-ref> [--help]`

## Steps

1. **Detect `--help`.** If present anywhere in args, print the help blurb (verbatim from SKILL.md's "Help mode" section) and stop. **Don't proceed to walker init.**

2. **Parse the argument.** Exactly one positional is expected: the **feature-issue reference** (a URL, `<owner>/<repo>#N`, or bare `#N` in the cwd repo). Capture it as `target_args`.
   - **No flags** are accepted other than `--help` / `-h`. Any other `--flag` → fail loudly with the offending flag and a one-line "this skill takes a single feature-issue ref; the only flag is --help."
   - **No target** (no positional given) → bail: "Pass the feature issue to build — a URL, `<owner>/<repo>#N`, or `#N` in the cwd repo. Plan it first with /feature-plan if you haven't."

3. **Autonomy contract.** Once the feature resolves, the skill works through every sub-issue to completion without approval gates or "keep going?" prompts. It only stops at a genuine wall (unresolvable target, missing bare clone, unresolvable test failure on the single targeted sub-issue) or when there's nothing to do (every sub-issue already shipped a commit on the feature branch).

4. **Set up walker state.** At init time `$SESSION_DIR` isn't known yet — it's resolved by `resolve-target` / `load-context`. So init creates a transient state file under `$TMPDIR`.

   ```bash
   STATE_BASE="${TMPDIR:-/tmp}/.claude-walker/feature-work"
   mkdir -p "$STATE_BASE"
   STATE="$STATE_BASE/$(date +%Y-%m-%dT%H-%M-%S).walk-state.json"
   scripts/walk.sh init --state "$STATE"
   ```

5. **Persist run-scoped state:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key target_args --value "<the feature-issue ref from $ARGUMENTS>"
   ```

## Outputs

- `$STATE` exists; `target_args` persisted

## Outgoing edges

- → `resolve-target` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from init --to resolve_target
```

## Failure modes

- Unknown flag → bail before walker init with a clear error.
- No feature-issue ref → bail (step 2).
- `tea` not authenticated (no default login) → defer detection until `resolve-target` (which actually calls it).
