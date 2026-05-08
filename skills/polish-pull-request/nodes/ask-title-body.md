# Node: ask-title-body

Prompt 1: title, body, and thread resolutions. Per-thread ambiguous-thread questions are inline within this gate (one user-input phase, multiple internal AskUserQuestion calls).

## Inputs

- `proposals_path` from walker state — for the title/body/thread proposals
- The Ambiguous threads list from `analyze`

```bash
STATE="<path>"
PROPOSALS=$(scripts/walk.sh get --state "$STATE" --key proposals_path)
```

## Steps

1. **Main prompt.** Use `AskUserQuestion`:

   > "Title, body, and thread resolutions for these PRs:
   > 
   > 1. **Apply all** — title, body, and resolutions as proposed
   > 2. **Pick what to apply** — per-PR, per-action selection
   > 3. **Edit first** — open conversation to iterate before applying
   > 4. **Skip title/body/threads** — leave them as-is, but continue to cleanup
   > 5. **Cancel** — stop here, no changes to anything"

2. **For "Pick what to apply"**, walk through each proposal interactively (one AskUserQuestion per item, or a multi-question form). For each: apply / skip. Record the per-PR decisions in walker state:
   ```bash
   scripts/walk.sh set --state "$STATE" --key tbt_decisions --value "<JSON>"
   ```

3. **For "Edit first"** route via `user_edit` to `discuss-tbt`. Don't persist any decisions yet — they get refined in the discussion.

4. **For ambiguous threads**, regardless of the main answer above (unless the user picked Cancel), ask one-by-one:
   > "Thread at `<path>:<line>`: '<comment summary>'. Code was touched in `<SHA>`, but it's unclear whether the concern is fully addressed.
   > 
   > 1. **Resolve** — mark the thread resolved
   > 2. **Leave open** — the concern may still apply
   > 3. **Skip** — don't touch this thread"

   Persist the per-thread decisions:
   ```bash
   scripts/walk.sh set --state "$STATE" --key ambiguous_decisions --value "<JSON>"
   ```

   Skip these sub-questions if the main answer was "Skip title/body/threads" or "Edit first."

## Outputs

- `tbt_decisions`, `ambiguous_decisions` in walker state

## Outgoing edges

- **`user_edit`** → `discuss-tbt`. User wants to iterate.
- **`user_apply`** → `apply-title-body`. User picked Apply all or Pick.
- **`user_skip_tbt`** → `ask-cleanup`. User picked "Skip title/body/threads" — continue to cleanup.
- **`user_cancel`** → `terminal`. User picked Cancel.

Record exactly one:

```bash
# Apply (after Apply all or Pick):
scripts/walk.sh transition --state "$STATE" --from ask_title_body --to apply_title_body --condition user_apply

# Edit/iterate:
scripts/walk.sh transition --state "$STATE" --from ask_title_body --to discuss_tbt --condition user_edit

# Skip TBT but continue:
scripts/walk.sh transition --state "$STATE" --from ask_title_body --to ask_cleanup --condition user_skip_tbt

# Cancel everything:
scripts/walk.sh transition --state "$STATE" --from ask_title_body --to terminal --condition user_cancel
```

## Notes

- **Default to "Edit first" when ambiguous.** Discussing is cheap; applying changes to a public PR title/body is more expensive to undo.
- **The main choice is the confirmation.** Don't add an "are you sure?" prompt after.
- **Cancel here exits without touching anything.** No worktree state, no GitHub mutations.
