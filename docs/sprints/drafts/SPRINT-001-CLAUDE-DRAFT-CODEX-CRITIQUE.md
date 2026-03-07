# Critique of `SPRINT-001-CLAUDE-DRAFT.md` (Codex)

## Overall Assessment
Claude's draft is strong on structure and intent alignment. It correctly embraces per-agent routing, preserves generate+symlink architecture, and provides a practical phased plan. The main issues are scope expansion and a few assumptions that should be tightened to keep Sprint-001 executable.

## What Works Well
1. Clear articulation of the core problem (false parity across agents).
2. Useful architecture and data-flow sections that make the target model concrete.
3. Capability matrix is mostly accurate and directly actionable.
4. Phase-based implementation plan is easy to execute.
5. Good definition-of-done checklist with observable filesystem outcomes.
6. Includes risk, security, and open-question sections, which improves decision quality.

## High-Priority Gaps and Risks

### 1) Sprint Scope Is Too Broad
The draft bundles foundational routing fixes with content writing, sprint infrastructure creation, Gemini conversion, and extra script/Makefile expansion. For Sprint-001 (first foundational sprint), this is likely too much for reliable completion.

Why this matters:
- Increases coordination overhead and regression risk.
- Makes the acceptance surface too large for one sprint.

Recommendation:
- Split into P0 and P1 within Sprint-001, or defer non-foundational tasks to Sprint-002.
- Keep Sprint-001 focused on correctness of routing and symlinks first.

### 2) Over-commits on New Artifacts Not Required by Intent
The draft introduces `docs/sprints/README.md`, `docs/sprints/ledger.tsv`, and ledger skill checks as core sprint work. The intent did not require sprint tooling bootstrap as part of architecture revamp.

Why this matters:
- Adds non-essential work that does not directly fix the agent compatibility issues.

Recommendation:
- Move sprint ledger/infrastructure tasks to stretch goals unless explicitly requested.

### 3) Subagent Support Position for Gemini Is Underspecified
The draft lists Gemini subagents as supported while also saying format is TBD and suggests excluding Gemini subagents in implementation phase. That contradiction needs resolution before coding.

Why this matters:
- Ambiguous acceptance criteria lead to partial or conflicting implementation.

Recommendation:
- Pick one explicit Sprint-001 policy:
  - either "Gemini subagents deferred, skip cleanly"
  - or "Gemini subagents supported with defined transform spec and fixtures"

### 4) Build Directory Choice Is Sensible but Introduces Migration Complexity
Using `build/gemini-commands/` is reasonable, but introducing a new generated location while other generated files remain in-place can create mixed conventions in Sprint-001.

Why this matters:
- Inconsistent generated artifact strategy increases maintenance burden.

Recommendation:
- Either keep all current generation in-place for Sprint-001 simplicity, or explicitly define mixed strategy as temporary with follow-up ticket.

### 5) Content Authoring Is Treated as Core Deliverable
Phase 2 requires meaningful instruction content across all agents. The intent primarily calls for architecture and compatibility correctness, not prompt writing quality.

Why this matters:
- Content authoring can consume large time without de-risking platform correctness.

Recommendation:
- Reduce to minimal non-empty stubs for validation and defer substantial content authoring.

## Medium-Priority Corrections
1. Clarify whether `agents/_GLOBAL_LB.md` is active or legacy. The draft references it as optional without defining behavior.
2. Tighten DoD around idempotency (`make all` run twice yields same outcomes).
3. Add explicit failure behavior for missing source files and missing destination parent dirs.
4. Replace percentage-based phase weights with timeboxed or dependency-based sequencing to avoid false precision.
5. Document exact skip logs expected for unsupported features (Codex subagents, Copilot commands, Gemini skills, etc.).

## Recommended Reframe for Sprint-001

### P0 (Must Ship)
1. Correct agent config generation/symlinks for all four agents.
2. Restrict skills symlink routing to supported agents only.
3. Fix subagent source and supported-agent routing.
4. Keep commands for Claude/Codex correct and explicit.
5. Update README + agents README with verified support matrix.
6. Ensure `make all` idempotency and deterministic behavior.

### P1 (Ship If Capacity Allows)
1. Gemini command conversion pipeline.
2. Optional helper scripts/targets for Gemini command linking.
3. Minimal seed content updates for agent files.

### Deferred
1. Sprint ledger tooling setup.
2. Rich instruction content authoring.
3. Broader generated-artifacts directory migration.

## Suggested Edits to Claude Draft
1. Move "Phase 6: Sprint Infrastructure" to Deferred.
2. Reduce "Phase 2: Agent Config Content" to minimal smoke-test stubs.
3. Resolve Gemini subagent support contradiction with one explicit policy.
4. Add idempotency checks to Definition of Done.
5. Add explicit "unsupported feature skip" assertions to verification checklist.

## Final Verdict
Claude's draft is a strong foundation and mostly aligned with intent. With scope tightening and a few consistency fixes, it can become an execution-ready Sprint-001 plan that is much more likely to finish successfully and safely.
