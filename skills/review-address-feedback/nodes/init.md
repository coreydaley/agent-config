# Node: init

Parse arguments, detect input mode, set up paths, initialize walker state.

## Inputs

- The user's arguments to the skill (optional)
  - PR number or URL → **Mode A** (live PR inline comments)
  - Path to a `REVIEW.md` ending in `.md` that exists → **Mode B** (local artifact)
  - Empty → **Mode A** against the current branch's open PR

The two modes are mutually exclusive. The skill loads findings from exactly one source.

## Steps

1. **Detect mode.**
   - If the argument is a number, GitHub URL, or empty → Mode A.
   - If the argument looks like a path that exists and ends in `.md` → Mode B.
   - Anything else → bail with "couldn't tell whether `<arg>` is a PR or a REVIEW.md path; pass a PR number/URL or a `.md` path."

2. **Resolve the PR number.**
   - Mode A: use the arg as-is, extract the trailing number from URLs, or fall back to `gh pr view --json number -q .number` for the current branch.
   - Mode B: parse the `# Code Review: PR #N` header from the REVIEW.md so Phase 4 can attempt GitHub replies. If the header is missing, leave `pr_number` empty and disable GitHub-side actions for this run.

3. **Verify the PR exists** (Mode A, and Mode B when `pr_number` was parsed). `gh pr view <N>` should succeed. If not, error: "PR #N not found, or you don't have access."

4. **Resolve report paths.** Derive `<org>/<repo>` from the source repo (prefer `upstream`, fall back to `origin`). Build:
   - `PR_BASE=$HOME/Reports/<org>/<repo>/pr-reviews/pr-<N>`
   - `SESSION_TS=$(date +%Y-%m-%dT%H-%M-%S)`
   - `SESSION_DIR=$PR_BASE/$SESSION_TS-addressed`
   - `mkdir -p "$SESSION_DIR"`

5. **Initialize the walker state file.**
   ```bash
   STATE="$SESSION_DIR/.walk-state.json"
   scripts/walk.sh init --state "$STATE"
   ```

6. **Persist run-scoped state** in the walker so it survives across tool calls and sessions:
   ```bash
   scripts/walk.sh set --state "$STATE" --key mode         --value "<A|B>"
   scripts/walk.sh set --state "$STATE" --key pr_number    --value "$PR_NUMBER"
   scripts/walk.sh set --state "$STATE" --key review_path  --value "$REVIEW_PATH"  # Mode B only
   scripts/walk.sh set --state "$STATE" --key pr_base      --value "$PR_BASE"
   scripts/walk.sh set --state "$STATE" --key session_dir  --value "$SESSION_DIR"
   scripts/walk.sh set --state "$STATE" --key session_ts   --value "$SESSION_TS"
   ```

7. **Print a brief opening message** — mode, PR number, session directory.

## Switch-mode re-entry

`choose-strategy` can route back here when a Mode B run wants to switch to Mode A. On re-entry, this node:

- Reads `mode` from the existing state file.
- If the prior mode was B and the user just chose `switch_mode`, flip to Mode A: clear `review_path`, refresh `session_ts` and `session_dir` (new run dir, fresh `ADDRESSED.md`), keep `pr_number` if it's known.
- Re-init the walker state via `scripts/walk.sh init --state "$STATE"` against the new session dir.

The walker tracks history across the re-init only inside the same state file — the new run creates a new `.walk-state.json`. That's fine: the previous run's `ADDRESSED.md` (if any) stays where it is, the new run is a clean slate.

## Outputs

- `$SESSION_DIR/` exists
- `$SESSION_DIR/.walk-state.json` exists with run-scoped fields in `extra`

## Outgoing edges

- → `verify-worktree` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from init --to verify_worktree
```

## Failure modes

- PR not found / no access → bail with a clear message before touching any files.
- `gh` not authenticated → bail with "run `gh auth login` first."
- Mode B path doesn't exist → bail with "no REVIEW.md at `<path>`."
- Argument is ambiguous (looks neither like a PR nor a path) → bail with the disambiguation prompt above.
