# Node: terminal

Sink node. Print a final summary, suggest next steps, stop.

## Inputs

- `$FINDINGS` (final ledger state)
- All accumulated state (iteration count, what was fixed, what's open, etc.)

## Steps

1. **Print a tight summary to the user.** Numbers first, prose second. Example:

   ```
   Self-review complete.

   Iterations: 3
   Findings: 12 total
     - Fixed: 8
     - Triaged (won't-fix / deferred / skipped): 2
     - Open at LOW/NIT: 2
     - Open at Blocker/High/Medium: 0

   Ledger: ~/Reports/<org>/<repo>/self-reviews/pr-123/findings.md
   Audit trail: ~/Reports/<org>/<repo>/self-reviews/pr-123/iteration-*/
   ```

2. **Suggest next steps.** Don't act on these — just print:

   ```
   Suggested next steps:
   1. Push the working branch to update the draft PR.
   2. Run `/polish-pull-request` if the title/body need a final pass.
   3. Watch CI on the PR. If failures land, /address-ci can drive the
      fix loop against CI logs.
   4. When you're satisfied, mark the PR ready-for-review:
        gh pr ready <PR-number>
      or via the GitHub UI.
   ```

3. **Stop.** No further state transitions, no file writes beyond what `address` already produced. Future runs of `/sprint-self-review` on this PR will pick up from the existing `findings.md` and continue iteration numbering.

## Outputs

- (printed to user — the artifacts on disk are unchanged from what address produced)

## Outgoing edges

None. This is a sink.

## Notes

- **Don't undraft the PR.** That's the user's call, always. Mention `gh pr ready` in suggested next steps; don't run it.
- **Don't push.** The user pushes when they're satisfied — also their call. CI runs once on that single push.
- **Don't auto-merge or comment.** Same principle: terminal is a stop, not a launch.

## Failure modes

- None expected. Terminal is the success-shaped exit. If we got here from a `user_done` after a half-complete run, the summary still reports honestly: "open at Blocker/High/Medium: N" tells the user the work isn't fully done. They chose this.
