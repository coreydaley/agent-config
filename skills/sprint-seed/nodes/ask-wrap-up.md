# Node: ask-wrap-up

Convergence has been sensed. Ask the user whether to wrap up, keep talking, or cancel. The user has final say.

## Inputs

- Walker state (no specific reads needed)

```bash
STATE="$SESSION_DIR/.walk-state.json"
```

## Steps

Use `AskUserQuestion`. Frame it as a single decision:

> "I think we have enough to generate the seed. Anything else you want to talk through, or are we good to synthesize?"
>
> 1. **Wrap up** — synthesize the refined seed and write SEED.md
> 2. **Keep talking** — there's more to surface; back to discussion
> 3. **Cancel** — drop this; don't write anything

## Outputs

- No file changes. State only:
  ```bash
  scripts/walk.sh set --state "$STATE" --key wrap_choice --value "<wrap|continue|cancel>"
  ```

## Outgoing edges

- **`user_wrap_up`** → `synthesize`. User picked option 1.
- **`user_continue`** → `discuss`. User picked option 2.
- **`user_cancel`** → `terminal`. User picked option 3.

Record exactly one:

```bash
# Wrap:
scripts/walk.sh transition --state "$STATE" --from ask_wrap_up --to synthesize --condition user_wrap_up

# Continue:
scripts/walk.sh transition --state "$STATE" --from ask_wrap_up --to discuss --condition user_continue

# Cancel:
scripts/walk.sh transition --state "$STATE" --from ask_wrap_up --to terminal --condition user_cancel
```

## Notes

- **Default to continue.** If the user is ambiguous, prefer keeping the conversation open. The cost of one more exchange is low; the cost of a rushed seed is iteration in `/sprint-plan`.
- **The choice is the confirmation.** Don't add a separate "are you sure?" after.
