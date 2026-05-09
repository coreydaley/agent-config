# Node: terminal

Sink node. Print a final summary, suggest next steps, stop.

## Inputs

- `$FINDINGS` (final ledger state)
- All accumulated state (iteration count, what was fixed, what's open, etc.)

## Steps

1. **Print a tight summary to the user.** Numbers first, prose second. Example (multi-repo case):

   ```
   Self-review complete.

   Sprint: <session-path>
   Repos in scope: acme/web-app, acme/api
   Iterations: 3
   Findings: 12 total
     - Fixed: 8 (5 in web-app, 2 in mono, 1 cross-repo)
     - Triaged (won't-fix / deferred / skipped): 2
     - Open at LOW/NIT: 2
     - Open at Blocker/High/Medium: 0

   Ledger: <session>/self-review/findings.md
   Audit trail: <session>/self-review/iteration-*/
   Draft PRs:
     - https://github.com/acme/web-app/pull/1234
     - https://github.com/acme/api/pull/5678
   ```

2. **Suggest next steps.** Don't act on these — just print:

   ```
   Suggested next steps:
   1. Push each repo's working branch to update its draft PR
      (one push per repo from each worktree).
   2. Run `/polish-pull-request` per PR if titles/bodies need a final pass.
   3. Watch CI on each PR. If failures land, address them via
      `/review-address-feedback <PR-url>` (it walks CI-bot comments the
      same way as human-reviewer comments).
   4. When you're satisfied with each PR, mark it ready-for-review:
        gh pr ready <PR-number>
      or via the GitHub UI.
   ```

3. **Note the ledger boundary explicitly.** Print:

   ```
   ── ledger note ──────────────────────────────────────────────
   findings.md captures the pre-push self-review state. After you
   push, post-push fixes (CI failures, address-feedback runs,
   post-merge follow-ups) flow through /review-address-feedback
   and live in pr-reviews/pr-<N>/ — they don't update findings.md.
   That's by design: self-review is the pre-push window.
   ─────────────────────────────────────────────────────────────
   ```

   This tells the user where post-push activity lives so they don't expect findings.md to keep tracking the PR's life after they've pushed.

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
