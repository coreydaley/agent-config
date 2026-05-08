# Node: decide-prior

Look for prior reviews of this PR and route based on what we find. Pure decision node — doesn't ask the user, just picks an edge.

## Inputs

- `$PR_BASE` from walker state (the parent dir for all this PR's reviews)
- `$REPORT_TS` from walker state (this run's timestamp, to exclude from "prior")

## Steps

```bash
STATE="$PR_DIR/.walk-state.json"
PR_BASE=$(scripts/walk.sh get --state "$STATE" --key pr_base)
REPORT_TS=$(scripts/walk.sh get --state "$STATE" --key report_ts)

PRIOR=$(/bin/ls "$PR_BASE/" 2>/dev/null | /usr/bin/grep -v "^$REPORT_TS$" | /usr/bin/sort | /usr/bin/tail -1)
```

If `$PRIOR` is empty, no prior runs exist. Otherwise, the latest prior run is `$PR_BASE/$PRIOR`, and `$PR_BASE/$PRIOR/REVIEW.md` is the canonical prior REVIEW.

If a prior exists, also detect whether the PR has changed since that review — compare current head SHA against the SHA recorded in the prior `metadata.json`:

```bash
CURRENT_SHA=$(/usr/bin/jq -r .headRefOid "$PR_DIR/metadata.json")
PRIOR_SHA=$(/usr/bin/jq -r .headRefOid "$PR_BASE/$PRIOR/metadata.json" 2>/dev/null)
if [ "$CURRENT_SHA" = "$PRIOR_SHA" ]; then
  CHANGED=false
else
  CHANGED=true
fi
```

Persist the prior info so `confirm-prior-review` can use it without re-discovering:

```bash
scripts/walk.sh set --state "$STATE" --key prior_dir         --value "$PR_BASE/$PRIOR"
scripts/walk.sh set --state "$STATE" --key prior_changed     --value "$CHANGED"
```

(Only set these if `$PRIOR` is non-empty.)

## Outgoing edges

Two outgoing edges. Pick based on whether a prior REVIEW exists.

- **`prior_exists`** → `confirm-prior-review`. There's at least one prior REVIEW for this PR.
- **`no_prior`** → `review`. Fresh review, no prior to consider.

Record exactly one:

```bash
# Prior review exists — ask the user how to handle it:
scripts/walk.sh transition --state "$STATE" --from decide_prior --to confirm_prior_review --condition prior_exists

# No prior — straight to fresh review:
scripts/walk.sh transition --state "$STATE" --from decide_prior --to review --condition no_prior
```

## Failure modes

- `$PR_BASE` doesn't exist (init didn't create it correctly): treat as `no_prior`.
- Prior `metadata.json` missing or malformed: treat the PR as changed (`prior_changed=true`) so the user is prompted to consider re-reviewing rather than silently showing a possibly-stale review.
