# Node: preflight-cleanup

Pure decision: re-verify branch state is still safe to rewrite. Time has passed since `analyze` ran — the user may have committed, the remote may have moved, etc.

## Inputs

- The PR set, with each PR's branch info

```bash
STATE="<path>"
```

## Steps

For each PR's branch, run these checks:

```bash
git status --porcelain                   # working tree clean (modulo
                                         # staged comment edits from apply-comments)
git rev-parse HEAD                       # matches what analyze saw
git fetch origin "$BASE"                 # base ref current
git log --pretty=%an "origin/$BASE"..HEAD \
  | sort -u                              # only the current user
```

Validation rules:

- **Working tree clean** — except for staged changes from `apply-comments`. If there are unrelated unstaged changes, fail preflight.
- **HEAD matches `analyze`'s snapshot.** Persist `head_at_analyze` in walker state during `analyze`; compare here. If they differ, fail.
- **Base ref fetched and current.** If the fetch fails, fail.
- **Only the current user authored commits.** If `git log --pretty=%an base..HEAD | sort -u` returns more than one author, fail.

## Outputs

- A pass/fail decision and a printed reason if failed.

## Outgoing edges

- **`preflight_ok`** → `apply-commits`. All checks passed.
- **`preflight_failed`** → `summarize`. Some check failed; surface why and route to summary so the user sees what was applied so far.

Record exactly one:

```bash
# Safe to rewrite:
scripts/walk.sh transition --state "$STATE" --from preflight_cleanup --to apply_commits --condition preflight_ok

# Not safe — bail to summary:
scripts/walk.sh transition --state "$STATE" --from preflight_cleanup --to summarize --condition preflight_failed
```

## Notes

- **Don't ask the user.** This is pure decision. If preflight fails, surface the reason and route to `summarize` — the user will see what changed up to this point and can re-run polish after fixing the underlying issue.
- **Defensive on purpose.** History rewrite + force-push is destructive. Re-checking right before the destructive op is cheap insurance.
- **Persist `head_at_analyze` early.** `analyze` (or `init`) should record the HEAD SHA so this node has something to compare against.
