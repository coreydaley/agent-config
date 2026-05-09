# Node: detect-inflight

Phase 5: detect work already in flight (existing PR, in-progress sprint state, commits ahead of base) and ask the user how to proceed. Avoids redoing work and routes to the right follow-on skill if the user wants.

## Inputs

- `path_mode`, `repos`, `worktree_paths`, `issue_ids`, `sprint_query`, `branch_name`, `session_dir` from walker state

```bash
STATE="<path>"
PATH_MODE=$(scripts/walk.sh get --state "$STATE" --key path_mode)
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
WORKTREE_PATHS=$(scripts/walk.sh get --state "$STATE" --key worktree_paths)
BRANCH=$(scripts/walk.sh get --state "$STATE" --key branch_name)
REPORTS_ROOT=$(scripts/walk.sh get --state "$STATE" --key reports_root)
```

## Linear paths

Use each issue's current state from `load-context`:

| State | Default behavior |
|---|---|
| Backlog / Triage / Todo | Fresh start; route via `user_continue`. No prompt. |
| In Progress / Started | Show last commit on branch + any open PR. AskUserQuestion: continue / address review feedback / cancel. |
| In Review | Open PR exists. AskUserQuestion: address review feedback / push more commits / cancel. |
| Done / Canceled | Refuse; tell the user to pick a different issue. Route via `user_exit`. |

For `linear-walk`, run this check per issue. If any issue is Done/Canceled, surface and ask whether to skip-and-continue or bail. **Persist the filtered list** so `implement` honors the skip:

```bash
# After per-issue user prompts, build the filtered active list and
# persist it for implement.md's loop. Don't just record the choice —
# implement reads issue_ids from walker state and won't know to skip.
scripts/walk.sh set --state "$STATE" --key active_issue_ids --value "<JSON: filtered ID list>"
scripts/walk.sh set --state "$STATE" --key skipped_issue_ids --value "<JSON: skipped ID list, with per-issue reason>"
```

`implement.md`'s linear-walk loop reads `active_issue_ids` (not `issue_ids`) so Done/Canceled-and-skipped issues are excluded. `summarize` reads `skipped_issue_ids` to surface what was skipped and why.

## SPRINT.md path

No Linear state; use ledger + git signals. The skill is cwd-independent — query the right ledger explicitly via `--root`, and check existing PRs / commits per repo via `worktree_paths`:

```bash
# Ledger status (the right ledger, even for cross-cutting sprints):
/sprints --current --root "$REPORTS_ROOT"
/sprints --list    --root "$REPORTS_ROOT"

# Per repo: existing PRs on the sprint branch, plus local commits ahead of
# that PR's base. Iterate the manifest's worktree_paths instead of relying
# on cwd. Don't assume `upstream/main` — different repos use different
# remotes (upstream vs. origin) and different default branches
# (main / master / develop). Resolve per-repo from the PR's baseRefName.
for ORG_REPO in $(echo "$WORKTREE_PATHS" | jq -r 'keys[]'); do
  WT=$(echo "$WORKTREE_PATHS" | jq -r ".[\"$ORG_REPO\"]")

  PR_JSON=$(gh pr list --repo "$ORG_REPO" --head "$BRANCH" \
    --json number,url,state,title,baseRefName)

  # baseRefName comes from the PR if one exists. If no PR yet, fall back to
  # the repo's default branch via `gh repo view --json defaultBranchRef`.
  BASE_REF=$(echo "$PR_JSON" | jq -r '.[0].baseRefName // empty')
  if [ -z "$BASE_REF" ]; then
    BASE_REF=$(gh repo view "$ORG_REPO" --json defaultBranchRef \
      -q '.defaultBranchRef.name')
  fi

  # Try upstream first (the source-of-truth remote in our workflow), then
  # origin (personal fork). Sandbox-style regular clones may have neither
  # `upstream` nor a separate `origin/<base>`, in which case we use the
  # local branch ref and skip the ahead-count if even that's missing.
  if git -C "$WT" rev-parse --verify "upstream/$BASE_REF" >/dev/null 2>&1; then
    REMOTE_BASE="upstream/$BASE_REF"
  elif git -C "$WT" rev-parse --verify "origin/$BASE_REF" >/dev/null 2>&1; then
    REMOTE_BASE="origin/$BASE_REF"
  elif git -C "$WT" rev-parse --verify "$BASE_REF" >/dev/null 2>&1; then
    REMOTE_BASE="$BASE_REF"
  else
    REMOTE_BASE=""
  fi

  if [ -n "$REMOTE_BASE" ]; then
    git -C "$WT" log --oneline "$REMOTE_BASE..HEAD" | head -10
  else
    echo "(could not resolve base $BASE_REF for $ORG_REPO; skipping ahead-count)"
  fi
done
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
