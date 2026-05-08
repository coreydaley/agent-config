# Node: create-milestone

Create the milestone in Linear, OR update the existing milestone, OR look up the existing milestone for re-use — driven by `rerun_mode`. **Never touches the project's name or description.**

## Inputs

- `project_id`, `milestone_name`, `plan_path`, `rerun_mode`, `matching_milestone_id`, `session_dir` from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
PROJECT_ID=$(scripts/walk.sh get --state "$STATE" --key project_id)
MILESTONE_NAME=$(scripts/walk.sh get --state "$STATE" --key milestone_name)
PLAN_PATH=$(scripts/walk.sh get --state "$STATE" --key plan_path)
RERUN_MODE=$(scripts/walk.sh get --state "$STATE" --key rerun_mode)
MATCHING_ID=$(scripts/walk.sh get --state "$STATE" --key matching_milestone_id)
```

`rerun_mode` is empty for a fresh run; otherwise one of `create_only_new`, `update`, `start_fresh`.

## Mode dispatch

### Fresh run (rerun_mode is empty) OR `start_fresh`

Create a new milestone:

```bash
linear milestone create \
  --project "$PROJECT_ID" \
  --name "$MILESTONE_NAME" \
  --description "$(cat <<'EOF'
[milestone description from plan]
EOF
)"
```

**`--target-date` is intentionally omitted by default.** SPRINT.md doesn't have a target-date concept, and inventing one (e.g. "two weeks from today") would impose an arbitrary org convention. The user sets a target date manually in Linear when they have a real one.

If the SPRINT.md or seed *does* explicitly state a target date (e.g. "ship by 2026-05-15"), pass it via `--target-date YYYY-MM-DD`. Otherwise omit.

### `update`

Update the existing milestone (description) in place:

```bash
linear milestone update "$MATCHING_ID" \
  --description "$(cat <<'EOF'
[regenerated milestone description]
EOF
)"
```

Don't change the milestone's name during update — name changes are confusing for the team. The user explicitly chose to overwrite the existing milestone, so the existing name stays.

### `create_only_new`

Don't touch the existing milestone. Look up its ID for `create-issues` to attach new issues to:

```bash
# matching_milestone_id is already set from decide-rerun
MILESTONE_ID="$MATCHING_ID"
```

Skip the create/update API call entirely.

## Steps

1. **Dispatch on `rerun_mode`** per the section above.

2. **Capture the milestone ID** (from create output, update confirmation, or `matching_milestone_id`):
   ```bash
   scripts/walk.sh set --state "$STATE" --key milestone_id --value "$MILESTONE_ID"
   ```

3. **Print confirmation:** which milestone (created / updated / re-used) and its URL.

## Project untouched

**Do not touch the project's name, description, or other fields.** The project belongs to the user; we only add (or update) a milestone and issues. This is a hard line.

## Outputs

- A new or updated milestone in Linear (or none, in `create_only_new`)
- `milestone_id` in walker state

## Outgoing edges

- → `create-issues` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from create_milestone --to create_issues
```

## Failure modes

- `linear milestone create` fails because a milestone with that exact name already exists (race against `decide-rerun`'s similarity check) → surface the failure and bail. The existing-milestone match check should have caught it, but if it didn't, don't silently fall back.
- `linear milestone update` fails (auth, permissions) → surface, bail.
- `linear` CLI not authenticated → surface, bail.
