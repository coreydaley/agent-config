# Node: show-result

Show the user the recent commit history so they can review what just landed.

## Steps

```bash
git log --oneline -50
```

Display the output. That's it.

## Outputs

- Printed git log, last 50 commits.

## Outgoing edges

- → `terminal` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from show_result --to terminal
```

## Notes

- **Always run `show-result`**, even on partial commit failure. The user needs to see what landed and what didn't.
- **Don't filter the log** to "just our commits." `git log --oneline -50` gives the user enough context to see how this run sits relative to recent history.
