# Node: handoff

Print where the feature landed and the **next step** — but don't execute it. The
user drives what happens next.

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
Feature filed: <issue_url>   (<issue_number>, labels: <applied_labels>, assigned to you)
Working copy:  $SESSION_DIR/FEATURE.md   (ephemeral — the issue is the record)

Next (your call — nothing runs automatically):
  /feature-plan <issue_url>   →  plan it and create the linked sub-issues
  /feature-work <issue_url>   →  build it autonomously, then finish together
```

The feature issue is now a tracked backlog item. You can plan it now, or leave it
and come back — `/feature-plan` reads it whenever you're ready.

### On failure (`create_status` = `failed`)

```
⚠ The issue wasn't filed (see the error above).
Your work is safe in the local draft:  $SESSION_DIR/FEATURE.md
Retry: re-run /feature-create, or file it by hand with `tea issues create`.
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

- **Print the chain, don't run it.** This skill stops at the filed issue; the
  user invokes the next step when ready.
- **Be honest about failure.** If `create-issue` couldn't file, say so and point
  at the local draft — never imply an issue exists.
- **Don't duplicate downstream work.** No planning, no sub-issues here — that's
  `/feature-plan`, surfaced as the next step only.
