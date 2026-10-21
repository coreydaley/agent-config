# Node: display

Show the proposals and ask, in plain text, which categories to apply. One final message, no tool call after it. `ask-polish` records the transition next turn.

## Inputs

- `polish_dir`, `regime`, `commit_cleanup_available`, `commit_cleanup_skip_reason` from walker state
- `$POLISH_DIR/PROPOSALS.md`

## Steps

1. **PROPOSALS.md inline**, in full. Body diffs rendered as diffs, comment edits as before/after pairs, the commit regroup as the list it is.

2. **Path line:**
   ```
   📄 <reports-root>/<org>/<repo>/prs/<key>/polish/<TS>/PROPOSALS.md
   ```

3. **The question**, plain text. Categories are named so the destructive one can't ride along on a general yes:

   **rewrite regime, commit cleanup available:**
   > Apply which? Name the categories: **title**, **body**, **threads**, **comments**, **commits**. **all** means the first four. Commits rewrite history and force-push with `--force-with-lease`, so that one only happens if you name it. **adjust** to change a proposal, **stop** to leave everything as is.

   **append regime** (or commit cleanup skipped):
   > Apply which? Name the categories: **title**, **body**, **threads**, **comments**, or **all**. History is append-only on this PR, so comment edits land as a new commit and the squash-merge message above is for the merge dialog. **adjust** to change a proposal, **stop** to leave everything as is.

   Ambiguous threads listed under "your call" are included in **threads** only if the user names them ("threads including the ambiguous one at x.go:40"). Otherwise threads means the resolved-by-code set.

4. **End the turn.**

## Outputs

- The proposals are in the conversation

## Outgoing edges

- → `ask-polish` (always, single outgoing edge, recorded next turn)

```bash
scripts/walk.sh transition --state "$STATE" --from display --to ask_polish
```

## Notes

- **"all" excludes commits on purpose.** Sub-actions get their own confirmation, and a force-push is the one that most needs it.
- **Say what each category does to the outside world.** Title, body, threads are GitHub writes. Comments are a commit and a push. Commits are a force-push.
