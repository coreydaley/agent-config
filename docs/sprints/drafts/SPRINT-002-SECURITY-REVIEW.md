# SPRINT-002 Security Review

## Review Scope

`docs/sprints/SPRINT-002.md` — reviewed against `commands/superplan.md` (the file being modified) and project context in `agents/claude/CLAUDE.md`.

---

## Finding 1: System Prompt Injection Surface (Phase 7 user summary addition)

**Section**: P0-C, Phase 7 closing
**Rating**: Low

**Description**: The new Phase 7 closing step instructs Claude to show the user a summary of devil's advocate findings. If the devil's advocate output (produced by Codex via `codex exec`) contains adversarial content, that content will surface in Claude's user-facing summary. This is an indirect prompt injection vector: attacker controls Codex output → Claude summarizes it → content reaches user in a "trusted" summary frame.

**Mitigation**: The risk is inherent to the workflow's design (Claude synthesizes Codex output in all phases), not specific to this sprint. The existing Phase 6 merge and Phase 8 security review create the same surface. No sprint-specific mitigation needed. Note in the Phase 7 text that Claude should summarize findings in its own words rather than quoting Codex output verbatim.

**Action**: Add one phrase to the Phase 7 closing text: "summarize findings in your own words."

---

## Finding 2: Reference to External Files in Agent Prompts (Phase 5 Codex exec)

**Section**: P0-B, Phase 5 Codex exec prompt
**Rating**: Low

**Description**: The Phase 5 Codex prompt tells Codex to read `docs/sprints/README.md` and `CLAUDE.md` for project structure. If those files contain adversarial content (e.g., from a supply-chain compromise of this repo), that content gets injected into Codex's planning context. However, these are files within the same repo that the operator controls, making this an inherent trust-the-repo assumption.

**Mitigation**: Already acceptable — same trust model as all other phases. P0-A creating README.md from scratch in this sprint means the content is author-controlled.

**Action**: None required.

---

## Finding 3: `docs/sprints/README.md` Content Flows into Agent System Prompts

**Section**: P0-A
**Rating**: Low

**Description**: The new `README.md` will be read by Claude (Phase 1: Orient) and referenced in Codex prompts (Phase 5). Its content becomes part of the agent context window. Malicious or unreviewed content in README.md would affect all subsequent superplan runs.

**Mitigation**: README.md is a new file created in this sprint, authored by Claude under human review. Content is sprint template documentation — no executable logic, no secrets, no user-controlled input.

**Action**: The existing project SECURITY.md disclaimer ("review all configurations before use") covers this. No additional action needed.

---

## Finding 4: Ledger Command Normalization

**Section**: P0-B (ledger audit)
**Rating**: Low

**Description**: The sprint normalizes all ledger references to `/ledger` skill syntax. The skill runs `python3 ${CLAUDE_SKILL_DIR}/scripts/ledger.py $ARGUMENTS`. If `$ARGUMENTS` is constructed from user-facing content (sprint titles, etc.), it could be injection-relevant. However, the `stats` and `sync` subcommands take no dynamic arguments.

**Mitigation**: The `/ledger sync` and `/ledger stats` calls use hardcoded subcommand strings, not user-supplied arguments. No injection surface in the specific calls being normalized.

**Action**: None required.

---

## Summary

| Finding | Rating | Action |
|---------|--------|--------|
| Phase 7 Codex summary injection | Low | Add "summarize in your own words" phrase to Phase 7 text |
| Phase 5 external file references | Low | None |
| README.md in agent context | Low | None (covered by existing SECURITY.md) |
| Ledger command normalization | Low | None |

**No Critical or High findings.**

All findings are Low. One finding warrants a minor wording addition to Phase 7.

---

## Incorporation Decision

- Add "summarize in your own words" phrase to the Phase 7 user summary step (P0-C). This is a Security Considerations addition, not a DoD change.
- No other modifications to `SPRINT-002.md` required.
