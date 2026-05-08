# Node: show-plan

Phase 6: render the plan inline so the user can read everything in one place before approving.

## Inputs

- `path_mode`, `context_dir`, `repos`, `repo_mode`, `merge_order`, `worktree_paths`, `recommended_model`, `sprint_md_path` from walker state

```bash
STATE="<path>"
PATH_MODE=$(scripts/walk.sh get --state "$STATE" --key path_mode)
```

## Render based on `path_mode`

### Linear paths

1. **Issue summary:** ID, title, priority, state.
2. **Issue body sections:** Context, Tasks, Files, Notes, Considerations, Success Criteria.
3. **Milestone-level ambient context:** outcome, AC checklist, Open Questions, cross-cutting Considerations.
4. **SPRINT.md-derived context** (when found): Recommended Execution, relevant Surface Areas.
5. **Repo plan:** single-repo or multi-repo + merge order if applicable.
6. **Worktree paths verified.**

For `linear-walk`, render all issues' summaries (table form), then expand the first issue's full body. Subsequent issues will have their own per-issue render inside `implement`.

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

- → `ask-approval` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from show_plan --to ask_approval
```

## Notes

- **Render the full picture.** The user is going to be asked to approve in the next node; they need the full context here.
- **Don't ask anything yet.** The user-input gate is `ask-approval`.
- **For `linear-walk`, don't dump every issue's body.** Issues table + first issue's body. The user can ask for more depth in `discuss-plan`.
