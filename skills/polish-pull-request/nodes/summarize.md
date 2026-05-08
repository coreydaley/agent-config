# Node: summarize

Per-PR final summary. Tell the user what happened, including any partial-failure states so they can recover.

## Inputs

- All result fields from walker state: `tbt_results`, `comment_results`, `commit_results`, `cleanup_skip_reason`, `cleanup_choice`, etc.

```bash
STATE="<path>"
```

## Steps

For each PR, print:

```
PR: <owner>/<repo>#<N>
  Title:        <new title> (renamed from "<old>") | unchanged
  Body:         rewritten | unchanged
  Threads:      N resolved, M ambiguous left open
  Cross-links:  consistent across multi-repo PRs | not applicable
  Commits:      rewritten (<orig N> → <new M>, force-pushed) | skipped (<reason>) | not approved
  Comments:     N edits applied | not approved
  Status:       Ready for merge | Partial — see warnings below
```

If anything went sideways (push rejected, hook failure mid-rewrite, comment edit failed), include a **Warnings** section per PR with the verbatim error and the recovery hint:

```
Warnings:
  - Commit rewrite on PR-A: force-push rejected (remote moved). Local
    branch is in rewritten state; either re-fetch and re-run polish,
    or `git reset --hard origin/<head-ref>` to discard the rewrite.
```

## Closing line

```
PR(s) ready for merge — click Merge in GitHub when you're ready.
```

But ONLY if everything actually completed successfully. If anything is in a partial state, don't print this line — the user needs to address the warnings first.

## Outputs

- Printed summary

## Outgoing edges

- → `terminal` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from summarize --to terminal
```

## Notes

- **Don't merge.** The skill never merges; that's always the user's manual click.
- **Don't suggest re-running** unless something failed. If everything went well, the next step is "click Merge" — that's the only suggestion that should appear.
