# Node: ask-per-match-decisions

Match-existing surfaced one or more matches. Walk each one and ask the user how to handle it. The decisions feed `create-issues`.

## Inputs

- `plan_path`, `match_count` from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
PLAN_PATH=$(scripts/walk.sh get --state "$STATE" --key plan_path)
```

## Steps

For each match in `$PLAN_PATH`'s `matches` array, ask via `AskUserQuestion`:

> Match: proposed "<proposed_title>"
>        ↔ existing <existing_id> "<existing_title>" (sim <score>)
>
> 1. **Skip** — already exists; don't create the new one
> 2. **Augment** — don't create new; post a comment on the existing issue with milestone context
> 3. **Replace** — create new (in the new milestone), close existing as duplicate
> 4. **Link as related** — create new, add Linear "relates to" link
> 5. **Create anyway** — create both; no relationship

Persist each decision in `$PLAN_PATH` so `create-issues` reads them:

```json
{
  "proposed_title": "...",
  "existing_id": "CON-1148",
  "decision": "augment | skip | replace | link | create"
}
```

After all matches are decided, transition.

## Cancel handling

If the user says "cancel" mid-walk (or any equivalent abort signal), route to `terminal` via `user_cancel`. **No partial creation** — Linear stays untouched until the full set of decisions is in.

## Outputs

- Decisions persisted in `$PLAN_PATH`

## Outgoing edges

- **`decisions_made`** → `create-milestone`. All matches decided.
- **`user_cancel`** → `terminal`. User aborted mid-walk.

Record exactly one:

```bash
# All decisions captured — proceed to create:
scripts/walk.sh transition --state "$STATE" --from ask_per_match_decisions --to create_milestone --condition decisions_made

# Cancel — Linear untouched:
scripts/walk.sh transition --state "$STATE" --from ask_per_match_decisions --to terminal --condition user_cancel
```

## Notes

- **Default to "Skip" when ambiguous.** If the user is unsure about a specific match, skipping (don't create the new one) is the safest — the existing issue is already there, the team can handle it.
- **The decision per match is the confirmation** for that match's action. No global "are you sure?" after the walk.
- **Existing issues that don't match anything proposed** are left untouched. This node only walks matches.
