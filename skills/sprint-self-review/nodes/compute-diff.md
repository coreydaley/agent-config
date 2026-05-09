# Node: compute-diff

The loop entry point. Each visit starts a new iteration: increments the cycle counter, creates the iteration directory, and computes per-repo diffs against each worktree's HEAD (which reflects any commits made by `address` in the previous iteration).

## Inputs

- `self_review_dir`, `repos`, `worktree_paths`, `prs`, `next_iteration`, `cycles_in_run` from walker state

```bash
# The walker passes $STATE (path to .walk-state.json) on every transition.
# Everything else derives from it: SESSION_DIR is the grandparent of STATE
# (since STATE = <session_dir>/self-review/.walk-state.json). Don't try
# to derive STATE from SESSION_DIR — SESSION_DIR isn't exported across
# node boundaries.
SESSION_DIR=$(dirname "$(dirname "$STATE")")
SELF_REVIEW_DIR=$(scripts/walk.sh get --state "$STATE" --key self_review_dir)
REPOS=$(scripts/walk.sh get --state "$STATE" --key repos)
WORKTREE_PATHS=$(scripts/walk.sh get --state "$STATE" --key worktree_paths)
PRS=$(scripts/walk.sh get --state "$STATE" --key prs)
NEXT_ITER=$(scripts/walk.sh get --state "$STATE" --key next_iteration)
CYCLES=$(scripts/walk.sh get --state "$STATE" --key cycles_in_run)
```

## Steps

### 1. Create the iteration directory and advance counters

```bash
TS=$(date +%Y-%m-%dT%H-%M-%S)
ITER_DIR="$SELF_REVIEW_DIR/iteration-$NEXT_ITER-$TS"
mkdir -p "$ITER_DIR/diffs"

scripts/walk.sh set --state "$STATE" --key iter_dir       --value "$ITER_DIR"
scripts/walk.sh set --state "$STATE" --key current_iter   --value "$NEXT_ITER"
scripts/walk.sh set --state "$STATE" --key next_iteration --value $((NEXT_ITER + 1))
scripts/walk.sh set --state "$STATE" --key cycles_in_run  --value $((CYCLES + 1))
```

### 2. Per-repo diffs

For each repo in `$REPOS`, resolve the base ref using the same `upstream → origin → local` ladder used by `/sprint-work/detect-inflight`. **Don't hardcode `origin/<base>`** — in the standard fork-with-upstream layout, `origin` is the personal fork and stale; diffing against it gives reviewers a corrupted bundle.

```bash
ORG=<from JSON>; REPO=<from JSON>
WT=$(echo "$WORKTREE_PATHS" | jq -r ".[\"$ORG/$REPO\"]")
BASE=$(echo "$PRS" | jq -r ".[\"$ORG/$REPO\"].base_ref")  # from gh pr view (PR's baseRefName)
PATCH="$ITER_DIR/diffs/$ORG-$REPO.patch"

# Resolve the base ref per repo. Try upstream first (source-of-truth in
# our workflow), then origin (personal fork), then local. Fetch the chosen
# remote ref so the diff is current.
if git -C "$WT" rev-parse --verify "upstream/$BASE" >/dev/null 2>&1; then
  git -C "$WT" fetch upstream "$BASE":refs/remotes/upstream/$BASE 2>/dev/null
  REMOTE_BASE="upstream/$BASE"
elif git -C "$WT" rev-parse --verify "origin/$BASE" >/dev/null 2>&1; then
  git -C "$WT" fetch origin "$BASE":refs/remotes/origin/$BASE 2>/dev/null
  REMOTE_BASE="origin/$BASE"
elif git -C "$WT" rev-parse --verify "$BASE" >/dev/null 2>&1; then
  REMOTE_BASE="$BASE"     # local-only base (sandbox-style or detached repos)
else
  bail "Cannot resolve base ref $BASE for $ORG/$REPO. Tried upstream/$BASE, origin/$BASE, $BASE."
fi

git -C "$WT" diff "$REMOTE_BASE"..HEAD > "$PATCH"
```

### 3. Sanity check

For each repo's patch:

- **Empty** → record `<org>/<repo>: empty` in walker state under `iter_<N>_diff_summary`. This means that repo has no diff against base. For multi-repo sprints, this is informational (maybe one repo's work was retracted, or the work is concentrated in another repo). For single-repo sprints, the meaning depends on iteration:
  - **Iter 1, single-repo, all empty** → hard failure, nothing to review. Bail.
  - **Iter N>1, all empty** → **terminal-clean signal**, NOT a failure. All findings have been fixed and the diff against base is now clean. Synthesize an empty findings round (no high_open, no low_open), write a one-line REVIEW.md noting "diff went clean on iter N", and let the iteration flow to `decide` → `only_low_nit` → `escalate` → user picks "done". This is the success path; bailing here would block legitimate completion.
  - **Multi-repo, all empty, any iteration** → bail iter 1 (nothing planned was implemented), terminal-clean iter N>1 (same reasoning).
- **Enormous (>10MB)** → warn the user. Self-review on a huge bundle is going to be slow and may not produce useful results. Ask whether to proceed.

### 4. Capture per-repo metadata

For the iteration's review-prompt context (commit count, file count per repo). **Reuse `$REMOTE_BASE` from step 2** — don't re-derive against `origin/$BASE`, which is wrong for fork-with-upstream layouts (same bug as the diff command had pre-fix):

```bash
for each repo:
  # $REMOTE_BASE was resolved in step 2 via the upstream/origin/local ladder
  git -C "$WT" rev-list --count "$REMOTE_BASE"..HEAD
  git -C "$WT" diff --name-only "$REMOTE_BASE"..HEAD | wc -l
```

Store as `iter_<N>_repo_stats` in walker state for the review prompt.

## Outputs

- `$ITER_DIR/` exists, walker state knows it as `iter_dir`
- `$ITER_DIR/diffs/<org>-<repo>.patch` per repo, each non-empty (unless that repo has no work this iteration)
- Counters advanced in walker state: `current_iter`, `next_iteration`, `cycles_in_run`

## Outgoing edges

- → `independent-reviews` (always)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from compute_diff --to independent_reviews
```

## Failure modes

- `origin/<base>` missing in a worktree → fetch first; if that fails, bail.
- All repos' diffs empty → bail (no work to review).
- One repo's diff missing because the worktree was deleted between init and now → bail; tell the user to re-run `/sprint-work`.
