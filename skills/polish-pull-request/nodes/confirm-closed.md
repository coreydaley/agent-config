# Node: confirm-closed

One or more resolved PRs are merged/closed. Surface clearly and ask whether to proceed.

## Inputs

- `pr_states` from walker state

```bash
STATE="<path>"
PR_STATES=$(scripts/walk.sh get --state "$STATE" --key pr_states)
```

## Steps

Use `AskUserQuestion`. List the closed/merged PRs by title and state, then:

> "Polishing a closed/merged PR is unusual — usually a mistake. Proceed anyway?"
>
> 1. **Yes, proceed** — polish all PRs in the set, including the closed/merged ones
> 2. **Skip the closed ones** — drop them from the set, polish the rest
> 3. **Cancel** — exit without doing anything

If the user picks "skip the closed ones," update `pr_set` and `pr_count` accordingly:

```bash
scripts/walk.sh set --state "$STATE" --key pr_set --value "<filtered JSON>"
scripts/walk.sh set --state "$STATE" --key pr_count --value "<new N>"
```

If after filtering the set is empty, route via `user_cancel` to terminal.

## Outputs

- Possibly updated `pr_set` and `pr_count`

## Outgoing edges

- **`user_proceed`** → `fetch-state`. User picked options 1 or 2.
- **`user_cancel`** → `terminal`. User picked option 3 (or "skip" emptied the set).

Record exactly one:

```bash
# Proceed:
scripts/walk.sh transition --state "$STATE" --from confirm_closed --to fetch_state --condition user_proceed

# Cancel:
scripts/walk.sh transition --state "$STATE" --from confirm_closed --to terminal --condition user_cancel
```

## Notes

- **Default to "skip the closed ones" when ambiguous.** If the user said "yeah polish the rest," that's the safer interpretation.
- **The choice is the confirmation.** No follow-up "are you sure?" prompts.
