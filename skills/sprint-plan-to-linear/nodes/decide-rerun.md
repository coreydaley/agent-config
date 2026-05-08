# Node: decide-rerun

Pure decision: is this a re-run of `/sprint-plan-to-linear` against the same SPRINT.md? Two triggers:

1. `$SESSION_DIR/LINEAR.md` already exists.
2. The chosen `milestone_name` has high name similarity to an existing milestone in the project.

If either trigger fires → route to `ask-rerun-mode`. Otherwise → straight to `build-plan`.

## Inputs

- `session_dir`, `milestone_name`, `milestones_path` from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
MILESTONE_NAME=$(scripts/walk.sh get --state "$STATE" --key milestone_name)
MILESTONES_PATH=$(scripts/walk.sh get --state "$STATE" --key milestones_path)
```

## Steps

1. **Check trigger 1 — LINEAR.md exists:**
   ```bash
   if [ -f "$SESSION_DIR/LINEAR.md" ]; then
     LINEAR_MD_EXISTS=true
   fi
   ```

2. **Check trigger 2 — milestone name similarity.** Score the chosen `milestone_name` against each existing milestone's name in `$MILESTONES_PATH`. Use lowercased Jaccard token similarity (cheap, fuzzy). Threshold: ≥0.7 → likely the same milestone.

3. **Decide:**
   - Either trigger fires → `rerun_detected`. Persist what we found:
     ```bash
     scripts/walk.sh set --state "$STATE" --key linear_md_exists --value "<true|false>"
     scripts/walk.sh set --state "$STATE" --key matching_milestone_id --value "<id or empty>"
     scripts/walk.sh set --state "$STATE" --key matching_milestone_name --value "<name or empty>"
     ```
   - Neither fires → `no_rerun`.

## Outputs

- `linear_md_exists`, `matching_milestone_id`, `matching_milestone_name` in walker state

## Outgoing edges

- **`rerun_detected`** → `ask-rerun-mode`. At least one trigger fired.
- **`no_rerun`** → `build-plan`. Clean slate — proceed.

Record exactly one:

```bash
# Re-run detected:
scripts/walk.sh transition --state "$STATE" --from decide_rerun --to ask_rerun_mode --condition rerun_detected

# Clean slate:
scripts/walk.sh transition --state "$STATE" --from decide_rerun --to build_plan --condition no_rerun
```

## Notes

- **Don't ask the user here.** Pure decision; user gate is `ask-rerun-mode`.
- **Both triggers are surfaced together** in `ask-rerun-mode` so the user sees the full picture (LINEAR.md + similar milestone) when deciding what to do.
- **Similarity threshold is conservative.** False positives (asking when the user actually wanted a fresh milestone with a similar name) cost only one extra prompt; false negatives (creating a duplicate milestone) are harder to undo.
