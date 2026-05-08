# Node: init

Set up state for the self-review run. Resolve which PR we're working on, verify it's a draft, work out paths, and load any existing ledger.

## Inputs

- `$ARGUMENTS` from the skill invocation (optional PR number or URL)
- Current branch
- Any existing `findings.md` from prior runs on this PR

## Steps

1. **Resolve the PR.** If `$ARGUMENTS` contains a number or URL, use it. Otherwise call `gh pr view --json number,state,baseRefName,isDraft` against the current branch.
2. **Verify state.** The PR must exist, be open, and be in draft state.
   - No PR for the current branch → error: "No open PR found for this branch. Run `/sprint-work` first or open a draft PR manually."
   - PR is closed/merged → error: "PR #N is <state>. self-review only operates on open draft PRs."
   - PR is open but not draft → warn the user. Ask whether to proceed anyway (the team is already notified) or abort. Default abort.
3. **Resolve report paths.** Derive `<org>/<repo>` from the source repo (prefer `upstream` remote, fall back to `origin`, see `CLAUDE.md` Reports section). Build:
   - `PR_DIR=$HOME/Reports/<org>/<repo>/self-reviews/pr-<N>`
   - `FINDINGS=$PR_DIR/findings.md`
4. **Load the ledger.** If `$FINDINGS` exists, load it. We're continuing a prior run.
5. **Pick the next iteration number.** Look for `$PR_DIR/iteration-*` directories. The next iteration is `max(existing) + 1`, or `1` if none exist. Iterations number monotonically across the PR's life — don't reset per run.
6. **Create the iteration directory.** `mkdir -p $PR_DIR/iteration-<N>-<TS>/` where `<TS>` is `YYYY-MM-DDTHH-MM-SS` for the current invocation.
7. **Print a brief opening message.** Tell the user: PR number, base ref, iteration number, prior runs (if findings.md existed), and the path to findings.md so they can follow along.
8. **Initialize the walker state file.** This creates `$PR_DIR/.walk-state.json` and registers `init` as the current node.
   ```bash
   scripts/walk.sh init --state "$PR_DIR/.walk-state.json"
   ```
   If this command fails (e.g., graph.dot has structural problems), bail.
9. **Persist run-scoped state** so it survives across tool calls and sessions:
   ```bash
   STATE="$PR_DIR/.walk-state.json"
   scripts/walk.sh set --state "$STATE" --key pr_number       --value "$PR_NUMBER"
   scripts/walk.sh set --state "$STATE" --key base_ref        --value "$BASE_REF"
   scripts/walk.sh set --state "$STATE" --key pr_dir          --value "$PR_DIR"
   scripts/walk.sh set --state "$STATE" --key findings_path   --value "$PR_DIR/findings.md"
   scripts/walk.sh set --state "$STATE" --key max_cycles      --value "${MAX_CYCLES:-3}"
   scripts/walk.sh set --state "$STATE" --key cycles_in_run   --value 0
   scripts/walk.sh set --state "$STATE" --key next_iteration  --value "$NEXT_ITER_N"
   ```
   Subsequent nodes read these via `scripts/walk.sh get --state "$STATE" --key <name>` rather than re-deriving them. If the session crashes, the next session can resolve `$STATE` from `$HOME/Reports/<org>/<repo>/self-reviews/pr-<N>/.walk-state.json` (using `gh pr view --json number` to get N) and resume.

## Outputs

- `$PR_DIR/iteration-<N>-<TS>/` exists (created by `review` on entry, not here — init only computes `next_iteration`)
- `$PR_DIR/.walk-state.json` exists with all run-scoped variables in `extra`
- If a prior `findings.md` was loaded, its contents are in working memory for the dedup logic in `address`

## Outgoing edges

- → `compute-diff` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$PR_DIR/.walk-state.json" --from init --to compute_diff
```

## Failure modes

- Missing PR / wrong state: bail with clear message before any work begins. Don't enter the loop with bad state.
- `gh` not authenticated: bail with "run `gh auth login` first."
