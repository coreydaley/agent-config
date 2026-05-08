# Node: confirm-prior-review

Prior review found. Ask the user what to do.

## Inputs

- `prior_dir` and `prior_changed` from walker state (set by `decide-prior`)

## Steps

```bash
STATE="$PR_DIR/.walk-state.json"
PRIOR_DIR=$(scripts/walk.sh get --state "$STATE" --key prior_dir)
CHANGED=$(scripts/walk.sh get --state "$STATE" --key prior_changed)
```

Compose the prompt based on `$CHANGED`:

### PR has changed since prior review (`CHANGED=true`)

> A prior review of this PR exists at `$PRIOR_DIR/REVIEW.md` (run on
> {timestamp}). The PR has been updated since then. What now?
>
> 1. Re-review (run a fresh review against the current diff)
> 2. Show the existing review (print the prior REVIEW.md and stop)
> 3. Cancel (stop without doing anything)

### PR is unchanged since prior review (`CHANGED=false`)

> A prior review of this PR exists at `$PRIOR_DIR/REVIEW.md` (run on
> {timestamp}) and the PR diff appears unchanged since then.
> Re-reviewing the same diff will likely produce similar results.
> What now?
>
> 1. Re-review anyway
> 2. Show the existing review (print the prior REVIEW.md and stop)
> 3. Cancel (stop without doing anything)

Use `AskUserQuestion`. Always include the prior path in the prompt body so the user can open it directly if they want to read it before deciding.

## Outgoing edges

- **`user_re_review`** → `review`. User wants a fresh review.
- **`user_show_existing`** → `show-existing`. User wants to see the prior REVIEW.md and stop.
- **`user_cancel`** → `terminal`. User cancels.

Record exactly one based on the user's answer:

```bash
# Re-review:
scripts/walk.sh transition --state "$STATE" --from confirm_prior_review --to review --condition user_re_review

# Show existing:
scripts/walk.sh transition --state "$STATE" --from confirm_prior_review --to show_existing --condition user_show_existing

# Cancel:
scripts/walk.sh transition --state "$STATE" --from confirm_prior_review --to terminal --condition user_cancel
```

## Failure modes

- User aborts (Ctrl-C / no answer): treat as `user_cancel`.
- Prior REVIEW.md doesn't actually exist at `$PRIOR_DIR/REVIEW.md` (run was created but never wrote it): warn and offer only re-review or cancel.
