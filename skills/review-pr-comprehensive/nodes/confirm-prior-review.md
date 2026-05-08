# Node: confirm-prior-review

A prior review exists. Ask the user how to proceed, framing the question differently depending on whether the PR has changed since the last review.

## Inputs

- `prior_dir`, `pr_changed`, `pr_number` from walker state

```bash
STATE="$PR_DIR/.walk-state.json"
PRIOR_DIR=$(scripts/walk.sh get --state "$STATE" --key prior_dir)
PR_CHANGED=$(scripts/walk.sh get --state "$STATE" --key pr_changed)
PR_NUMBER=$(scripts/walk.sh get --state "$STATE" --key pr_number)
```

## Steps

Use `AskUserQuestion`. Frame based on `pr_changed`:

### `pr_changed=true` — PR has new commits

> "PR #N has 1 prior review from [timestamp]. The PR has been updated since then. Proceed with a new review?"
>
> 1. **Yes, review the updated PR** — runs the full dual-agent pipeline
> 2. **No, open the existing review instead** — print the prior REVIEW.md and stop
> 3. **Cancel** — do nothing, exit

### `pr_changed=false` — same diff as last review

Warn more strongly:

> "PR #N has 1 prior review from [timestamp] and the diff appears unchanged. Re-reviewing the same diff will likely produce similar results."
>
> 1. **Yes, re-review anyway** — runs the full dual-agent pipeline
> 2. **No, open the existing review instead** — print the prior REVIEW.md and stop
> 3. **Cancel** — do nothing, exit

## Outputs

- No file changes. Walker state only:
  ```bash
  scripts/walk.sh set --state "$STATE" --key prior_choice --value "<re_review|show_existing|cancel>"
  ```

## Outgoing edges

- **`user_re_review`** → `independent-reviews`. User wants a fresh review.
- **`user_show_existing`** → `show-existing`. User wants to see the prior review.
- **`user_cancel`** → `cleanup-worktree`. User wants out (worktree was set up, needs cleanup).

Record exactly one:

```bash
# Re-review:
scripts/walk.sh transition --state "$STATE" --from confirm_prior_review --to independent_reviews --condition user_re_review

# Show existing:
scripts/walk.sh transition --state "$STATE" --from confirm_prior_review --to show_existing --condition user_show_existing

# Cancel:
scripts/walk.sh transition --state "$STATE" --from confirm_prior_review --to cleanup_worktree --condition user_cancel
```

## Notes

- **Default to "show existing" when `pr_changed=false`.** Re-running the same review on the same diff is rarely useful; the user is usually trying to find something they already have.
- **The choice is the confirmation.** Don't add an "are you sure?" after.
