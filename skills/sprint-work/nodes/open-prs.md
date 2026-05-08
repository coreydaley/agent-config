# Node: open-prs

Phase 10: open draft PR(s). Multi-repo: one per repo, cross-link bodies. Skip creation when `skip_pr_open=true` (push-more flag from `detect-inflight`).

## Inputs

- `path_mode`, `repos`, `merge_order`, `context_dir`, `issue_ids`, `skip_pr_open`, `criteria_results` from walker state

```bash
STATE="<path>"
SKIP_PR_OPEN=$(scripts/walk.sh get --state "$STATE" --key skip_pr_open)
REPOS=$(scripts/walk.sh get --state "$STATE" --key repos)
PATH_MODE=$(scripts/walk.sh get --state "$STATE" --key path_mode)
```

## Push-more skip

If `skip_pr_open=true` (the user picked "push more commits to existing PR" in `detect-inflight`):

- **Don't open a new PR.** The existing PR will be updated when the user pushes.
- Record this in the summary so the user knows.
- Route to `summarize` via the standard edge — the summarize node will reflect that no new PR was opened.

## PR conventions (when actually opening)

**Always open as draft** (`gh pr create --draft ...`). Drafts give the user a chance to review the auto-generated body, add reviewers, check CI, and run `/polish-pull-request` before the team is notified. The user marks the PR ready-for-review themselves when they're satisfied — **this skill never undrafts**.

### PR title

```
<LINEAR-ID>: <short summary>
```

If no Linear issue is associated (pure SPRINT.md path without Linear handoff), drop the prefix:

```
<short summary>
```

Imperative-style summary, sentence case, max ~70 chars total. Completion-framed (*"Add full tag support for python"*, not *"Implement -full for python"*).

### PR body — concise template

```markdown
## Summary

[1-2 sentences on what this PR does and why.]

## Linear            (omit if no Linear issue)

[CON-1234 — Issue Title](https://linear.app/<workspace>/issue/CON-1234)

## Companion PR      (multi-repo only)

[<companion PR URL>](<url>) — [brief role description]

## Test plan

- [ ] [verification step]
- [ ] [verification step]
```

If any Success Criteria were marked "ship without" or "defer" in `validate-success`, add a `## Known incomplete` section listing them.

## Multi-repo

Open one PR per repo. Order of opening follows the issue's / SPRINT.md's **Merge order** if specified; otherwise alphabetical. After both open, update each PR's body to add the companion-PR cross-link to the other.

```bash
gh pr edit <PR_A> --body "$NEW_BODY_A_WITH_LINK_TO_PR_B"
gh pr edit <PR_B> --body "$NEW_BODY_B_WITH_LINK_TO_PR_A"
```

Both PRs reference the same Linear issue ID (when applicable) so Linear's GitHub integration attaches both to the issue.

## Don'ts

- **Don't post a comment on the Linear issue.** Linear's GitHub integration links PRs automatically.
- **Don't undraft.** That's the user's call.
- **Don't merge.** Same.
- **Don't run `git push` outside what `gh pr create` does.** No extra branch shuffling.

## Outputs

- Draft PR(s) opened on GitHub
- Persist for `summarize`:
  ```bash
  scripts/walk.sh set --state "$STATE" --key pr_results --value "<JSON: per-repo PR URL or skip-reason>"
  ```

## Outgoing edges

- → `summarize` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from open_prs --to summarize
```

## Failure modes

- `gh pr create` fails (auth, permission, branch not pushed) → surface error, record the failure for that repo, continue with other repos. `summarize` reflects partial success.
- Multi-repo: PR A opens, PR B fails → `summarize` flags the gap; the user can `/sprint-work` again or open the second PR manually.
