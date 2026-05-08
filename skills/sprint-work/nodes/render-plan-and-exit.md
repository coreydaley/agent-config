# Node: render-plan-and-exit

`--review` mode: render the loaded context inline so the user can read the plan, then stop. No implementation, no PR, no ledger changes.

## Inputs

- `path_mode`, `context_dir`, `session_dir`, `recommended_model` from walker state

```bash
STATE="<path>"
PATH_MODE=$(scripts/walk.sh get --state "$STATE" --key path_mode)
```

## Steps

Render based on `path_mode`:

### `sprintmd`

Render the SPRINT.md inline (the user can read it directly in conversation). Don't summarize — give them the full thing.

Append after SPRINT.md:

```
📄 SPRINT.md path: $SPRINT_MD_PATH
```

### `linear-issue`

Render the issue body inline (Context, Tasks, Files, Notes, Considerations, Success Criteria). Then the milestone description if available.

Append:

```
📄 Linear issue: <issue URL>
📄 Milestone: <milestone URL or "no milestone">
📄 SPRINT.md (if found): <path or "not located">
```

### `linear-walk`

Render the milestone description first, then the issue list as a table:

```
| # | ID | Title | Priority | State | Blocked by |
|---|----|-------|----------|-------|------------|
```

Append the same `📄` references as `linear-issue` plus the count of issues to be walked.

## Outputs

- The plan rendered inline. No file changes, no state mutations.

## Outgoing edges

- → `terminal` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from render_plan_and_exit --to terminal
```

## Notes

- **Render the full content inline**, not just paths. The user invoked `--review` to *see* the plan in conversation.
- **Don't ask anything.** `--review` is print-and-exit; the user runs `/sprint-work` without `--review` when they're ready to act.
- **Don't run `/sprints --start`.** No ledger mutation in review mode.
