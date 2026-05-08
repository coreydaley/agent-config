# Node: compute-diff

The loop entry point. Each visit starts a new iteration: increments the cycle counter, creates the iteration directory, computes a fresh diff against the working tree (which reflects any commits made by `address` in the previous iteration).

## Inputs

- `base_ref`, `pr_dir`, `next_iteration`, `cycles_in_run` from walker state
- The current working tree

## Steps

1. **Read run-scoped state from the walker:**
   ```bash
   STATE="$PR_DIR/.walk-state.json"   # PR_DIR is in your working memory from init
   BASE_REF=$(scripts/walk.sh get --state "$STATE" --key base_ref)
   PR_DIR_FROM_STATE=$(scripts/walk.sh get --state "$STATE" --key pr_dir)
   NEXT_ITER=$(scripts/walk.sh get --state "$STATE" --key next_iteration)
   CYCLES=$(scripts/walk.sh get --state "$STATE" --key cycles_in_run)
   ```
2. **Create the iteration directory and advance counters:**
   ```bash
   TS=$(date +%Y-%m-%dT%H-%M-%S)
   ITER_DIR="$PR_DIR_FROM_STATE/iteration-$NEXT_ITER-$TS"
   mkdir -p "$ITER_DIR"

   scripts/walk.sh set --state "$STATE" --key iter_dir       --value "$ITER_DIR"
   scripts/walk.sh set --state "$STATE" --key current_iter   --value "$NEXT_ITER"
   scripts/walk.sh set --state "$STATE" --key next_iteration --value $((NEXT_ITER + 1))
   scripts/walk.sh set --state "$STATE" --key cycles_in_run  --value $((CYCLES + 1))
   ```
   `current_iter` is the iteration number this iteration is working in (used for `Seen in: iter-N` ledger entries). `cycles_in_run` is how many compute-diff entries we've completed in this invocation (used by `decide` for the cap check). `next_iteration` is bumped so the next loop has the right number ready.
3. **Generate the diff against the working tree:**
   ```bash
   git diff "origin/$BASE_REF"..HEAD > "$ITER_DIR/diff.patch"
   ```
4. **Sanity check.** If `diff.patch` is empty, the branch has no changes against base. Bail with a message: "Branch has no diff against `origin/<base>`. Self-review has nothing to do." This is a failure of the assumption that the PR has changes — surface to the user, don't proceed silently.
5. **Capture metadata** for use by the review pipeline (commit count, file count):
   ```bash
   git rev-list --count "origin/$BASE_REF"..HEAD
   git diff --name-only "origin/$BASE_REF"..HEAD | wc -l
   ```

## Outputs

- `$ITER_DIR` exists, walker state knows it as `iter_dir`
- `$ITER_DIR/diff.patch` exists and is non-empty
- Counters advanced in walker state: `current_iter`, `next_iteration`, `cycles_in_run`

## Outgoing edges

- → `independent-reviews` (always)

Record the transition:

```bash
scripts/walk.sh transition --state "$PR_DIR/.walk-state.json" --from compute_diff --to independent_reviews
```

## Failure modes

- `origin/<base>` doesn't exist locally → fetch it first: `git fetch origin "$BASE_REF":refs/remotes/origin/$BASE_REF` and retry. If fetch still fails, bail.
- Diff is empty → bail (see step 2).
- Diff is enormous (>10MB say) → warn the user. Self-review on a huge diff is going to be slow and may not produce useful results. Ask whether to proceed.
