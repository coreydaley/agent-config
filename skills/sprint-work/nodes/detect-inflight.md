# Node: detect-inflight

Phase 5: detect work already in flight (existing PR, in-progress sprint state, commits ahead of base) and ask the user how to proceed. Avoids redoing work and routes to the right follow-on skill if the user wants.

## Inputs

- `path_mode`, `repos`, `worktree_paths`, `issue_ids`, `sprint_query` from walker state

```bash
STATE="<path>"
PATH_MODE=$(scripts/walk.sh get --state "$STATE" --key path_mode)
```

## Linear paths

Use each issue's current state from `load-context`:

| State | Default behavior |
|---|---|
| Backlog / Triage / Todo | Fresh start; route via `user_continue`. No prompt. |
| In Progress / Started | Show last commit on branch + any open PR. AskUserQuestion: continue / address review feedback / cancel. |
| In Review | Open PR exists. AskUserQuestion: address review feedback / push more commits / cancel. |
| Done / Canceled | Refuse; tell the user to pick a different issue. Route via `user_exit`. |

For `linear-walk`, run this check per issue. If any issue is Done/Canceled, surface and ask whether to skip-and-continue or bail.

## SPRINT.md path

No Linear state; use ledger + git signals:

```bash
# Ledger status:
/sprints --current
/sprints --list

# Existing PRs on the feature branch:
CUR_BRANCH=$(git branch --show-current)
gh pr list --head "$CUR_BRANCH" --json number,url,state,title

# Local commits ahead of base:
git log --oneline upstream/main..HEAD | head -10
```

Decide:
- Sprint status `in_progress`, OR a PR exists, OR commits ahead of base → AskUserQuestion (see options below).
- Otherwise → fresh state, route via `user_continue` silently.

## AskUserQuestion options

When work is detected, ask:

> 1. **Continue from here** — proceed with the full pipeline, layering changes on top
> 2. **Address review feedback** — exit; suggest `/review-address-feedback <PR>` instead
> 3. **Push more commits to existing PR** — proceed but skip Phase 10 PR creation (existing PR will be updated when you push)
> 4. **Cancel** — stop without doing anything

Persist the user's choice:

```bash
scripts/walk.sh set --state "$STATE" --key inflight_choice --value "<continue|address|push_more|cancel>"
scripts/walk.sh set --state "$STATE" --key skip_pr_open --value "<true|false>"
```

`skip_pr_open=true` when choice is "push_more" — `open-prs` checks this flag.

## Outputs

- `inflight_choice`, `skip_pr_open` in walker state

## Outgoing edges

- **`user_continue`** → `show-plan`. Continue or push-more (push-more is a state flag, not a separate route — `open-prs` handles it).
- **`user_exit`** → `terminal`. Cancel or address-feedback (the latter exits with a suggestion for the next skill).

Record exactly one:

```bash
# Continue (or push-more):
scripts/walk.sh transition --state "$STATE" --from detect_inflight --to show_plan --condition user_continue

# Exit:
scripts/walk.sh transition --state "$STATE" --from detect_inflight --to terminal --condition user_exit
```

## Notes

- **Default to "Continue from here" when ambiguous.** The user can still cancel from `ask-approval` after seeing the plan.
- **For "Address review feedback"**, surface the suggestion clearly: `Suggested: /review-address-feedback <PR-url>` before routing to terminal.
- **Don't proceed silently when in-flight state is detected.** Ask explicitly. Re-running over existing work is rarely intended.
