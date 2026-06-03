# Node: handoff

Print where the PRD landed and the natural next step. Single inline output.

## Inputs

- `publish_action`, `prd_url`, `org_repo`, `session_dir` from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
ACTION=$(scripts/walk.sh get --state "$STATE" --key publish_action)
PRD_URL=$(scripts/walk.sh get --state "$STATE" --key prd_url)
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
```

## Steps

### On success (`publish_action` = `created` or `updated`)

```
PRD <created|updated>: <prd_url>
Working copy:          $SESSION_DIR/PRD.md

Next:
  /sprint-seed   — plan the next sprint against this PRD (it auto-reads it).
```

`/sprint-seed` auto-discovers this exact page, so the PRD immediately starts
steering planning — that's the payoff.

### On failure (`publish_action` = `failed`)

```
⚠ The wiki write didn't land (see the error above).
Your work is safe in the local draft:  $SESSION_DIR/PRD.md
Retry: re-run /project-create-prd (revise mode will pick up where the wiki is),
or paste the draft into the <org/repo> wiki "PRD" page by hand.
```

That's it — no closing summary, no "let me know if you have questions."

## Outputs

- Inline printed output. No file changes.

## Outgoing edges

- → `terminal` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from handoff --to terminal
```

## Notes

- **Don't re-print the whole PRD.** `draft` already rendered it; point at the URL.
- **Be honest about failure.** If `publish` couldn't write the wiki, say so and
  point at the local draft — never imply success.
