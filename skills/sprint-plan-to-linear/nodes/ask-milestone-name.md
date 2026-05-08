# Node: ask-milestone-name

Derive a completion-framed milestone name from the SPRINT.md title (rename detection), then ask the user to confirm.

## Inputs

- `sprint_title`, `parsed_sprint_path` from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
SPRINT_TITLE=$(scripts/walk.sh get --state "$STATE" --key sprint_title)
```

## Activity-framing rename detection

The milestone gets a descriptive, completion-framed name with no sprint-tracking artifacts. Detect activity framing:

- **Imperative-verb start** (Add, Implement, Create, Update, Migrate, Refactor, Build, etc.) → propose a completion-framed alternative.

  ```
  Bare title:     Add full tag support to top 10 most popular images
  Proposed:       Top 10 most popular images support full tag
  ```

- **Already completion-framed** (subject + active verb describing end state, e.g. "X supports Y") → propose as-is, but still let the user override.

The milestone name **must not contain the word "sprint"** or any sprint number.

## Steps

1. **Run rename detection** on `sprint_title`. Record:
   ```bash
   scripts/walk.sh set --state "$STATE" --key bare_title     --value "<original>"
   scripts/walk.sh set --state "$STATE" --key proposed_title --value "<rewritten or same>"
   ```

2. **Ask the user.** Use `AskUserQuestion`:

   > Milestone name:
   >
   > 1. **Keep current bare title** — `<bare>`
   > 2. **Use proposed completion-framed** — `<proposed>` (option 2 hidden if bare and proposed are identical)
   > 3. **Custom** — enter a different name
   > 4. **Cancel** — stop here

3. **Persist the chosen name:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key milestone_name --value "<chosen>"
   ```

4. **Validate the chosen name** doesn't contain "sprint" or a sprint number prefix. If it does, point that out and re-ask.

## Outputs

- `bare_title`, `proposed_title`, `milestone_name` in walker state

## Outgoing edges

- **`name_chosen`** → `decide-rerun`. User picked a name.
- **`user_cancel`** → `terminal`. User backed out.

Record exactly one:

```bash
# Name chosen:
scripts/walk.sh transition --state "$STATE" --from ask_milestone_name --to decide_rerun --condition name_chosen

# Cancel:
scripts/walk.sh transition --state "$STATE" --from ask_milestone_name --to terminal --condition user_cancel
```

## Notes

- **Default to "use proposed"** when ambiguous and the proposed differs from the bare. Completion-framing is the user's stated preference and mirrors the project description style.
- **The choice is the confirmation.** No follow-up "are you sure?" prompts.
