# Node: finalize

Record the outcome in PLAN.md, print the summary, hand the user the squash-merge message when history is append-only. Stop. Never merge.

## Inputs

- Everything in walker state: `pr_state`, `pr_url`, `regime`, `approved`, `github_results`, `comment_results`, `commit_results`, `plan_available`, `polish_dir`
- `$POLISH_DIR/PROPOSALS.md` (for the squash-merge message)

```bash
STATE="$PLAN_DIR/.walk-state.polish.json"
```

## Steps

### Arrived via `already_merged`

1. PLAN.md: `Status` → `merged`, Log: `<date> merged as #<N> (<url>)`. Say so in one line. Stop. If the PR merged and Follow-ups is non-empty, list them: they're the work that didn't happen in this PR, and this is the last time the plan will be looked at.

### Everything else

1. **Staged leftovers.** If preflight failed after apply-comments staged edits, commit them now as `chore(<scope>): tighten comments` and push normally, so nothing approved is lost.

2. **PLAN.md Log**, one line: `<date> pr-polish: <title|body|threads N|comments N|commits k→m force-pushed|stopped>`. Status stays `in-review`.

3. **Summary:**
   ```
   PR #<N>:  <url>
   Title:    renamed → "<new>"  |  unchanged
   Body:     rewritten  |  unchanged
   Threads:  2 resolved, 1 left for you
   Comments: 4 edits, committed a1b2c3d and pushed  |  folded into rewrite  |  none
   Commits:  6 → 3, force-pushed (backup tag pr-polish-backup-...)  |  not offered (human review started)  |  skipped: <reason>
   ```
   Warnings, when any step failed, with the verbatim error and the recovery hint. A rejected force-push gets both paths spelled out.

4. **Append regime: the squash-merge message.** Print it in a fenced block, title line first, ready to paste into the merge dialog. This is the thing that lands in the default branch's history, so it's the polish that matters most on a reviewed PR.

5. **Closing line**, only when everything approved landed without warnings:
   ```
   Ready to merge. Mark it ready for review if it's still a draft, then Merge in GitHub when you're ready.
   ```
   Otherwise the warnings are the closing line.

## Outputs

- PLAN.md Log (and Status on merged)
- Printed summary and, in append regime, the squash-merge message

## Outgoing edges

- → `terminal` (always, single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from finalize --to terminal
```

## Notes

- **Don't merge, undraft, or request review.** All the user's.
- **Don't suggest re-running** unless something failed.
