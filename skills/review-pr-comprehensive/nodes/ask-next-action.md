# Node: ask-next-action

User has read the inline REVIEW.md. Ask what they want to do next, keeping it open-ended (not a checklist of GitHub mechanics).

## Inputs

- `pr_dir` from walker state

```bash
STATE="$PR_DIR/.walk-state.json"
```

## Steps

Use `AskUserQuestion`. Three options:

1. **Post to GitHub** — I'll decide how (comment, approval, request-changes, inline)
2. **Discuss first** — talk through the findings before doing anything
3. **Nothing for now** — I've read it, I'll handle next steps myself

Persist the choice for downstream nodes:

```bash
scripts/walk.sh set --state "$STATE" --key next_action --value "<post|discuss|nothing>"
```

## Outputs

- `next_action` in walker state

## Outgoing edges

- **`user_post`** → `ask-post-style`. User picked "Post to GitHub."
- **`user_discuss`** → `discuss`. User wants to talk first.
- **`user_nothing`** → `cleanup-worktree`. User is done.

Record exactly one:

```bash
# Post:
scripts/walk.sh transition --state "$STATE" --from ask_next_action --to ask_post_style --condition user_post

# Discuss:
scripts/walk.sh transition --state "$STATE" --from ask_next_action --to discuss --condition user_discuss

# Nothing:
scripts/walk.sh transition --state "$STATE" --from ask_next_action --to cleanup_worktree --condition user_nothing
```

## Notes

- **Default to "discuss" when ambiguous.** Posting to GitHub is irreversible (or hard to reverse without leaving traces); discussing is cheap. The cost of one extra exchange is low; the cost of a mistakenly posted review is real.
- **The choice is the gate.** Don't add "are you sure?" follow-ups.
