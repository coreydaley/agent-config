# Node: show-plan

Render the plan inline so the user can read the whole picture in one place before the autonomous run starts. Non-blocking — there's no approval gate.

## Inputs

- `feature_ref`, `feature_title`, `feature_branch`, `context_dir`, `repos`, `repo_mode`, `worktree_paths`, `active_subissue_ids`, `shipped_subissue_ids` from walker state

```bash
STATE="<path>"
```

## Render

1. **Feature summary:** ref (`<owner>/<repo>#<n>`), title, the `feature/<slug>` branch the work lands on.
2. **Sub-issue work list** (table form): each active sub-issue's ref (`<owner>/<repo>#<m>`), title, priority, in dependency order. Note any **resumed/skipped** sub-issues (already shipped a commit on the branch) so the user sees the resume is working.
3. **Feature-level ambient context:** the feature issue's intent / acceptance criteria — what the sub-issues add up to.
4. **Repo plan:** single-repo or multi-repo + commit order if applicable. The base each feature branch is cut from (per-repo default branch).
5. **Worktree paths verified** (the `feature/<slug>` worktree per repo).
6. **Then expand the first active sub-issue's full body** (Tasks, Files, Success Criteria). Subsequent sub-issues get their own per-issue render inside `implement`.

## Outputs

- The plan rendered inline. No file changes, no state mutations.

## Outgoing edges

- → `implement` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from show_plan --to implement
```

## Notes

- **Render the full picture, then proceed.** This is a non-blocking render for transparency — there's **no approval gate**. After printing the plan, flow straight into `implement` and build every sub-issue.
- **Don't ask the user to approve or pick sub-issues.** The run is autonomous; do every sub-issue the feature resolved to.
- **Don't dump every sub-issue's body.** Print the work-list table + the first active sub-issue's body, then start working. Per-sub-issue bodies are re-rendered in `implement` as each comes up.
- **Remind the user the merge is theirs.** A one-line note that the commits land on `feature/<slug>` and the sub-issues close when they merge sets expectations before the run.
