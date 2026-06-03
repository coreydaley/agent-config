# Node: summarize

Phase 11: per-repo / per-issue summary, suggested next step, stop.

## Inputs

- Result fields from walker state, shape depending on `path_mode`:
  - **sprintmd / forgejo-issue:** `implement_results`, `tests_passed`, `criteria_results`, `commit_results` (singular per-sprint values)
  - **forgejo-walk:** `forgejo_walk_results` (object map keyed by issue ref `<owner/repo#n>`, each entry containing `{tests, criteria, commits}` from validate-success and commit-push invocations) plus `implement_results` and `skipped_issue_ids`
- Plus: `path_mode`, `repos`, `issue_ids`, `active_issue_ids`

```bash
STATE="<path>"
```

## Steps

Print a concise summary:

```
Target:      <Forgejo issue ref + title | Sprint <session-TS> + title>
Path mode:   <sprintmd | forgejo-issue | forgejo-walk>
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

Commits pushed (one per issue):
  - <owner>/<repo>#42  →  <sha>  on main  (issue closed)
  - <owner>/<repo>#43  →  <sha>  on main  (issue closed)
  (sprintmd: one commit summarizing the sprint, no issue to close)
```

If anything went sideways, include a **Warnings** section:

```
Warnings:
  - Push for <repo> rejected: <error>. Reconcile (pull/rebase) and re-run
    /sprint-work — the issue stays open until the commit lands on the default branch.
  - Test suite failed in <repo>: see $TEST_LOG_DIR/<repo>.log
```

## Milestone completion check (feeds the auto-retro)

Compute how many issues are **still open in the milestone** and persist
it so `check-milestone` can route on it (and so this summary can tell the
user what's left). Skip for the `sprintmd` path or any run with no
resolved milestone — persist `0`/empty and let `check-milestone` treat it
as "no milestone."

```bash
MILESTONE_REPO=$(scripts/walk.sh get --state "$STATE" --key milestone_repo)
MILESTONE_NAME=$(scripts/walk.sh get --state "$STATE" --key milestone_name)
if [ -n "$MILESTONE_REPO" ] && [ -n "$MILESTONE_NAME" ]; then
  OPEN_LEFT=$(tea issues list --repo "$MILESTONE_REPO" \
    --milestones "$MILESTONE_NAME" --state open --output json | jq 'length')
else
  OPEN_LEFT=""   # no milestone (sprintmd / single issue w/o milestone)
fi
scripts/walk.sh set --state "$STATE" --key milestone_open_count --value "${OPEN_LEFT:-}"
```

## Suggested next step

The retro is **automatic** — if this run just closed the last open issue
in the milestone, `check-milestone` writes the retrospective and closes
the milestone right after this summary. So frame the next step on what's
left:

```
Milestone <name>: <OPEN_LEFT> issue(s) still open
  → /sprint-work <target>     # continue the milestone
(— or, if OPEN_LEFT == 0 —)
All milestone issues closed → writing the retrospective and closing the
sprint now.
```

For the `sprintmd` path (no milestone), keep the manual hint:

```
  /sprint-work --retro <target>          # write the retrospective and
                                         # mark the sprint complete
```

If the path was `forgejo-walk` and any issue failed (with `--continue`), surface the failed issues separately so the user knows what to revisit. If a push was rejected, call that out — the issue won't have closed (so the milestone won't read as complete, and the auto-retro correctly won't fire).

## Don'ts

- **Don't run `git push`** at this phase. `commit-push` already pushed each issue's commit; nothing further to push here.
- **Don't re-touch the issues here.** `implement` / `commit-push` already commented, closed, and labeled them; summarize only reports.
- **Don't open a PR.** This flow commits straight to the default branch.
- **Don't mark the sprint completed here.** `write-retro` does that — reached either via the auto-retro (`check-milestone`, when this run emptied the milestone) or an explicit `--retro`. Summarize only reports and computes the open count.

## Outputs

- Printed summary
- `milestone_open_count` in walker state (drives `check-milestone`)

## Outgoing edges

- → `check-milestone` (always — single outgoing edge). It decides whether
  this run completed the milestone and, if so, auto-fires the retro.

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from summarize --to check_milestone
```

## Notes

- **Be specific in the summary.** "Tests: PASS" without the test count is worse than "Tests: PASS (218 unit, 14 e2e)" if the numbers are easy to capture.
- **Surface every commit SHA and which issue it closed.** The SHA + issue ref is the audit trail for what shipped.
