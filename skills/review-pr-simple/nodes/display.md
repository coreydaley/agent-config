# Node: display

Output the freshly-written `REVIEW.md` inline so the user can read it without opening a file.

## Inputs

- `$PR_DIR/REVIEW.md` (just written by `review`)

```bash
STATE="$PR_DIR/.walk-state.json"
PR_DIR=$(scripts/walk.sh get --state "$STATE" --key pr_dir)
```

## Steps

1. **Read `$PR_DIR/REVIEW.md`.**
2. **Output its full contents inline** as markdown in the user's response. Don't just reference the file path — the whole point is the user can scan it without leaving the terminal.
3. **End with a short location reminder** so the user knows where the artifacts live:

   > _(saved to `$PR_DIR/REVIEW.md`; supporting artifacts in `$PR_DIR/`)_

## Outputs

- REVIEW.md content rendered inline in the response
- No file changes

## Outgoing edges

- → `ask-next-action` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from display --to ask_next_action
```

## Failure modes

- REVIEW.md missing or empty (review node failed silently): print a brief error and bail to terminal rather than asking the user about a non-existent review.
