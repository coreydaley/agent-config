# Node: init

Resolve which PR we're reviewing, set up paths, initialize the walker state file.

## Inputs

- `$ARGUMENTS` from the skill invocation (PR number or URL, optional)
- Current branch (used for auto-detection if no arg)

## Steps

1. **Resolve the PR.** If `$ARGUMENTS` contains a number or URL, use it. If it's a URL, extract the trailing PR number. If empty, call `gh pr view --json number -q .number` against the current branch.
2. **Verify the PR exists.** `gh pr view <N>` should succeed. If not, error: "PR #N not found, or you don't have access."
3. **Resolve report paths.** Derive `<org>/<repo>` from the source repo (prefer `upstream` remote, fall back to `origin` — see `CLAUDE.md` Reports section). Build:
   - `PR_BASE=$HOME/Reports/<org>/<repo>/pr-reviews/pr-<N>`
   - `REPORT_TS=$(date +%Y-%m-%dT%H-%M-%S)`
   - `PR_DIR=$PR_BASE/$REPORT_TS`
4. **Create the run directory.** `mkdir -p "$PR_DIR"`.
5. **Initialize the walker state file.**
   ```bash
   STATE="$PR_DIR/.walk-state.json"
   scripts/walk.sh init --state "$STATE"
   ```
6. **Persist run-scoped state** in the walker so it survives across tool calls and sessions:
   ```bash
   scripts/walk.sh set --state "$STATE" --key pr_number  --value "$PR_NUMBER"
   scripts/walk.sh set --state "$STATE" --key pr_base    --value "$PR_BASE"
   scripts/walk.sh set --state "$STATE" --key pr_dir     --value "$PR_DIR"
   scripts/walk.sh set --state "$STATE" --key report_ts  --value "$REPORT_TS"
   ```
7. **Print a brief opening message** — PR number, run directory.

## Outputs

- `$PR_DIR/` exists
- `$PR_DIR/.walk-state.json` exists with run-scoped fields in `extra`

## Outgoing edges

- → `fetch-context` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from init --to fetch_context
```

## Failure modes

- PR not found / no access → bail with a clear message before touching any files.
- `gh` not authenticated → bail with "run `gh auth login` first."
