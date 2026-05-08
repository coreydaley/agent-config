# Node: init

Parse arguments, set up walker state. This skill polishes one or more PRs in place — no per-run report directory.

## Inputs

- The user's arguments to the skill (zero or more PR identifiers)

PR identifier shapes:

- PR URL: `https://github.com/<org>/<repo>/pull/<N>`
- PR number: `<N>` (resolves against `gh pr view`'s default repo)
- Empty: detect from current branch via `gh pr view --json url,number`

Multiple identifiers (space-separated) → multi-repo mode.

## Steps

1. **Parse `$ARGUMENTS`** into a list of raw PR identifiers. Empty → empty list (auto-detect later).

2. **Set up walker state.** This skill doesn't write to `~/Reports/`, so the state file lives in a temp dir:
   ```bash
   STATE_BASE="${TMPDIR:-/tmp}/.claude-walker/polish-pr"
   mkdir -p "$STATE_BASE"
   STATE="$STATE_BASE/$(date +%Y-%m-%dT%H-%M-%S).walk-state.json"
   scripts/walk.sh init --state "$STATE"
   ```

3. **Persist run-scoped state:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key raw_args --value "<original $ARGUMENTS>"
   ```

## Outputs

- `$STATE` exists

## Outgoing edges

- → `resolve-prs` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from init --to resolve_prs
```

## Failure modes

- `gh` not authenticated → bail with "run `gh auth login` first" before any state mutation. (Could also defer this until `resolve-prs` if simpler.)
