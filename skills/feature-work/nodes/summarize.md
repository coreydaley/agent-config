# Node: summarize

Per-repo / per-sub-issue rundown, the **DEFER punch list** (the collaborative ~10%), and the next step — which reminds the user the merge is theirs. Then stop.

## Inputs

- Result fields from walker state:
  - **single sub-issue:** `implement_results`, `tests_passed`, `criteria_results`, `commit_results`
  - **multi-sub-issue walk:** `feature_walk_results` (object map keyed by sub-issue ref `<owner/repo#m>`, each entry `{tests, criteria, commits}`) plus `implement_results` and `shipped_subissue_ids`
- Plus: `feature_ref`, `feature_title`, `feature_branch`, `repos`, `subissue_ids`, `active_subissue_ids`, `deferrals`

```bash
STATE="<path>"
```

## Steps

Print a concise summary:

```
Feature:       <feature_ref> — <feature_title>
Branch:        <feature/<slug>>  (commits land here; NOT merged)
Repos:         <single | multi: repo1, repo2>

Sub-issues:
  shipped (commit on branch):
    - <owner>/<repo>#5  →  <sha>  (open — closes on merge)
    - <owner>/<repo>#6  →  <sha>  (open — closes on merge)
  resumed/skipped (already on branch from a prior run):
    - <owner>/<repo>#4  →  <sha>
  failed (recorded, not committed):
    - <owner>/<repo>#7  →  <reason>

Files changed (per repo):
  <repo1>: <git diff --stat first line vs the base branch>

Tests:         <PASS | FAIL — see logs>
```

If anything went sideways, include a **Warnings** section:

```
Warnings:
  - Push for <repo> rejected: <error>. Reconcile (pull/rebase the feature
    branch) and re-run /feature-work <feature_ref>.
  - Test suite failed in <repo>: see $TEST_LOG_DIR/<repo>.log
```

## The DEFER punch list (the collaborative handoff)

Read `deferrals` (plus any criteria marked deferred in `validate-success`) and print the punch list — what the autonomous run **intentionally left** for the user to finish together. This is the handoff from the ~90% to the ~10%, not a failure list:

```
Punch list — left for you (autonomous run can't decide these):
  - [#5] Tune the empty-state copy — subjective/visual call.
  - [#6] Verify the haptic on a real device — needs hardware.
  - [#7] Wire the prod API key — needs a secret I won't handle.
  - [#8] Submit the screenshots in App Store Connect — submission step.
```

If there were no deferrals, say so: "Nothing deferred — the full feature built autonomously." Keep each line scoped to a sub-issue and stated so the user can act on it cold.

## Suggested next step

The sub-issues are committed on the feature branch but **OPEN** — they close when the user merges. Frame the next step around that:

```
Branch <feature/<slug>> is ready on each repo. The sub-issues stay open until
you merge.

Next (your call):
  - Review the branch, finish the punch list together, then merge
    <feature/<slug>> → <default-branch> per repo — that fires each Closes #N
    and closes the sub-issues.
  - Or re-run /feature-work <feature_ref> later to resume any failed/unfinished
    sub-issues (already-shipped ones are skipped automatically).
```

If any sub-issue failed, surface those separately so the user knows what to revisit. If a push was rejected, call it out — that sub-issue's commit didn't reach the branch.

## Don'ts

- **Don't run `git push`** here. `commit-push` already pushed each sub-issue's commit to the feature branch.
- **Don't re-touch the sub-issues here.** `implement` / `commit-push` already commented and assigned them; summarize only reports.
- **Don't merge, don't open a PR.** This flow stops at the pushed feature branch; the merge is the user's.
- **Don't close any sub-issue.** They close on merge.
- **Don't bury the punch list.** It's the point of the handoff — make it prominent.

## Outputs

- Printed summary + punch list

## Outgoing edges

- → `terminal` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from summarize --to terminal
```

## Notes

- **Be specific in the summary.** "Tests: PASS" without the count is worse than "Tests: PASS (218 unit, 14 e2e)" when the numbers are easy to capture.
- **Surface every commit SHA and which sub-issue it ships.** The SHA + sub-issue ref is the audit trail for what's on the branch.
- **Make the punch list the headline of the handoff.** A clean defer-and-report is a successful run, not a half-finished one.
