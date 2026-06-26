# Node: ask-create

User-input gate. The body has been rendered and a priority chosen. Creating the
issue files a GitHub issue (a mutation), so confirm — and name the exact labels
that will be applied so there are no surprises.

## Inputs

- The rendered body from `draft`; `org_repo`, `issue_type`, `issue_title`, `priority`

```bash
STATE="$SESSION_DIR/.walk-state.json"
ORG_REPO=$(scripts/walk.sh get --state "$STATE" --key org_repo)
ISSUE_TYPE=$(scripts/walk.sh get --state "$STATE" --key issue_type)
PRIORITY=$(scripts/walk.sh get --state "$STATE" --key priority)
```

## Steps

Offer three choices, naming the labels explicitly:

```
Ready to file this in <org/repo>?
  1. Create      — open a self-assigned issue, labelled `type/<type>` + `priority/<p>`.
  2. Revise more — back to the discussion to adjust the body (or change the type).
  3. Cancel      — keep the local draft; file nothing.

(No size/* or deferred/* labels are set — those are work-time / sweep decisions.)
```

Default conservative when ambiguous: prefer **revise more** (`user_revise`) over
filing. Cheap to keep editing; the issue is the committal act.

## Outgoing edges

- **`user_create`** → `create-issue`. File it.
- **`user_revise`** → `gather`. Back to refining the body (or re-running the type
  template if the user wants a different type — re-set `issue_type` in `gather`).
- **`user_cancel`** → `terminal`. Local draft kept; GitHub untouched.

Record exactly one:

```bash
scripts/walk.sh transition --state "$STATE" --from ask_create --to create_issue --condition user_create
# or
scripts/walk.sh transition --state "$STATE" --from ask_create --to gather       --condition user_revise
# or
scripts/walk.sh transition --state "$STATE" --from ask_create --to terminal     --condition user_cancel
```

## Notes

- **Creating the issue is the only mutation in this skill.** Up to here everything
  is local + read-only against GitHub. Treat the confirmation seriously.
- **Cancel is safe.** The working draft stays at `$SESSION_DIR/ISSUE.md`; the user
  can re-run later or file it by hand.
- **Revise can change the type.** If the user realizes it's an enhancement, not a
  bug, route to `gather` and re-set `issue_type` there before re-drafting.
