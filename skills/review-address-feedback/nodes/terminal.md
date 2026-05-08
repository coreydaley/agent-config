# Node: terminal

Sink. Print a brief confirmation and stop.

## Inputs

- Walker history (for telling the user what happened)
- `session_dir` from walker state

## Steps

1. **Print a one-line summary** based on the last transition:
   - From `finalize → terminal`: "Done. See `$SESSION_DIR/ADDRESSED.md`."
   - From `verify-worktree → terminal [worktree_missing]`: "Stopped — wrong checkout. Re-run from the PR head branch."
   - From `load-findings → terminal [no_findings]`: "No addressable findings — nothing to do."
   - From `choose-strategy → terminal [user_cancel]`: "Cancelled — no work done."

2. **Point at the artifacts** (only when work happened):
   ```
   Artifacts:
     $SESSION_DIR/ADDRESSED.md     the outcome record
     $SESSION_DIR/final-test.log   full test run output
     $SESSION_DIR/diff.stat        git diff --stat at finalize time
   ```

3. **Stop.** No transitions, no further work.

## Outputs

- Brief printed summary to the user.

## Outgoing edges

None. Terminal is a sink.

## Notes

- **Don't suggest re-running** unless the user asks. Terminal is meant to be a clean exit.
- **Don't print full ADDRESSED.md.** The user has the path; it's their call whether to read it now.
- **Don't commit, don't push.** Per the global git rule, those wait for the user.
