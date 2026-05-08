# Node: show-existing

Print the prior REVIEW.md inline and route to terminal. No new review run.

## Inputs

- `prior_dir` from walker state

## Steps

```bash
STATE="$PR_DIR/.walk-state.json"
PRIOR_DIR=$(scripts/walk.sh get --state "$STATE" --key prior_dir)
```

Read `$PRIOR_DIR/REVIEW.md` and output its full contents inline as markdown in the user's response context. Don't just reference the path — the user picked "show existing" because they want to read it now.

After printing, optionally note:

> _(prior review run: `$PRIOR_DIR/`)_

So the user can navigate there if they want the supporting artifacts (diff.patch, ci-status.txt, etc.).

## Outputs

- Prior REVIEW.md content rendered inline in the response
- No new files written, no new state changes (this run was a "view only" exit)

## Outgoing edges

- → `terminal` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from show_existing --to terminal
```

## Failure modes

- `$PRIOR_DIR/REVIEW.md` is missing despite `decide-prior` finding the directory: print a brief explanation and route to terminal anyway. Don't fall back to running a fresh review (the user chose "show existing" — respect that choice; if they wanted a fresh review they would have picked it).
