# Node: discuss

Free-form Q&A about the findings. Stay here until the user signals they're done discussing, then loop back to `ask-next-action` so they can pick a next move with their refined thinking.

## Inputs

- `$PR_DIR/REVIEW.md` (user is asking about findings in here)
- The diff, metadata, and intermediate review files in `$PR_DIR/` for reference

## Steps

1. Acknowledge: "Sure, let's talk through it. What do you want to discuss?"

2. Engage. Be honest:
   - If a finding's reasoning is shaky, say so. The user may want to drop it.
   - If the user pushes back on severity, work through it. Don't capitulate just because they're pushing — but if they have a point, agree.
   - If they ask "what would you change?", say what you'd change.

3. **The user signals "done"** when they say something like:
   - "OK, let's post"
   - "Got it, I'll handle the rest"
   - "Move on" / "What's next?" / "OK I'm ready"
   - Or simply ask about the post options — that's a strong signal.

4. **Don't loop indefinitely.** If the user has been quiet or the conversation has resolved each finding they raised, prompt: "Anything else, or ready to pick a next action?"

## Outputs

- No file changes. The user has refined context in their own head; the REVIEW.md stays the original review.

## Outgoing edges

- → `ask-next-action` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from discuss --to ask_next_action --condition discussion_done
```

## Notes

- **Don't update REVIEW.md from the discussion.** The artifact stays the original review. If they want findings revised, that's a re-review (re-run the skill).
- **Don't pre-commit to posting** during discussion. The post action is gated by `ask-next-action` returning `user_post`.
