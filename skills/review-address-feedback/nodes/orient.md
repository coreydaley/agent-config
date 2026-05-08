# Node: orient

Print a tight orientation summary so the user can decide on a strategy with full context. No user input here — this is a pure print step.

## Inputs

- Walker state (mode, pr_number, pr_head, session_dir, findings_count)
- Findings list (in memory or `$SESSION_DIR/findings.json`)

## Steps

Print 3–6 bullets:

- **Source** — Mode A (`PR #N`) or Mode B (`<path to REVIEW.md>`)
- **Findings count, by severity** (Mode B). For Mode A: total count + author breakdown ("3 from @alice, 2 from @bob") since GitHub comments don't carry severity.
- **PR number, head branch, current CI status** (`gh pr checks $PR_NUMBER` — fine to re-call here, output is short)
- **Session directory** — `$SESSION_DIR`

Skip bullets that don't apply (e.g., severity breakdown is N/A in Mode A).

## Outputs

- Printed orientation summary. No file changes, no state updates.

## Outgoing edges

- → `choose-strategy` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to choose_strategy
```

## Notes

- **Don't ask anything yet.** The user-input gate is `choose-strategy`. Orient is just situational awareness.
- **Don't dump the full finding list.** A summary, not a wall of text. The user will see findings one-by-one (or per-batch) in `address`.
