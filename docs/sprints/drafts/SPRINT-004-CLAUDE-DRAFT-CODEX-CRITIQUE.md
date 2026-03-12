# Critique of `SPRINT-004-CLAUDE-DRAFT.md` (Codex)

## Findings (Ordered by Severity)

### High
1. **The draft encodes an invalid `/sprint-work` invocation**
   - The output checklist says to inform the user to run `/sprint-work SPRINT-NNN` ([docs/sprints/drafts/SPRINT-004-CLAUDE-DRAFT.md](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/drafts/SPRINT-004-CLAUDE-DRAFT.md#L166C1)).
   - `commands/sprint-work.md` expects a numeric sprint argument like `005`, not a filename-shaped token.
   - Impact: the command would teach the wrong invocation pattern at the handoff point.
   - Fix: consistently instruct the user to run `/sprint-work NNN`, or just `/sprint-work` if the new sprint has already been added to the ledger as `planned`.

2. **Severity escalation by cross-agent agreement is not a sound security policy**
   - The synthesis phase says to escalate severity by one level whenever both agents flag the same issue ([docs/sprints/drafts/SPRINT-004-CLAUDE-DRAFT.md](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/drafts/SPRINT-004-CLAUDE-DRAFT.md#L124C1)).
   - Agreement between reviewers increases confidence that a finding is real, but it does not increase exploitability or business impact. A duplicated Medium should not automatically become a High.
   - Impact: this can inflate sprint priority, create false urgency, and make the final sprint noisier than the actual risk warrants.
   - Fix: use agreement to raise confidence, not severity. Re-rate severity based on impact, exploitability, reachability, and blast radius.

### Medium
3. **README integration is treated as optional even though this is a user-facing command**
   - The draft only says to "Consider adding `audit-security` to `README.md`" ([docs/sprints/drafts/SPRINT-004-CLAUDE-DRAFT.md](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/drafts/SPRINT-004-CLAUDE-DRAFT.md#L268C1)).
   - For a new top-level command in `commands/`, discoverability should be part of the sprint, not a maybe-later follow-up.
   - Impact: the repo can ship a real command that is invisible in the main usage docs.
   - Fix: make the README update a required P1 or P0 documentation task with acceptance criteria.

4. **The draft never defines a stable finding schema despite requiring finding IDs later**
   - Phase 5 requires each sprint task to include a finding ID, location, description, and remediation step ([docs/sprints/drafts/SPRINT-004-CLAUDE-DRAFT.md](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/drafts/SPRINT-004-CLAUDE-DRAFT.md#L151C1)).
   - But the independent review and synthesis phases do not define how IDs are assigned or what structured fields each intermediate artifact must contain.
   - Impact: synthesis and devil's advocate passes become looser than they need to be, and future machine parsing becomes harder.
   - Fix: define a minimal finding record shape up front, for example: `ID`, `Severity`, `Title`, `Location`, `Why it matters`, `Recommended fix`, `Evidence/notes`.

5. **`docs/security/README.md` is probably over-scoped for this sprint**
   - The intent's success criteria only require `commands/audit-security.md` and a working sprint-output contract, but the draft makes `docs/security/README.md` a P0 deliverable ([docs/sprints/drafts/SPRINT-004-CLAUDE-DRAFT.md](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/drafts/SPRINT-004-CLAUDE-DRAFT.md#L183C1)).
   - The repo already has `docs/sprints/README.md` as the canonical sprint format reference. Adding a second README for a directory introduced by the same sprint is nice-to-have, not obviously must-ship.
   - Impact: expands scope and documentation surface without directly improving command correctness.
   - Fix: defer `docs/security/README.md` to P1, or fold its essential naming guidance into `commands/audit-security.md`.

### Low
6. **Rollback guidance uses a discouraged git pattern**
   - The rollback note says `git checkout` to revert ([docs/sprints/drafts/SPRINT-004-CLAUDE-DRAFT.md](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/drafts/SPRINT-004-CLAUDE-DRAFT.md#L262C1)).
   - In this repo's current agent guidance, destructive checkout-style rollback should be avoided unless explicitly requested.
   - Fix: reword rollback as "revert the text-file changes with normal git restore/revert workflow as appropriate" or simply omit rollback guidance for a text-only command-authoring sprint.

## What Claude Got Right
1. The draft makes the correct top-level product decision: one command, `audit-security`, with output as a normal sprint instead of inventing a second remediation workflow.
2. The 5-phase shape is clear and lines up well with the existing `sprint-plan` pattern: independent work, synthesis, adversarial review, then final artifact.
3. The security-specific review categories are concrete and relevant to this repo, especially prompt injection and privilege-escalation concerns in command files.
4. The severity-to-priority mapping is explicit, which is important if `/sprint-work` is going to execute the result without manual restructuring.
5. The no-findings case is handled explicitly in the Definition of Done, which avoids the empty-sprint ambiguity.

## What It Missed
1. It missed the concrete `/sprint-work` argument contract and accidentally documented the wrong command syntax.
2. It missed that agreement between agents is a confidence signal, not a severity signal.
3. It missed the need for a stable finding schema even though later phases depend on finding IDs and structured remediation tasks.
4. It underplayed command discoverability by leaving the main README update as optional.

## What I Would Do Differently
1. Keep `commands/audit-security.md` as the only must-ship artifact, and move `docs/security/README.md` to P1 unless implementation proves it is truly needed.
2. Define one lightweight finding template used in all four audit artifacts so synthesis and devil's advocate review operate on consistent data.
3. Replace "escalate severity on agreement" with "escalate confidence on agreement; re-evaluate severity from evidence."
4. Make README documentation a required part of shipping the command.
5. Keep the final handoff simple: create the sprint, add it to the ledger, then tell the user to run `/sprint-work NNN`.

## Recommended Reframe

### P0 (Must Ship)
1. Fix the `/sprint-work` invocation contract.
2. Remove automatic severity escalation by reviewer agreement.
3. Add a minimal structured finding format for all intermediate audit files and the final sprint translation.
4. Author `commands/audit-security.md` so it produces a normal sprint document that `/sprint-work` can consume directly.

### P1 (If Capacity Allows)
1. Update `README.md` with command discovery and examples.
2. Add `docs/security/README.md` only if the directory needs standalone documentation after the command text is finalized.
3. Document multi-path scope handling and commit-sensitivity guidance for audit artifacts.

## Final Assessment
Claude's draft is directionally strong and much closer to execution-ready than not. The main problems are one command-level correctness bug, one security-severity policy mistake, and some scope allocation that leans a bit heavier than necessary. Tightening those points would make the sprint simpler, safer, and better aligned with the repo's "minimal new infrastructure" pattern.
