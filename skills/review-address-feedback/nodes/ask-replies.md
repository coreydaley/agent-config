# Node: ask-replies

After the address pass, ask whether to reply on the PR. The choice is the route.

## Inputs

- `pr_number`, `mode` from walker state
- The in-memory addressed list (or `$SESSION_DIR/addressed.json`)

```bash
STATE="$SESSION_DIR/.walk-state.json"
PR_NUMBER=$(scripts/walk.sh get --state "$STATE" --key pr_number)
MODE=$(scripts/walk.sh get --state "$STATE" --key mode)
```

## Steps

Use `AskUserQuestion`. Offer:

1. **Reply per addressed thread** — for every finding marked `fixed` (or `won't-fix` with a reason worth posting), draft a terse reply. The user reviews / edits / drops drafts before anything is posted.
2. **Single summary comment** — one top-level PR comment listing what was changed, in changelog form. No IDs. Drafted for review first.
3. **Both** — replies + summary.
4. **Nothing** — skip Phase 4 entirely.

If `pr_number` is empty (Mode B without a parseable PR reference), only option 4 is available — and you can skip asking. Just route to `persist` directly with a note: "No PR linked, skipping replies."

Persist the user's choice:

```bash
scripts/walk.sh set --state "$STATE" --key reply_style --value "<per_thread|summary|both|nothing>"
```

## Outputs

- `reply_style` in walker state

## Outgoing edges

- **`user_reply`** → `replies`. User picked options 1, 2, or 3.
- **`user_no_reply`** → `persist`. User picked 4 (or no PR linked in Mode B).

Record exactly one:

```bash
# Replying:
scripts/walk.sh transition --state "$STATE" --from ask_replies --to replies --condition user_reply

# Skipping:
scripts/walk.sh transition --state "$STATE" --from ask_replies --to persist --condition user_no_reply
```

## Notes

- **Default to summary-only** when ambiguous. Single top-level comment is the lowest-noise option that still tells reviewers something happened.
- **The choice is the confirmation.** Don't add an "are you sure?" after the menu.
