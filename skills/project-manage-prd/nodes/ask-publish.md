# Node: ask-publish

User-input gate. The assembled PRD has been rendered inline. Publishing writes
to the repo's wiki (a mutation), so confirm before doing it.

## Inputs

- The rendered PRD from `draft`; `prd_mode`, `org_repo`

```bash
STATE="$SESSION_DIR/.walk-state.json"
PRD_MODE=$(scripts/walk.sh get --state "$STATE" --key prd_mode)
ORG_REPO=$(scripts/walk.sh get --state "$STATE" --key org_repo)
```

## Steps

Offer three choices. Phrase the publish action by mode so the user knows
whether they're creating or overwriting:

```
Ready to write this to the <org/repo> wiki (page "PRD")?
  1. Publish      — [create the PRD page | UPDATE the existing PRD page].
  2. Revise more  — back to the discussion to adjust it.
  3. Cancel       — keep the local draft; write nothing to the wiki.
```

In **revise** mode, be explicit that publishing **overwrites** the current wiki
PRD with the new version. (Forgejo keeps wiki page history, so the prior version
isn't lost — mention that if the user hesitates.)

Default conservative when ambiguous: prefer **revise more** (`user_revise`) over
publishing. Cheap to keep editing; the wiki write is the committal act.

## Outgoing edges

- **`user_publish`** → `publish`. Write it to the wiki.
- **`user_revise`** → `discuss`. Back to refining.
- **`user_cancel`** → `terminal`. Local draft kept; wiki untouched.

Record exactly one:

```bash
scripts/walk.sh transition --state "$STATE" --from ask_publish --to publish  --condition user_publish
# or
scripts/walk.sh transition --state "$STATE" --from ask_publish --to discuss  --condition user_revise
# or
scripts/walk.sh transition --state "$STATE" --from ask_publish --to terminal --condition user_cancel
```

## Notes

- **The wiki write is the only mutation in this skill.** Up to here everything is
  local + read-only against Forgejo. Treat the publish confirmation seriously.
- **Cancel is safe.** The working draft stays at `$SESSION_DIR/PRD.md`; the user
  can re-run later or apply it by hand.
