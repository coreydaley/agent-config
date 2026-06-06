# Node: ask-create

User-input gate. The issue body has been rendered inline. Creating it files a
Forgejo issue (a mutation), so confirm before doing it.

## Inputs

- The rendered body from `draft`; `org_repo`, `issue_title`, `priority`

```bash
STATE="$SESSION_DIR/.walk-state.json"
ORG_REPO=$(scripts/walk.sh get --state "$STATE" --key org_repo)
PRIORITY=$(scripts/walk.sh get --state "$STATE" --key priority)
```

## Steps

Offer three choices. Name the labels that will be applied so there are no
surprises:

```
Ready to file this as an issue in <org/repo>?
  1. Create      — open a self-assigned issue, labelled `feature`[ + priority/<p>].
  2. Revise more — back to the discussion to adjust the body.
  3. Cancel      — keep the local draft; file nothing.
```

If `readiness-check` rendered a verdict, factor it in — surface its blockers /
majors alongside the choices so the decision is informed. A `Needs revision` /
`Not ready` verdict is a nudge toward **revise more**, not a hard block.

Default conservative when ambiguous: prefer **revise more** (`user_revise`) over
filing. Cheap to keep editing; the issue is the committal act.

## Outgoing edges

- **`user_create`** → `create-issue`. File it.
- **`user_revise`** → `discuss`. Back to refining.
- **`user_cancel`** → `terminal`. Local draft kept; Forgejo untouched.

Record exactly one:

```bash
scripts/walk.sh transition --state "$STATE" --from ask_create --to create_issue --condition user_create
# or
scripts/walk.sh transition --state "$STATE" --from ask_create --to discuss      --condition user_revise
# or
scripts/walk.sh transition --state "$STATE" --from ask_create --to terminal     --condition user_cancel
```

## Notes

- **Creating the issue is the only mutation in this skill.** Up to here
  everything is local + read-only against Forgejo. Treat the confirmation
  seriously.
- **Cancel is safe.** The working draft stays at `$SESSION_DIR/FEATURE.md`; the
  user can re-run later or file it by hand.
