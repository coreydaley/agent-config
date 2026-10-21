# Node: finalize

Summary, an honest call on whether another review pass is warranted, and the next step. Stop.

## Inputs

- Everything in walker state: `outcomes_path`, `push_result`, `fix_commits`, `pr_url`, `regime`, `fix_dir`, `plan_dir`, `mode`
- `$FIX_DIR/addressed.json`, the branch diff stat before and after (before is recorded by triage's Diff growth line)

```bash
STATE="$PLAN_DIR/.walk-state.fix.json"
```

## Steps

1. **Summary:**
   ```
   Findings:  7 → 4 fixed, 2 deferred (PLAN.md Follow-ups), 1 won't-fix
   Commits:   3 fixups squashed into originals, force-with-lease pushed   |   2 commits pushed   |   left local
   Replies:   3 posted   |   skipped   |   n/a (review-sourced)
   Diff:      +212/-40 → +230/-44 (files touched: 6 → 6)
   Record:    <reports-root>/<org>/<repo>/prs/<key>/fixes/<TS>/ADDRESSED.md
   ```
   Blocked or stale rows get their own lines with what the user should look at.

2. **Re-review call.** This is where the "three review passes on one PR" pattern is broken. Recommend another `/pr-review` only if one of these is true:
   - a fix touched a file the branch hadn't touched before,
   - any fixed finding was Blocker or High and the fix was more than a few lines,
   - the fix set grew the diff by more than about a third,
   - a fix changed behavior rather than a check, a message, or a test.

   Otherwise say plainly: "These fixes don't warrant another full review pass." An XS fix set gets no re-review (`lib/pr-discipline.md` § Verification Ceremony Scales With Stakes).

3. **Next step**, one line:

   - Re-review warranted: `Next: /pr-review`.
   - Not warranted, PR is a draft: "Next: mark the PR ready for review and request reviewers on GitHub." (The user does both.)
   - Not warranted, human review in progress: "Next: wait for the reviewer. Replies are posted." or "Next: reply to the threads yourself (skipped here)."
   - Stopped at triage: `Resume: /pr-fix <path to TRIAGE.md>`.
   - Push rejected or left local: the exact push command, ready to paste, and the regime it must respect.

## Outputs

- Printed summary and recommendation

## Outgoing edges

- → `terminal` (always, single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from finalize --to terminal
```

## Notes

- **Don't undraft, don't request reviewers, don't merge.** All the user's.
- **Don't recommend re-review reflexively.** The default after a fix round is no re-review. The list above is the exception set.
