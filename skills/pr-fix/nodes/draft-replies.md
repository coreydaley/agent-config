# Node: draft-replies

Every thread gets an honest answer, human or bot. Draft one per thread, show them, end the turn. Review-sourced findings have no threads, so this node is a pass-through for them. On re-entry from `ask-replies` (`user_edit`), apply the edits and re-show.

## Inputs

- `mode`, `outcomes_path`, `findings_path`, `push_result`, `fix_dir` from walker state
- The user's edit request on re-entry

```bash
STATE="$PLAN_DIR/.walk-state.fix.json"
MODE=$(scripts/walk.sh get --state "$STATE" --key mode)
```

## Steps

1. **No threads?** `mode=review` or `resume` from a review-sourced triage, or every thread finding was `stale`/`skipped` with nothing to say → route `no_threads` silently. `CI` findings have no thread and get no reply: the commit or ADDRESSED.md answers them. Resolving threads is left alone, human and bot alike.

2. **Draft one reply per thread**, human (`H`) and bot (`B`), from the outcome:

   | Outcome | Reply shape |
   |---|---|
   | fixed | what changed, in the code's terms, one or two sentences. Name the commit only if the branch wasn't squashed. |
   | deferred | that it's out of this PR's scope and why (which Scope bullet), and that it's recorded as a follow-up. No issue number, because none was filed. |
   | won't-fix | the reason, technical, one or two sentences. Disagreeing is fine. Being terse about it is fine. |
   | stale | that the cited code changed and the comment may no longer apply, and what's there now. |
   | blocked | that the fix broke a test and what the test says, and that it needs a second look. |

   Voice: conversational, lowercase openers are fine (`yeah, good catch`, `ah`), no formality, no "Thank you for the feedback." Never an internal ID, never "per the triage," never the reviewer's name in the third person. Every reply ends with `*(via Claude Code)*` so the user's own comments stay distinguishable.

   Top-level review bodies (`HR` and `BR` findings) get one reply as a PR comment summarizing how their asks were handled.

   **Bot threads** get the same honesty as human ones. An unanswered bot thread reads the same as one nobody looked at, and a human reviewer opening the PR shouldn't have to redo the analysis. Two adjustments:
   - Use the bot's own disposition syntax when it has one (a `@<bot> dismiss: <reason>` style command for won't-fix and defer), so the reply also clears the finding.
   - More than 10 bot threads in the run → one PR comment summarizing the bot dispositions instead of a reply per thread (a table of file:line, outcome, one-line reason), plus per-thread replies only where the bot needs one to clear the finding.

3. **Write `$FIX_DIR/replies.md`:** one section per thread with the file:line, the reviewer's ask paraphrased in one line, and the draft reply.

4. **Show the drafts inline**, then the path, then the question in plain text:

   > Replies: **post** all, **edit** (name the thread and the change), or **skip** (fixes are pushed, nothing is said)?

5. **End the turn.** No tool call after the question. `ask-replies` records the transition.

## Outputs

- `$FIX_DIR/replies.md`

## Outgoing edges

- **`drafted`** → `ask-replies` (recorded next turn)
- **`no_threads`** → `persist`

```bash
scripts/walk.sh transition --state "$STATE" --from draft_replies --to ask_replies --condition drafted
scripts/walk.sh transition --state "$STATE" --from draft_replies --to persist     --condition no_threads
```

## Notes

- **Drafts are shown before posting, always.** "Fix and reply" in the user's approval of the triage was not authorization to post. This is the draft-first rule (`lib/pr-discipline.md` § Scope Discipline).
- **Don't thank, don't apologize, don't hedge.** Say what happened.
