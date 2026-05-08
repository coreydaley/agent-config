# Node: ask-rerun-mode

A re-run was detected. Surface the evidence and ask the user how to proceed.

## Inputs

- `linear_md_exists`, `matching_milestone_id`, `matching_milestone_name`, `milestone_name` from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
LINEAR_MD_EXISTS=$(scripts/walk.sh get --state "$STATE" --key linear_md_exists)
MATCHING_ID=$(scripts/walk.sh get --state "$STATE" --key matching_milestone_id)
MATCHING_NAME=$(scripts/walk.sh get --state "$STATE" --key matching_milestone_name)
MILESTONE_NAME=$(scripts/walk.sh get --state "$STATE" --key milestone_name)
```

## Steps

1. **Surface the evidence first:**

   ```
   Re-run detected:
   ```
   Then list whichever applies:
   ```
   - LINEAR.md exists at $SESSION_DIR/LINEAR.md
     (this SPRINT.md has been planned-to-Linear before)
   - Milestone "<MATCHING_NAME>" already exists in this project
     (high similarity to chosen "<MILESTONE_NAME>")
   ```

2. **Ask via `AskUserQuestion`:**

   > 1. **Create only new issues** *(default)* — leave the existing milestone and its issues alone; only create issues for SPRINT.md sections that weren't created before. Milestone description left as-is.
   > 2. **Update existing milestone and issues** — overwrite milestone description and issue descriptions with regenerated content. Risks blowing away comments and team edits — flag this clearly.
   > 3. **Start fresh** — create a new milestone with a disambiguated name (e.g. add a date suffix); ignore the prior LINEAR.md.
   > 4. **Cancel** — stop here.

3. **Persist the choice:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key rerun_mode --value "<create_only_new|update|start_fresh>"
   ```

4. **For "start fresh"** — propose a disambiguated `milestone_name` (e.g. append `(2026-05-07)` or similar) and update walker state:
   ```bash
   scripts/walk.sh set --state "$STATE" --key milestone_name --value "<disambiguated>"
   ```

5. **For "update"** — flag explicitly that descriptions will be overwritten, possibly losing comments / manual edits. Get explicit confirmation:
   > "Confirm: this will overwrite the existing milestone description and any issue descriptions in the milestone. Comments are not affected. Proceed?"

   If the user backs out at this confirmation, route to `terminal` via `user_cancel`.

## Outputs

- `rerun_mode` in walker state
- Possibly updated `milestone_name` (start-fresh case)

## Outgoing edges

- **`mode_chosen`** → `build-plan`. User picked options 1-3.
- **`user_cancel`** → `terminal`. User picked option 4 or backed out of update confirmation.

Record exactly one:

```bash
# Mode chosen — proceed to build the plan:
scripts/walk.sh transition --state "$STATE" --from ask_rerun_mode --to build_plan --condition mode_chosen

# Cancel:
scripts/walk.sh transition --state "$STATE" --from ask_rerun_mode --to terminal --condition user_cancel
```

## Notes

- **Default is "create only new"** because Linear issue and milestone descriptions accumulate review comments and team edits we shouldn't clobber.
- **Update mode warrants the explicit confirm** because it can destroy work the team did directly in Linear.
- **The mode flows downstream** to `create-milestone` and `create-issues`, which adapt their behavior. No new graph nodes for each mode — the dispatch is internal.
