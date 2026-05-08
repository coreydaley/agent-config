# Node: summarize

Phase 11: per-repo / per-issue summary, suggested next step, stop.

## Inputs

- All result fields: `implement_results`, `tests_passed`, `criteria_results`, `pr_results`, `path_mode`, `repos`, `issue_ids` from walker state

```bash
STATE="<path>"
```

## Steps

Print a concise summary:

```
Target:      <Linear ID + title | Sprint <number> + title>
Path mode:   <sprintmd | linear-issue | linear-walk>
Repos:       <single | multi: repo1, repo2>

Files changed (per repo):
  <repo1>: <git diff --stat first line>
  <repo2>: <git diff --stat first line>

Tests:       <PASS | FAIL — see logs>
Success Criteria:
  <count> met
  <count> ship-without
  <count> deferred
  <count> not-met

PRs opened:
  - <repo1>: <PR URL>  [DRAFT]
  - <repo2>: <PR URL>  [DRAFT]
  (or "skipped — pushed to existing PR" if skip_pr_open)

Multi-repo cross-links: confirmed (or "not applicable")
```

If anything went sideways, include a **Warnings** section:

```
Warnings:
  - PR for <repo> failed to open: <error>. Re-run /sprint-work or open
    manually with `gh pr create --draft ...`.
  - Test suite failed in <repo>: see $TEST_LOG_DIR/<repo>.log
```

## Suggested next step

```
Ready for review:
  /review-pr-comprehensive <PR-url>      # for the full dual-agent review
  /review-pr-simple <PR-url>             # for a quick single-agent pass

After PRs merge:
  /sprint-work --retro <target>          # to write the retrospective and
                                         # close the sprint in the ledger
```

If the path was `linear-walk` and any issue failed (with `--continue`), surface the failed issues separately so the user knows what to revisit.

## Don'ts

- **Don't run `git commit` / `git push`** beyond what `gh pr create` did.
- **Don't set Linear issue state** — Linear's GitHub integration handles the transition when the PR opens.
- **Don't comment on the Linear issue** — same.
- **Don't merge.** Always the user's call.
- **Don't mark the sprint completed in the ledger.** Only `--retro` does that.

## Outputs

- Printed summary

## Outgoing edges

- → `terminal` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from summarize --to terminal
```

## Notes

- **Be specific in the summary.** "Tests: PASS" without the test count is worse than "Tests: PASS (218 unit, 14 e2e)" if the numbers are easy to capture.
- **Surface every PR URL.** Even if the user is going to open a follow-on review skill, they may want to share the URL with reviewers immediately.
