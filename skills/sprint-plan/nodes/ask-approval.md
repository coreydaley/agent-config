# Node: ask-approval

Phase 9 Step 5: present the final plan to the user, ask for approval / revision / cancel.

## Inputs

- `sprint_md_path`, `reviews_run`, `recommended_tier`, `recommended_model` from walker state

```bash
STATE="<path>"
SPRINT_MD=$(scripts/walk.sh get --state "$STATE" --key sprint_md_path)
```

## Steps

Render inline, in this order:

1. **Review findings summary** — bullets of what was incorporated from each enabled Phase 8 review and what was explicitly rejected, with brief reasoning for rejections.

2. **Full sprint document rendered inline** — print the entire contents of `$SESSION_DIR/SPRINT.md` directly so the user can read what they're about to approve. Render as markdown so the in-conversation rendering is readable.

3. **Recommended Execution block** — repeat the Recommended Execution section last and prominently. Tier, `/model` command, `/sprint-work` command, rationale.

4. **Approval prompt.** Use `AskUserQuestion`:

   > 1. **Approve & register** — register the sprint in the ledger; you can run `/sprint-work` next
   > 2. **Request changes** — let's iterate on the plan first
   > 3. **Cancel** — stop without registering

Persist:

```bash
scripts/walk.sh set --state "$STATE" --key approval_choice --value "<approve|revise|cancel>"
```

## Outputs

- The plan rendered inline. Walker state with the user's choice.

## Outgoing edges

- **`user_approve`** → `register`. Register the sprint and exit cleanly.
- **`user_revise`** → `discuss-finalize`. Iterate, then come back here.
- **`user_cancel`** → `terminal`. Don't register; the SPRINT.md stays on disk for the user to use as they like.

Record exactly one:

```bash
# Approve:
scripts/walk.sh transition --state "$STATE" --from ask_approval --to register --condition user_approve

# Revise:
scripts/walk.sh transition --state "$STATE" --from ask_approval --to discuss_finalize --condition user_revise

# Cancel:
scripts/walk.sh transition --state "$STATE" --from ask_approval --to terminal --condition user_cancel
```

## Notes

- **Render the full document inline.** The user is approving content they should have just read — don't ask them to open the file separately.
- **The Recommended Execution block goes last.** That's the actionable next step; it should be the final thing in the user's eye before they decide.
- **The choice is the gate.** No follow-up "are you sure?".
- **Cancel doesn't delete SPRINT.md.** It stays on disk; the user can use it manually if they want, just won't be in the ledger.
