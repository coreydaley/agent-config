# Sprint 004 Merge Notes

## Claude Draft Strengths
- Specified the actual 5-phase workflow with Codex exec prompt content
- Defined intermediate file naming scheme explicitly
- Included `docs/security/README.md` as a reference anchor
- Included `/ledger add NNN` step in Phase 5
- Explicitly handled no-findings case in DoD
- Agent-config-specific review categories (prompt injection, privilege escalation)

## Claude Draft Weaknesses (from Codex critique)
- Wrong `/sprint-work` invocation syntax: `SPRINT-NNN` → should be just `NNN`
- Severity escalation on agreement is a policy mistake: agreement = higher confidence,
  not higher severity; severity should be re-evaluated on impact/exploitability/blast radius
- No stable finding schema for intermediate files (Phase 2/3 artifacts)
- `docs/security/README.md` as P0 is over-scoped; fold essentials into command
- README.md update was listed as optional ("consider adding") — should be required P1
- Rollback section mentions `git checkout` which conflicts with project's safe-git guidance

## Codex Draft Strengths
- Key Decisions section — explicit rationale for design choices
- Explicit out-of-scope list — prevents scope creep
- Verification Plan with systematic edge cases
- Output contract verification step against sprint-work.md
- README.md update as required P1

## Codex Draft Weaknesses (from Claude critique)
- No actual command phases specified — sprint plan to build the command rather than spec of the command
- Intermediate file naming undefined — leaves naming to executing agent
- Missing `docs/security/README.md`
- Missing `/ledger add NNN` step
- Missing severity escalation/confidence calibration logic
- Vague Codex exec prompt content

## Valid Critiques Accepted

| Critique | Source | Decision |
|---|---|---|
| `/sprint-work SPRINT-NNN` → `/sprint-work NNN` | Codex → Claude | Accepted — fix in command and sprint |
| Severity escalation on agreement is wrong | Codex → Claude | Accepted — replace with confidence note; re-rate on evidence |
| Finding schema needed for intermediate files | Codex → Claude | Accepted — define schema in command |
| `docs/security/README.md` → P1 | Codex → Claude | Accepted — fold naming convention into command body |
| README.md update → required P1 | Codex → Claude | Accepted |
| Fix rollback wording | Codex → Claude | Accepted — reword to standard git restore/revert |
| Key Decisions section | Claude → Codex | Incorporate into sprint document |
| Verification Plan edge cases → DoD | Claude → Codex | Incorporate as DoD items |

## Critiques Rejected (with reasoning)

None — all valid critiques accepted.

## Interview Refinements Applied

- Single command: `audit-security` (not two commands)
- Output: standard `SPRINT-NNN.md` sprint (executed by `/sprint-work`)
- Naming convention: `audit-*` namespace for extensibility
- Same sprint ledger and SPRINT-NNN numbering
- No separate remediation command

## Final Decisions

1. **P0 (only)**: `commands/audit-security.md` — one file, one must-ship
2. **P1-A**: `README.md` update — required documentation for discoverability
3. **P1-B**: `docs/security/README.md` — nice-to-have; fold naming into command
4. **Finding schema**: define inline in command — `ID | Severity | Title | Location | Why | Recommended Fix`
5. **Severity calibration**: agreement between agents = higher confidence; severity rated on evidence (impact, exploitability, blast radius, reachability)
6. **Sprint sizing gate**: PASSES — one file creation task, well-scoped for a single sprint
