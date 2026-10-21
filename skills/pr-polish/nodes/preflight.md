# Node: preflight

Pure decision, no user input. Time has passed since analyze. Re-verify that rewriting the branch is still safe, right before doing it.

## Inputs

- `worktree`, `base_ref`, `branch`, `head_at_init`, `pr_number`, `repo` from walker state

```bash
STATE="$PLAN_DIR/.walk-state.polish.json"
WT=$(scripts/walk.sh get --state "$STATE" --key worktree)
BASE_REF=$(scripts/walk.sh get --state "$STATE" --key base_ref)
```

## Checks

All must pass:

1. **Regime hasn't flipped.** Re-query the PR's reviews and comments. A human comment since init means history is append-only now. Fail with that reason. This is the check that matters most.
2. **Working tree clean** except for changes staged by apply-comments. Unrelated unstaged changes → fail.
3. **HEAD unchanged** since init (`git -C "$WT" rev-parse HEAD` equals `head_at_init`). Someone (or the user) committed in between → fail.
4. **Remote matches local.** `git -C "$WT" fetch origin "$BRANCH"`, then `origin/$BRANCH` must equal `HEAD`. Otherwise the lease would fail anyway. Fail early with a clearer message.
5. **Only our commits.** `git -C "$WT" log --format=%ae "$BASE_REF..HEAD" | sort -u` is exactly one address, ours.
6. **No merge commits** from the base in the range.
7. **Base ref fetched** just now, so the reset target is current.

## Outputs

- A pass or a printed reason for failing

## Outgoing edges

- **`preflight_ok`** → `apply-commits`
- **`preflight_failed`** → `finalize` (staged comment edits, if any, are committed there as a plain chore commit so nothing is lost)

```bash
scripts/walk.sh transition --state "$STATE" --from preflight --to apply_commits --condition preflight_ok
scripts/walk.sh transition --state "$STATE" --from preflight --to finalize      --condition preflight_failed
```

## Notes

- **Don't ask the user here.** Fail and explain. They re-run after fixing the cause.
- **Cheap insurance before the one destructive step.** Every check is a few milliseconds against the cost of a bad force-push.
