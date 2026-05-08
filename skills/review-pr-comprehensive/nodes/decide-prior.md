# Node: decide-prior

Pure decision: does a prior REVIEW.md exist for this PR? If yes, also note whether the PR has changed since that review.

## Inputs

- `pr_base`, `pr_dir`, `report_ts`, `head_oid` from walker state

```bash
STATE="$PR_DIR/.walk-state.json"
PR_BASE=$(scripts/walk.sh get --state "$STATE" --key pr_base)
PR_DIR=$(scripts/walk.sh get --state "$STATE" --key pr_dir)
REPORT_TS=$(scripts/walk.sh get --state "$STATE" --key report_ts)
HEAD_OID=$(scripts/walk.sh get --state "$STATE" --key head_oid)
```

## Steps

1. **Check for a prior run dir:**
   ```bash
   ls "$PR_BASE/" 2>/dev/null | grep -v "^$REPORT_TS$" | sort
   ```

2. If the listing is empty → no prior runs → record `prior_exists=false` and route via `no_prior`.

3. If at least one prior run dir exists:
   - Pick the most recent (last alphabetically — the timestamps sort correctly).
   - Persist its path:
     ```bash
     PRIOR_DIR=$(ls "$PR_BASE/" | grep -v "^$REPORT_TS$" | sort | tail -1)
     scripts/walk.sh set --state "$STATE" --key prior_dir --value "$PR_BASE/$PRIOR_DIR"
     ```

4. **Detect whether the PR has changed.** GitHub diffs include the commit SHA in `index <sha>...<sha>` headers. Compare the current `HEAD_OID` against the SHA captured in the prior diff:
   ```bash
   PRIOR_HEAD=$(grep -m1 'index ' "$PR_BASE/$PRIOR_DIR/diff.patch" | awk '{print $NF}' | cut -d. -f3-)
   ```
   Or just compare full diffs if that's simpler:
   ```bash
   if diff -q "$PR_DIR/diff.patch" "$PR_BASE/$PRIOR_DIR/diff.patch" >/dev/null 2>&1; then
     PR_CHANGED=false
   else
     PR_CHANGED=true
   fi
   scripts/walk.sh set --state "$STATE" --key pr_changed --value "$PR_CHANGED"
   ```

5. Route via `prior_exists`.

## Outputs

- `prior_dir`, `pr_changed` in walker state (only when prior exists)

## Outgoing edges

- **`prior_exists`** → `confirm-prior-review`. Prior run dir found.
- **`no_prior`** → `independent-reviews`. Clean slate.

Record exactly one:

```bash
# Prior run exists — ask the user:
scripts/walk.sh transition --state "$STATE" --from decide_prior --to confirm_prior_review --condition prior_exists

# No prior — proceed:
scripts/walk.sh transition --state "$STATE" --from decide_prior --to independent_reviews --condition no_prior
```

## Notes

- **Don't ask the user here.** This is a pure decision node. The user-input gate is `confirm-prior-review`.
- **The prior REVIEW.md may not exist** even if the prior run dir exists (e.g., user cancelled mid-review). The skill treats any run dir as "prior run" — `confirm-prior-review` will surface the appropriate context.
