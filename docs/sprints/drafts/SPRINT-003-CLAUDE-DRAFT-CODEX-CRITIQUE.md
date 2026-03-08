# Critique of `SPRINT-003-CLAUDE-DRAFT.md` (Codex)

## Findings (Ordered by Severity)

### High
1. **Uses a non-existent project path for command guidance (`CLAUDE.md`)**
   - The draft repeatedly points `/sprint` validation guidance to `CLAUDE.md`, but this repository does not have a root-level `CLAUDE.md`.
   - The in-repo Claude-specific convention file is `agents/claude/_CLAUDE.md`; project-level execution targets are documented in `README.md` and `Makefile`.
   - Impact: introduces broken instructions in the command flow and repeats a known stale-reference class from prior sprint work.
   - Fix: replace root `CLAUDE.md` references with existing sources (`README.md`, `Makefile`, and only agent-specific docs when explicitly needed).

2. **Proposes an invalid ledger command for sprint existence verification**
   - Phase 2 says to use `/ledger status NNN` to verify a sprint exists.
   - `ledger.py` defines `status` as `status <sprint_id> <status>` (a mutating command), not a read/check command.
   - Impact: this would either fail or accidentally alter sprint state if misused.
   - Fix: use `/ledger list`, `/ledger next`, or `/ledger stats` for read-only verification; if existence check is needed, specify a non-mutating pattern.

### Medium
3. **Behavior for explicit sprint argument conflicts with ledger integrity goals**
   - Use Case 4 says `/sprint 005` should run even if not `planned`, while Phase 2 also proposes verification before execution.
   - This is directionally inconsistent and can bypass intended state discipline.
   - Fix: define one policy clearly (for example: explicit NNN allowed only if entry exists; otherwise instruct `/ledger sync` or `/ledger add` then stop).

4. **In-progress sprint handling is left as an open question rather than a decided rule**
   - The intent explicitly calls out this edge case; the draft includes a guard but leaves hard-stop vs soft-prompt unresolved.
   - Impact: reduces implementability and can lead to inconsistent behavior.
   - Fix: decide and encode one default behavior in acceptance criteria.

### Low
5. **Security section is mostly restating mechanics, not sprint-specific controls**
   - The section explains why risk is low but does not add an actionable safeguard (for example, explicit non-use outside `/sprint` or command-scope wording).
   - Fix: include one enforceable instruction in `skills/ledger/SKILL.md` usage text or `commands/sprint.md` guardrail language.

## What Works Well
1. Correctly identifies the root integration defect (`disable-model-invocation: true`) and targets a minimal fix.
2. Keeps scope constrained to `commands/sprint.md` and `skills/ledger/SKILL.md`, matching sprint intent.
3. Adds practical edge-case coverage (no planned sprint, already in-progress sprint).
4. Preserves the no-change stance on `skills/ledger/scripts/ledger.py`.

## Recommended Reframe

### P0 (Must Ship)
1. Remove all references to root `CLAUDE.md` and anchor validation guidance in existing files.
2. Replace invalid `/ledger status NNN` verification step with a read-only ledger check.
3. Resolve explicit-argument policy so sprint execution cannot silently bypass ledger consistency.
4. Resolve in-progress behavior as a concrete default (not an open question).

### P1 (If Capacity Allows)
1. Add one explicit guardrail sentence limiting ledger state mutation to user-initiated sprint flows.
2. Tighten acceptance criteria so each edge case has a deterministic expected command outcome.

## Suggested Edits to Claude Draft
1. Change build/test guidance references from `CLAUDE.md` to `README.md` and `Makefile`.
2. Replace `/ledger status NNN` verification wording with non-mutating alternatives.
3. Add a specific branch for "explicit NNN missing from ledger" (run `/ledger sync` or `/ledger add`, then re-run `/sprint`).
4. Convert the in-progress open question into a decided behavior in the plan and DoD.

## Final Assessment
Claude's draft is close and well-scoped, but it contains one critical command-level correctness bug and one high-impact stale path reference. Fixing those, then locking the argument/in-progress policies, would make it execution-safe and aligned with Sprint 003 intent.
