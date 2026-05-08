# Node: ask-next-action

User has read the review. Ask what to do next.

## Inputs

- The just-displayed REVIEW.md (in user context)

## Steps

```bash
STATE="$PR_DIR/.walk-state.json"
```

Use `AskUserQuestion`:

> What would you like to do next?
>
> 1. Post to GitHub — I'll decide how (comment / request changes / approve / inline)
> 2. Discuss first — talk through the findings before doing anything
> 3. Nothing for now — I've read it, I'll handle next steps myself

## Outgoing edges

- **`user_post`** → `ask-post-style`. User wants to post; we ask the style next.
- **`user_discuss`** → `discuss`. User wants to talk through findings before posting (or before deciding not to).
- **`user_nothing`** → `terminal`. User is done with this run.

Record exactly one based on the answer:

```bash
# Post to GitHub:
scripts/walk.sh transition --state "$STATE" --from ask_next_action --to ask_post_style --condition user_post

# Discuss first:
scripts/walk.sh transition --state "$STATE" --from ask_next_action --to discuss --condition user_discuss

# Nothing for now:
scripts/walk.sh transition --state "$STATE" --from ask_next_action --to terminal --condition user_nothing
```

## Failure modes

- User aborts: treat as `user_nothing` (the safest default — leaves everything as-is).
- Ambiguous answer: ask once for clarification, then default to `user_nothing` if still unclear.
