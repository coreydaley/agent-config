# Node: ask-polish

Interpret the user's reply to the proposals. No `AskUserQuestion`.

## Inputs

- The user's reply
- `commit_cleanup_available`, `proposals_path` from walker state

```bash
STATE="$PLAN_DIR/.walk-state.polish.json"
```

## Steps

1. **Record the deferred transition** `display → ask_polish`.

2. **Map the reply** to a set of approved categories:

   | Reply shape | Result |
   |---|---|
   | all, apply, go, mis | title, body, threads (resolved-by-code only), comments |
   | a list of category names | exactly those. "commits" is honored only when `commit_cleanup_available=true`; otherwise say why it can't be and apply the rest |
   | "all including commits", "everything, commits too" | the four plus commits |
   | a change to a proposal ("keep the comment at x.go:40", "shorter body") | `user_adjust`, carrying the change to analyze |
   | stop, nothing, leave it | `user_stop` |

   An empty approved set (the user named only categories that are "unchanged") is `user_stop` with a note.

3. **Persist:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key approved --value "<JSON list from: title, body, threads, threads_ambiguous:[ids], comments, commits>"
   ```

4. **Ambiguous** → one-line plain-text follow-up, end the turn. Never resolve toward commits.

## Outgoing edges

- **`user_apply`** → `apply-github` (runs whatever GitHub-side categories were approved, possibly none, then routes on the local ones)
- **`user_adjust`** → `analyze`
- **`user_stop`** → `finalize`

```bash
scripts/walk.sh transition --state "$STATE" --from ask_polish --to apply_github --condition user_apply
scripts/walk.sh transition --state "$STATE" --from ask_polish --to analyze      --condition user_adjust
scripts/walk.sh transition --state "$STATE" --from ask_polish --to finalize     --condition user_stop
```

## Notes

- **Named categories are the confirmation.** No second "are you sure" for anything, including commits. The user typed the word.
