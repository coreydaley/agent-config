# Node: handoff

Print the path, the seed, and the exact next command. Single inline output so the user has everything in one place.

## Inputs

- `session_dir`, `seed_text` (or read SEED.md back), `prd_status`, `prd_delta_path` from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
PRD_STATUS=$(scripts/walk.sh get --state "$STATE" --key prd_status)
PRD_DELTA_PATH=$(scripts/walk.sh get --state "$STATE" --key prd_delta_path)
```

## Steps

Print, in order:

1. **Path to the SEED.md.**
   ```
   SEED.md written: $SESSION_DIR/SEED.md
   ```

2. **The synthesized seed prompt** — copy of what's at the top of SEED.md (the 2-3 paragraphs from `synthesize`). Print inline so the user can read it without opening the file.

3. **The exact next command:**
   ```
   /sprint-plan $SESSION_DIR/SEED.md
   ```

4. **PRD delta (only when `prd_status` is `rescope_proposed`).** Print the drafted change and point the user at the wiki — applying it is their deliberate act, not something this skill did:
   ```
   ⚠ This seed prompted a proposed PRD change: $PRD_DELTA_PATH
     Review it and apply it to the PRD wiki page yourself if you agree:
       <owner>/<repo> wiki → "PRD"
     (sprint-seed drafted it but did NOT edit the wiki.)
   ```

That's it. No additional commentary, no closing summary, no "let me know if you have questions."

## Outputs

- Inline printed output to the user. No file changes.

## Outgoing edges

- → `terminal` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from handoff --to terminal
```

## Notes

- **Don't auto-invoke `/sprint-plan`.** That's the user's call. They may want to edit SEED.md first or revisit the discussion in their head before planning.
- **Don't suggest alternatives** ("you could also..."). The next step is `/sprint-plan`, full stop.
- **Don't recap the discussion.** The user just lived it; SEED.md captures what matters.
