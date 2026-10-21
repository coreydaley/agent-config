# Node: display

Show the triage table and the scope it was judged against, then ask in plain text. One final message, no tool call after it. The transition to `ask-triage` is recorded next turn.

## Inputs

- `triage_path`, `plan_available`, `plan_dir` from walker state
- `$FIX_DIR/TRIAGE.md`, PLAN.md Scope section

## Steps

1. **Scope anchor first, short.** Three to six lines: what Scope In says this PR delivers, what Scope Out already declined. Without a plan: the PR's stated intent in one sentence and a note that the triage is inferred. This is the "read the ticket scope out loud" step. It goes above the table so the table is read against it.

2. **The table, inline.** Full TRIAGE.md as markdown, including the Diff growth line and the Discuss section.

3. **Path line:**
   ```
   📄 <reports-root>/<org>/<repo>/prs/<key>/fixes/<TS>/TRIAGE.md
   ```

4. **The question**, plain text:

   > Fix or defer? **approve** the table as is, **adjust** (name IDs and the action you want), or **stop** here (the triage stays on disk and `/pr-fix <path>` resumes it later).

   If the Discuss section is non-empty, add: "The Discuss items need an answer before approve."

5. **End the turn.** Nothing after the question.

## Outputs

- The triage is in the conversation

## Outgoing edges

- → `ask-triage` (always, single outgoing edge, recorded next turn)

```bash
scripts/walk.sh transition --state "$STATE" --from display --to ask_triage
```

## Notes

- **Neutral framing.** "Fix or defer?", not "fix everything / fix priority / nothing." The options don't lean.
- **Don't bundle.** Approving the table authorizes the edits and commits. It does not authorize pushing or posting replies. Those have their own gates.
