# Node: detect-inflight

**Git-derived resume.** Read the `feature/<slug>` branch's commit log and skip any sub-issue whose `Closes #N` commit is already on the branch — it's done. This is the whole resume mechanism: no stored cursor, no `--continue` flag. Automatic, never prompts. Only "every sub-issue already shipped" stops the run here.

## Inputs

- `repos`, `worktree_paths`, `subissue_ids`, `feature_branch` from walker state

```bash
STATE="<path>"
WORKTREE_PATHS=$(scripts/walk.sh get --state "$STATE" --key worktree_paths)
SUBISSUE_IDS=$(scripts/walk.sh get --state "$STATE" --key subissue_ids)
FEATURE_BRANCH=$(scripts/walk.sh get --state "$STATE" --key feature_branch)
```

## What "already done" means

A sub-issue is **done** when a commit carrying its `Closes #<m>` trailer is already on the feature branch. That's the durable, idempotent signal — it survives `$TMPDIR` cleanup, reboots, and re-runs, because it lives in git history, not in any walker state. (Sub-issues stay *open* until the user merges, so issue state alone can't tell you what's done this branch — the commit log is the source of truth.)

### Scan the feature branch for shipped sub-issues

For each repo's feature-branch worktree, collect the `Closes #<m>` refs already committed:

```bash
for ORG_REPO in $(echo "$WORKTREE_PATHS" | jq -r 'keys[]'); do
  WT=$(echo "$WORKTREE_PATHS" | jq -r ".[\"$ORG_REPO\"]")

  # Commits on the feature branch but NOT on its base (the default branch),
  # so we only count work this feature added. @{upstream} or the merge-base
  # against the default branch both work; grep their messages for Closes #N.
  git -C "$WT" log --format='%B' "$FEATURE_BRANCH" \
    | grep -Eio 'closes #[0-9]+' | grep -Eo '[0-9]+'
done
```

Build the set of **shipped sub-issue numbers** (per repo, so `#5` in repo A isn't confused with `#5` in repo B). A sub-issue `<owner>/<repo>#<m>` is done if its `#<m>` appears in that repo's shipped set.

### Filter the work list

Partition `subissue_ids` into:

- **active** — still-open sub-issues with **no** `Closes #<m>` commit on the branch yet.
- **shipped** — sub-issues already committed this branch (skip — resume past them).

Also skip any sub-issue already `closed` on GitHub (rare for this flow, but it means the work merged in a prior cycle).

```bash
scripts/walk.sh set --state "$STATE" --key active_subissue_ids  --value "<JSON: still-to-do refs>"
scripts/walk.sh set --state "$STATE" --key shipped_subissue_ids --value "<JSON: already-on-branch refs, with reason>"
```

`implement`'s loop reads `active_subissue_ids` (not `subissue_ids`) so shipped sub-issues are excluded. `summarize` reads `shipped_subissue_ids` to report what was skipped as already-done.

## In-flight local changes

If a feature-branch worktree has uncommitted changes (e.g. a prior run was interrupted mid-sub-issue, after the auto-stash), note it briefly and **proceed** — `implement` layers its work on top and `commit-push` commits everything for the active sub-issue. Don't prompt.

## Decide

- **Something to do** (at least one active sub-issue) → print a one-line note of what's being resumed/skipped, then route via `proceed`.
- **Nothing to do** (every sub-issue already has a `Closes #N` commit on the branch, or is closed) → route via `nothing_to_do`.

## Outputs

- `active_subissue_ids` / `shipped_subissue_ids` in walker state

## Outgoing edges

- **`proceed`** → `show-plan`. There's work to do; carry on autonomously.
- **`nothing_to_do`** → `terminal`. Every sub-issue already shipped a commit on the feature branch — nothing left to build. (Remind the user the branch is ready to merge.)

Record exactly one:

```bash
# Work to do:
scripts/walk.sh transition --state "$STATE" --from detect_inflight --to show_plan --condition proceed

# Nothing left:
scripts/walk.sh transition --state "$STATE" --from detect_inflight --to terminal --condition nothing_to_do
```

## Notes

- **Never prompt here.** The run is autonomous; this node only detects and decides. The only exit is "nothing to do."
- **The feature branch's commit log is the cursor.** Resume is idempotent by construction — re-running the same `/feature-work <feature-issue-ref>` picks up exactly where the branch left off. There is no `--continue`; there is no stored position.
- **A shipped sub-issue means its commit is on the branch — not that it's merged.** It still shows OPEN on GitHub until the user merges. Skip it for *this* run's work, but it's not "closed" yet.
