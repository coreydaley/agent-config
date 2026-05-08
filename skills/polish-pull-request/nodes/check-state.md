# Node: check-state

Pure decision: do any of the resolved PRs have state `MERGED` or `CLOSED`?

## Inputs

- `pr_set` from walker state

```bash
STATE="<path>"
PR_SET=$(scripts/walk.sh get --state "$STATE" --key pr_set)
```

## Steps

1. **Empty PR set guard.** If `pr_count` is zero, surface the issue and route to terminal via `no_closed` → fetch-state will then bail on its own (or you can short-circuit by routing directly to terminal). Easiest: print "No PRs to polish" and use `no_closed` so the empty list flows down and `fetch-state` handles it.

2. **Fetch the state for each PR** (one `gh pr view` per PR, JSON-only):
   ```bash
   gh pr view "<owner>/<repo>#<N>" --json state,mergeable,url,title -q '.'
   ```

3. Persist a quick summary:
   ```bash
   scripts/walk.sh set --state "$STATE" --key pr_states --value "<JSON list of {url, state, mergeable, title}>"
   ```

4. **Decide:** if any PR has `state` in `{"MERGED", "CLOSED"}`, route via `has_closed`. Otherwise route via `no_closed`.

## Outputs

- `pr_states` in walker state

## Outgoing edges

- **`has_closed`** → `confirm-closed`. At least one PR is merged or closed; ask the user.
- **`no_closed`** → `fetch-state`. All PRs are open; proceed.

Record exactly one:

```bash
# Has closed/merged:
scripts/walk.sh transition --state "$STATE" --from check_state --to confirm_closed --condition has_closed

# All open:
scripts/walk.sh transition --state "$STATE" --from check_state --to fetch_state --condition no_closed
```

## Notes

- **Don't ask the user here.** Pure decision. The user-input gate is `confirm-closed`.
- **Polishing a closed PR is rare and usually a mistake.** That's why we surface and confirm rather than proceeding silently.
