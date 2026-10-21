# Node: ask-next-action

Interpret the user's answer to the question `display` asked in plain text. **No `AskUserQuestion` here.** The question has been asked. The answer comes in the user's own words.

## Inputs

- `pr_dir`, `mode`, `ownership` from walker state
- The user's reply

```bash
STATE="$PR_DIR/.walk-state.review.json"
MODE=$(scripts/walk.sh get --state "$STATE" --key mode)
OWNERSHIP=$(scripts/walk.sh get --state "$STATE" --key ownership)
```

## Steps

1. **Record the pending `display → ask_next_action` transition.**

2. **Map the reply:**

   | Reply | Ownership | Route |
   |---|---|---|
   | fix, address these, triage, run pr-fix | own | `user_nothing`, after printing `Next: /pr-fix <absolute path to REVIEW.md>` so the handoff is one paste away. This skill doesn't invoke pr-fix itself. It cleans up its worktree and stops. |
   | post, post it, post as a comment, post Medium and above | external, PR mode | `user_post`. A reply that already names a style or a floor pre-answers `ask-post-style`; carry it through rather than re-asking. |
   | any question about a finding, pushback on severity, "what would you change" | any | `user_discuss` |
   | nothing, done, thanks, I'll take it from here | any | `user_nothing` |

   **Post is external-only and PR-mode-only.** An own-mode user who says "post" gets: "This is your PR. Reviews of our own work stay local. `/pr-fix` is the next step." A local-mode user who says "post" gets: "Nothing's on GitHub yet. Push, then re-run against the PR." Neither takes the `user_post` edge.

3. **Ambiguous** → one-line plain-text follow-up. Never resolve toward posting.

## Outputs

- No file or state changes. The transition condition records the choice.

## Outgoing edges

- **`user_post`** → `ask-post-style`. External mode, PR mode, only.
- **`user_discuss`** → `discuss`.
- **`user_nothing`** → `cleanup-worktree`. Done, or handing off to `/pr-fix`.

Record exactly one:

```bash
scripts/walk.sh transition --state "$STATE" --from ask_next_action --to ask_post_style   --condition user_post
scripts/walk.sh transition --state "$STATE" --from ask_next_action --to discuss          --condition user_discuss
scripts/walk.sh transition --state "$STATE" --from ask_next_action --to cleanup_worktree --condition user_nothing
```

## Notes

- **Default to discuss when ambiguous.** Posting is hard to reverse. Discussing is cheap.
- **The choice is the gate.** No "are you sure?" follow-ups.
