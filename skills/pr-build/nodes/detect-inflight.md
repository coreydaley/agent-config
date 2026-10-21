# Node: detect-inflight

Is there already work on this branch? Commits ahead of base, an open PR, human review comments. Fresh branches pass through silently. Anything else gets surfaced and the user decides.

## Inputs

- `worktree`, `branch`, `base_ref`, `repo`, `plan_status`, `plan_path` from walker state

```bash
STATE="$PLAN_DIR/.walk-state.build.json"
WT=$(scripts/walk.sh get --state "$STATE" --key worktree)
BASE_REF=$(scripts/walk.sh get --state "$STATE" --key base_ref)
BRANCH=$(scripts/walk.sh get --state "$STATE" --key branch)
ORG_REPO=$(scripts/walk.sh get --state "$STATE" --key repo)
```

## Steps

1. **Commits ahead of base:**
   ```bash
   AHEAD=$(git -C "$WT" log --oneline "$BASE_REF..HEAD" | wc -l | tr -d ' ')
   ```

2. **Open PR for the branch:**
   ```bash
   PR_JSON=$(gh pr list --repo "$ORG_REPO" --head "$BRANCH" --state open --json number,url,isDraft,reviews,comments 2>/dev/null)
   ```
   If one exists, record `pr_number`, `pr_url`. Check whether a human has reviewed: any review or comment whose author isn't the current user and isn't a bot. Record `human_review_started=true|false`. pr-build never rewrites history anyway, but pr-fix and pr-polish read this later, and the user should know now.

3. **Plan's own Log.** Prior `pr-build:` lines in PLAN.md's Log tell you which tasks already landed. Parse them into `tasks_done` (task numbers).

4. **Decide.**
   - `AHEAD=0`, no PR, `plan_status=approved` → fresh. Route `user_continue` without asking.
   - Otherwise show what exists in a few lines (commit subjects ahead of base, PR URL and draft state, whether human review has started, tasks the Log says are done) and ask with `AskUserQuestion`:
     1. **Continue**: build the remaining tasks on top. If a PR exists, open-pr pushes to it instead of creating one.
     2. **Cancel**: stop without changes.

   A PR whose human review has started gets one extra line in the prompt: "Human review has started on this PR, so anything from here lands as new commits, never a squash." That's already how pr-build works, but it changes what the user might do afterward.

5. **Persist:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key commits_ahead        --value "$AHEAD"
   scripts/walk.sh set --state "$STATE" --key pr_number            --value "<N or empty>"
   scripts/walk.sh set --state "$STATE" --key pr_url               --value "<url or empty>"
   scripts/walk.sh set --state "$STATE" --key human_review_started --value "<true|false>"
   scripts/walk.sh set --state "$STATE" --key tasks_done           --value "<JSON list of task numbers, possibly empty>"
   ```
   Set PLAN.md `Status` to `building` if it was `approved`. Append a Log line: `<date> pr-build: started (<AHEAD> commits already on branch)` only when resuming, so a fresh run's first Log entry is the PR.

## Outputs

- `commits_ahead`, `pr_number`, `pr_url`, `human_review_started`, `tasks_done` in walker state
- PLAN.md `Status` → `building`

## Outgoing edges

- **`user_continue`** → `implement`
- **`user_exit`** → `terminal`

```bash
scripts/walk.sh transition --state "$STATE" --from detect_inflight --to implement --condition user_continue
scripts/walk.sh transition --state "$STATE" --from detect_inflight --to terminal  --condition user_exit
```

## Notes

- **Don't infer "done" from the diff.** The Log is the record of which tasks pr-build completed. Commits the user made by hand are visible in the ahead list but don't tick off tasks. implement re-reads the tree before each task anyway.
- **`gh` failure here is not fatal.** No network → assume no PR, say so, continue. open-pr will find out for real.
