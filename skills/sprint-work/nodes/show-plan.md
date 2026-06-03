# Node: show-plan

Phase 6: render the plan inline so the user can read everything in one place before approving.

## Inputs

- `path_mode`, `context_dir`, `repos`, `repo_mode`, `merge_order`, `worktree_paths`, `recommended_model`, `sprint_md_path` from walker state

```bash
STATE="<path>"
PATH_MODE=$(scripts/walk.sh get --state "$STATE" --key path_mode)
```

## Render based on `path_mode`

### Forgejo paths

1. **Issue summary:** ref (`<owner>/<repo>#<n>`), title, priority, state.
2. **Issue body sections:** Context, Tasks, Files, Notes, Considerations, Success Criteria.
3. **Milestone-level ambient context:** outcome, AC checklist, Open Questions, cross-cutting Considerations.
4. **SPRINT.md-derived context** (when found): Recommended Execution, relevant Surface Areas.
5. **Repo plan:** single-repo or multi-repo + merge order if applicable.
6. **Worktree paths verified.**

For `forgejo-walk`, render all issues' summaries (table form), then expand the first issue's full body. Subsequent issues will have their own per-issue render inside `implement`.

### SPRINT.md path

1. **SPRINT.md sections** most relevant to execution: Implementation Plan (P0 first), Definition of Done, Files Summary.
2. **Recommended Execution.**
3. **Open Questions / Considerations** to keep in mind.
4. **Repo plan + worktree paths verified.**

## Tooling reminder

If `recommended_model` is non-empty and differs from the current session model (which the agent can introspect), surface a note:

```
This sprint's Recommended Execution is "<tier>". You're currently on "<current>".
You can `/model <tier>` and re-invoke if you'd like.
```

## Outputs

- The plan rendered inline. No file changes, no state mutations.

## Outgoing edges

- → `implement` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from show_plan --to implement
```

## Notes

- **Render the full picture, then proceed.** This is a non-blocking render for transparency — there's **no approval gate**. After printing the plan, flow straight into `implement` and execute the whole sprint. (Use `--review` to preview the plan and stop without acting.)
- **Don't ask the user to approve or pick issues.** The run is autonomous; do every issue the target resolved to.
- **For `forgejo-walk`, don't dump every issue's body.** Print the issues table + the first issue's body, then start working. Per-issue bodies are re-rendered in `implement` as each issue comes up.
