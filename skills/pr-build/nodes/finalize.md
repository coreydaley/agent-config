# Node: finalize

Record the outcome in PLAN.md, print the summary and the next step. Stop.

## Inputs

- `plan_path`, `worktree`, `base_ref`, `branch_proposed`, `tests_passed`, `gaps`, `sweep_findings`, `open_choice`, `pr_result`, `pr_url`, `pr_number` from walker state

```bash
STATE="$PLAN_DIR/.walk-state.build.json"
```

## Steps

1. **PLAN.md header.**
   - `Branch`: drop a `(proposed)` marker if the branch now exists.
   - `Status`: `in-review` when `pr_result` is `opened` or `pushed`. Otherwise stays `building`.

2. **PLAN.md Log**, one line by outcome:
   - `<date> pr-build: opened #<N> as draft (<url>)`
   - `<date> pr-build: pushed <k> commits to #<N>, body updated`
   - `<date> pr-build: <k> commits on <branch>, PR not opened (user stop)`
   - `<date> pr-build: pushed, PR creation failed: <one-line error>`

   The `user_blocked` route from verify goes straight to terminal, so verify writes its own Log line before transitioning.

3. **Summary**, compact:
   ```
   Branch:  fix/gh-123-retry-budget (5 commits ahead of upstream/main, pushed)
   Tests:   PASS (build-verify.log)
   Sweep:   3 fixes, 1 chore commit
   Gaps:    none   |   2 shipped-with, listed in the PR and PLAN.md Follow-ups
   PR:      https://github.com/acme/widget/pull/N (draft)
   Plan:    ~/Reports/<org>/<repo>/prs/<key>/PLAN.md (status: in-review)
   ```
   Auto-stashed changes from setup-worktree get a reminder line here.

4. **Next step**, one line, matched to the outcome:

   - PR opened or pushed: `Next: /pr-review` (the pre-review procedure continues there, then /pr-fix, then you mark the PR ready for review and request reviewers on GitHub).
   - Stopped before opening: how to resume: `/pr-build` again picks up the branch, or push and create by hand with `pr-body.md`.
   - Create failed: the exact `gh pr create` command with the body file, ready to paste.

## Outputs

- PLAN.md `Status`, `Branch`, `Log` updated
- Printed summary

## Outgoing edges

- → `terminal` (always, single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from finalize --to terminal
```

## Notes

- **Don't ask for human review.** The order is fixed (`lib/pr-discipline.md` § PR Pre-Review Procedure): sweeps (done), pr-review, pr-fix, then the user marks the PR ready and requests reviewers. This skill ends before step two.
- **Don't undraft, don't merge, don't add reviewers or labels.** All the user's.
- **No "shall I run pr-review?"** The next step is printed. The user runs it.
