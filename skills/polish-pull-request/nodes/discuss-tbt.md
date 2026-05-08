# Node: discuss-tbt

User picked "Edit first" on Prompt 1. Iterate on the proposed title/body/threads in conversation until the user is ready to apply (or back out).

## Inputs

- `proposals_path` from walker state — the in-flight proposals to discuss
- The Ambiguous threads list

## Steps

1. **Acknowledge:** "Sure, let's tune them. What do you want to change?"

2. **Engage.** The user may push back on:
   - The proposed title (different framing, different Linear ID handling)
   - The proposed body rewrite (different Summary, different test plan)
   - Which threads to resolve
   - Whether to mark a thread resolved at all

   Update the in-memory proposal as you go. If the user changes their mind on multiple things, keep updating the same proposals object — don't fork it.

3. **Persist updates** to the proposals sidecar so `apply-title-body` reads the current version:
   ```bash
   echo "$UPDATED_PROPOSALS_JSON" > "$PROPOSALS"
   ```

4. **The user signals "done"** when they say something like:
   - "OK, apply it"
   - "Looks good, ship it"
   - "Move on" / "What's next?"

5. **Don't loop forever.** If the conversation has resolved each open question, prompt: "Anything else, or ready to apply?"

## Outputs

- Updated `$PROPOSALS` JSON

## Outgoing edges

- → `ask-title-body` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from discuss_tbt --to ask_title_body --condition discussion_done
```

## Notes

- **Always loop back to ask-title-body**, not directly to apply. The user makes the apply call from there with the updated proposals.
- **Don't apply mid-discussion.** That's `apply-title-body`'s job.
- **Don't touch the cleanup proposals here.** Those are gated by Prompt 2 (`ask-cleanup`).
