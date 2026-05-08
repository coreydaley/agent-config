# Node: ask-cleanup

Prompt 2: commit + comment cleanup. **Destructive** — commit cleanup rewrites history and force-pushes. Surface the consequences clearly.

## Inputs

- `proposals_path`, `cleanup_skip_reason` from walker state

```bash
STATE="<path>"
PROPOSALS=$(scripts/walk.sh get --state "$STATE" --key proposals_path)
CLEANUP_SKIP_REASON=$(scripts/walk.sh get --state "$STATE" --key cleanup_skip_reason)
```

## Steps

1. **Auto-skip if `cleanup_skip_reason` is set.** `analyze` already determined commit cleanup is unsafe (collaborator commits, merge from base, HEAD mismatch). Print the reason, don't ask, route via `user_skip` to `summarize`.

   ```
   Commit cleanup: SKIPPED — <reason>.
   Comment cleanup may still be available — but skipping in this run for safety.
   ```

   Edge case: if there are comment-cleanup proposals but commits are unsafe, you could in principle still offer comments-only. For simplicity and safety, skip both when `cleanup_skip_reason` is set. The user can run `/polish-pull-request` again after fixing the underlying issue.

2. **State the consequences up front:**

   > "Commit cleanup rewrites history and force-pushes with `--force-with-lease`. Existing approvals on the PR may be dismissed depending on branch protection settings. Comment cleanup edits added comments inline — non-destructive, but does add to the diff."

3. **Use `AskUserQuestion`:**

   > 1. **Apply commit + comment cleanup** — both, as proposed
   > 2. **Commit cleanup only** — rewrite history; leave inline comments alone
   > 3. **Comment cleanup only** — edit comments; leave history alone (no force-push)
   > 4. **Pick per item** — walk each proposed commit group / comment edit
   > 5. **Skip cleanup** — leave commits and comments as-is

4. **For "Pick per item"**, walk through each proposed commit group and each proposed comment edit interactively. Record:
   ```bash
   scripts/walk.sh set --state "$STATE" --key cleanup_decisions --value "<JSON>"
   scripts/walk.sh set --state "$STATE" --key do_comments --value "<true|false>"
   scripts/walk.sh set --state "$STATE" --key do_commits --value "<true|false>"
   ```

5. **Persist the high-level choice:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key cleanup_choice --value "<both|commits_only|comments_only|pick|skip>"
   ```

## Outputs

- `cleanup_choice`, `do_comments`, `do_commits`, `cleanup_decisions` in walker state

## Outgoing edges

- **`comments_first`** → `apply-comments`. Comments are part of the cleanup (cases: both, comments_only, pick with do_comments=true).
- **`commits_only`** → `preflight-cleanup`. Only commits approved (case: commits_only, or pick with do_commits=true and do_comments=false).
- **`user_skip`** → `summarize`. User skipped, or `cleanup_skip_reason` was set.

Record exactly one:

```bash
# Comments first (with optional commits to follow):
scripts/walk.sh transition --state "$STATE" --from ask_cleanup --to apply_comments --condition comments_first

# Commits only:
scripts/walk.sh transition --state "$STATE" --from ask_cleanup --to preflight_cleanup --condition commits_only

# Skip cleanup entirely:
scripts/walk.sh transition --state "$STATE" --from ask_cleanup --to summarize --condition user_skip
```

## Notes

- **Default to "Skip cleanup" when ambiguous.** Force-push is recoverable but disruptive. The user can re-run polish later if they want cleanup.
- **State the consequences before the prompt.** "It rewrites history and force-pushes" needs to be in the user's eyes when they pick. Don't bury it.
- **The choice is the confirmation.** No "are you sure?" follow-up.
