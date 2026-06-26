# Node: handoff

Print where the issue landed. There is **no pipeline next-step** — this is the
single-issue track; the issue goes on your board and you pick it up when ready.

## Inputs

- `create_status`, `issue_url`, `issue_number`, `applied_labels`, `session_dir`
  from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
CREATE_STATUS=$(scripts/walk.sh get --state "$STATE" --key create_status)
ISSUE_URL=$(scripts/walk.sh get --state "$STATE" --key issue_url)
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
```

## Steps

### On success (`create_status` = `created`)

```
Issue filed: <issue_url>   (<issue_number>, labels: <applied_labels>, assigned to you)
Working copy: $SESSION_DIR/ISSUE.md   (ephemeral — the issue is the record)

It's on your board. Pick it up whenever; nothing runs automatically.
```

### On failure (`create_status` = `failed`)

```
⚠ The issue wasn't filed (see the error above).
Your work is safe in the local draft:  $SESSION_DIR/ISSUE.md
Retry: re-run /issue-create, or file it by hand with `gh issue create`.
```

That's it — no closing summary, no "let me know if you have questions."

## Outputs

- Inline printed output. No file changes, **nothing executed**.

## Outgoing edges

- → `terminal` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from handoff --to terminal
```

## Notes

- **No plan/work follow-on.** That's the feature track (`/feature-plan`,
  `/feature-work`). An issue here is self-contained — don't print a pipeline.
- **Be honest about failure.** If `create-issue` couldn't file, say so and point at
  the local draft — never imply an issue exists.
