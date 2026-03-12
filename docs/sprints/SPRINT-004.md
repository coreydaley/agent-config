# Sprint 004: `audit-security` Command

## Overview

This sprint creates `commands/audit-security.md` — a dual-agent security
audit command that applies the same competitive-review-then-synthesize
pattern as `sprint-plan.md` to security work.

The design key: instead of a custom report format requiring a separate
remediation command, `audit-security` produces a standard
`docs/sprints/SPRINT-NNN.md` sprint document. Security findings become
sprint tasks (Critical/High → P0, Medium → P1, Low → Deferred), and
`/sprint-work` executes them as-is. No new execution infrastructure.

The command is namespaced `audit-*` to establish an extensible family
(`audit-deps`, `audit-performance`, etc.) without inventing a new verb
category each time.

**Inherent limitations**: This is a workflow aid for human-reviewed
security work, not an automated security scanner. Static LLM review
cannot assess runtime exploitability, compensating controls, or
deployment-context-specific risk. The output is a starting point for
human judgment, not a guarantee of coverage. Scope the audit explicitly;
do not treat a "no findings" result as a clean bill of health without
reviewing what was actually covered.

## Key Decisions

1. **One command, no remediation companion** — output is a normal sprint
   document worked by the existing `/sprint-work` command.
2. **`audit-*` namespace** — first in an extensible audit family.
3. **Intermediate artifacts in `docs/security/`** — keeps working files
   separate from `docs/sprints/` while preserving sprint docs as the
   final executable work.
4. **Codex as adversarial reviewer** — same pattern as `sprint-plan`:
   independent work, synthesis, Codex devil's advocate, final output.
5. **Severity by evidence** — agreement between reviewers raises
   confidence, not severity. Severity is rated on impact, exploitability,
   blast radius, and reachability.

## Out of Scope

- A separate remediation/address command
- Changes to `commands/sprint-work.md`
- Scanner, linter, or automated code-analysis tooling
- A separate non-sprint report format as primary deliverable
- Additional `audit-*` commands (establish the pattern first)

## Use Cases

1. **Pre-merge security gate**: audit a branch, review the sprint,
   run `/sprint-work` to remediate P0 findings before merging.
2. **Periodic repo audit**: run on demand or before a release; produces
   a sprint trackable in the ledger.
3. **Scoped dependency review**: scope to specific files or directories
   after adding libraries.
4. **Agent config self-audit**: command files flow directly into agent
   system prompts — prompt injection and privilege escalation are
   high-value findings here.

## Architecture

```
audit-security [$ARGUMENTS = optional path/scope]

Phase 1: Orient
  → Determine scope ($ARGUMENTS or cwd)
  → Identify key files, recent changes, trust boundaries
  → Determine next SPRINT-NNN number

Phase 2: Independent Reviews (parallel)
  → Codex: write docs/security/NNN-CODEX.md  (launched first, background)
  → Claude: write docs/security/NNN-CLAUDE.md (simultaneously)

Phase 3: Synthesis
  → Read both reviews
  → Deduplicate; flag agreements as higher-confidence
  → Write docs/security/NNN-SYNTHESIS.md

Phase 4: Devil's Advocate (Codex)
  → Codex attacks synthesis → docs/security/NNN-DEVILS-ADVOCATE.md
  → Claude incorporates valid challenges

Phase 5: Sprint Output
  → Produce docs/sprints/SPRINT-NNN.md
  → Map findings → tasks (Critical/High=P0, Medium=P1, Low=Deferred)
  → /ledger add NNN "Security: [scope]"
  → User runs /sprint-work NNN
```

## Finding Schema

All intermediate files (`NNN-CLAUDE.md`, `NNN-CODEX.md`,
`NNN-SYNTHESIS.md`) must represent findings in this structure so
synthesis and devil's advocate phases operate on consistent data:

```
| ID | Severity | Title | Location | Why It Matters | Recommended Fix | Evidence/Notes |
|----|----------|-------|----------|----------------|-----------------|----------------|
| C001 | High | Description | path/to/file:line | Explanation | Fix guidance | Code quote or reference |
```

Severity levels: **Critical**, **High**, **Medium**, **Low**.

Severity is assessed on evidence: impact, exploitability, blast radius,
and reachability — not on whether both reviewers flagged it (that
raises confidence, not severity). Severity is also independent of
remediation cost; a Low-cost High-severity fix and an expensive
Medium-severity architectural weakness both deserve their rating.

## Implementation Plan

### P0: Must Ship

#### P0-A: `commands/audit-security.md`

**Files:**
- `commands/audit-security.md` — NEW

**Frontmatter:**
```yaml
---
description: >-
  Dual-agent security audit — Claude and Codex review independently,
  synthesize, devil's advocate pass, output as executable sprint
---
```

**Phase 1 — Orient:**
- Determine scope from `$ARGUMENTS` or default to cwd. Validate the
  path exists. Scope should exclude `build/`, generated files, vendored
  or third-party code, and binary files unless explicitly included in
  `$ARGUMENTS`.
- Read key files: `git log --oneline -10`, entry points, config files
- Determine next SPRINT-NNN: `ls docs/sprints/SPRINT-*.md | tail -1`;
  increment. If none exist, start at SPRINT-001.
- Create `docs/security/` if needed
- Note: `$ARGUMENTS` scope is validated as a path before being used
  elsewhere — do not interpolate raw user input into shell strings in
  Codex exec prompts

**Phase 2 — Independent Reviews (parallel):**

Launch Codex in background (substitute NNN at orient time):
```bash
codex exec "Perform a thorough security review of [scope]. \
  Write findings to docs/security/NNN-CODEX.md using this table \
  format for each finding: \
  | ID | Severity | Title | Location | Why It Matters | Recommended Fix | \
  where ID = C001, C002... (C for Codex). \
  Cover: (1) attack surface and trust boundaries, \
  (2) injection risks (command injection, prompt injection, path traversal), \
  (3) sensitive data handling and secrets exposure, \
  (4) authentication and authorization gaps, \
  (5) dependency risks and supply chain, \
  (6) for agent-config repos: prompt injection and privilege escalation \
  in command/skill/agent files. \
  Rate severity on evidence: impact, exploitability, blast radius, \
  reachability. Do not read Claude's review."
```

Claude writes its own independent review to `docs/security/NNN-CLAUDE.md`
simultaneously, using the same table format (ID = A001, A002... for Audit).

**Phase 3 — Synthesis:**
- Verify both `docs/security/NNN-CLAUDE.md` and
  `docs/security/NNN-CODEX.md` exist and are non-empty. If one is
  missing or empty, proceed with single-agent synthesis and note this
  prominently in `NNN-SYNTHESIS.md` with a warning in the final sprint.
- Read both reviews
- Deduplicate findings that appear in both (note which reviewers flagged
  each finding — overlap = higher confidence, not higher severity)
- When deduplicating, preserve the best `Evidence/Notes` from each
  reviewer; do not collapse two findings into one if they have different
  exploit preconditions or affected assets
- Assign canonical IDs (S001, S002...) in the synthesis
- Write `docs/security/NNN-SYNTHESIS.md` with unified finding table
- Re-evaluate severity for each finding based on evidence; do not
  automatically escalate severity because both reviewers agreed

**Phase 4 — Devil's Advocate:**

Launch Codex:
```bash
codex exec "Read docs/security/NNN-SYNTHESIS.md. Your job is to attack \
  it, not improve it. Write your challenge to \
  docs/security/NNN-DEVILS-ADVOCATE.md covering: \
  (1) false positives — findings not actually exploitable in this context, \
  (2) severity miscalibrations — findings rated too high or too low, \
  (3) missing findings — what did both reviewers miss? \
  (4) remediation steps that are impractical or incorrect."
```

Claude reads the devil's advocate output and:
- Removes confirmed false positives from the working finding list
- Recalibrates severity where the challenge is valid
- Adds genuinely missed findings
- **Documents every rejected challenge with explicit reasoning** in a
  "Rejected Challenges" subsection of `NNN-SYNTHESIS.md`

**Phase 5 — Sprint Output:**

Produce `docs/sprints/SPRINT-NNN.md` following the standard sprint
template from `docs/sprints/README.md`:

- **Title**: `Security Audit: [scope] ([YYYY-MM-DD])`
- **Overview**: audit scope, total findings by severity, top 3 issues
- **P0 tasks**: Critical and High findings — each task must include
  finding ID, location, issue description, and concrete remediation step
- **P1 tasks**: Medium findings
- **Deferred**: Low findings with reasoning
- **No-findings case**: if no findings, P0 must include a single
  "Verify no findings" task documenting scope, date, and review method
- **Definition of Done**: verification step for each remediation cluster

After writing the sprint:
- Run `/ledger add NNN "Security: [scope]"` to register it. If the
  ledger add fails, instruct the user to run it manually.
- **Before instructing the user to run `/sprint-work`**: note that
  security sprints may require reviewing P0 task ordering before
  execution — some remediations depend on others (e.g. fix a
  deserialization sink before removing the injection point upstream)
- Instruct user: "Review task ordering in SPRINT-NNN.md, then run
  `/sprint-work NNN`"

**Output checklist:**
- [ ] `docs/security/NNN-CLAUDE.md` written (table format)
- [ ] `docs/security/NNN-CODEX.md` written (table format)
- [ ] `docs/security/NNN-SYNTHESIS.md` written with canonical IDs
- [ ] `docs/security/NNN-DEVILS-ADVOCATE.md` written
- [ ] Valid devil's advocate challenges incorporated
- [ ] `docs/sprints/SPRINT-NNN.md` written with P0/P1/Deferred tiering
- [ ] Ledger entry added via `/ledger add NNN`
- [ ] User instructed to run `/sprint-work NNN`

**Tasks:**
- [ ] Write `commands/audit-security.md` with full 5-phase workflow
      using the Phase 1–5 spec above
- [ ] Verify all Codex exec prompts are self-contained (NNN resolved
      at orient time, not as a variable)
- [ ] Verify sprint output template follows `docs/sprints/README.md`
- [ ] Verify `/ledger add` uses correct syntax from `skills/ledger/`
- [ ] Verify rollback section uses "git restore/revert" language, not
      destructive `git checkout --` pattern

**Acceptance:**
- `commands/audit-security.md` exists with valid single-line
  `description:` frontmatter (Gemini TOML compatible)
- Phase 2 runs Claude and Codex reviews in parallel
- Finding schema (table) is consistent across all intermediate files
- Phase 5 output is a valid sprint document consumable by `/sprint-work`
- Severity is assessed on evidence, not on reviewer agreement
- `/sprint-work NNN` (not `SPRINT-NNN`) in user-facing instructions
- No `--model`/`--full-auto` flags in any Codex exec call

### P1: Ship If Capacity Allows

#### P1-A: `README.md` update

Add `audit-security` to the commands section of `README.md` with:
- Brief description of the command
- Invocation example
- Note on relationship to `/sprint-work`
- Consistent with the repo's agent capability matrix

**Acceptance:**
- Users can discover `audit-security` without reading the source file
- No mention of a separate remediation command

#### P1-B: `docs/security/README.md`

Lightweight reference file for the `docs/security/` directory:
- Purpose and naming convention (NNN matches sprint number)
- Finding schema (ID, Severity, Title, Location, Why, Fix)
- Note: these files may contain sensitive findings; review before
  committing to public repos

### Deferred

- `audit-deps` and other `audit-*` commands — establish `audit-security`
  pattern first
- Linear/Jira sync for audit findings — reuse sprint-plan's tool sync
  pattern when needed
- Automated scheduling — out of scope for command files

## Files Summary

| File | Action | Purpose |
|------|--------|---------|
| `commands/audit-security.md` | Create | 5-phase dual-agent security audit command (P0) |
| `README.md` | Modify | Document new command for discoverability (P1-A) |
| `docs/security/README.md` | Create | Naming conventions and finding schema (P1-B) |

## Definition of Done

- [ ] `commands/audit-security.md` exists with valid single-line `description:` frontmatter
- [ ] Phase 2: Codex launched in background; Claude writes review simultaneously
- [ ] All intermediate files use the finding schema table (ID, Severity, Title, Location, Why, Fix)
- [ ] Phase 3: synthesis deduplicates findings; notes confidence from agreement; severity rated on evidence
- [ ] Phase 4: Codex devil's advocate runs; valid challenges incorporated before sprint is written
- [ ] Phase 5: sprint output follows `docs/sprints/README.md` template
- [ ] Severity mapping is unambiguous: Critical/High → P0, Medium → P1, Low → Deferred
- [ ] No-findings case produces a "Verify no findings" P0 task (not an empty sprint)
- [ ] `/ledger add NNN` included in Phase 5
- [ ] User instructed to run `/sprint-work NNN` (correct syntax — not `SPRINT-NNN`)
- [ ] All Codex exec calls use no `--model`/`--full-auto` flags
- [ ] Rollback section uses "git restore/revert" language (not destructive checkout)
- [ ] Phase 1 validates `$ARGUMENTS` as a path before any use in Codex exec prompts (SR-005)
- [ ] Phase 2 Codex prompt explicitly covers `commands/*.md` and `skills/` when scope includes agent-config (SR-009)
- [ ] Phase 3 verifies both review files non-empty before proceeding; notes single-agent mode if one missing
- [ ] Phase 4 rejected challenges documented with explicit reasoning
- [ ] Phase 5 notes task ordering review before running `/sprint-work`
- [ ] Manual read-through: each phase produces what the next phase consumes
- [ ] Edge-case read-through: (1) no scope arg, (2) path-scoped audit, (3) overlapping findings, (4) no findings
- [ ] Output contract check: compare Phase 5 sprint format against `docs/sprints/README.md`

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Codex exec prompts reference NNN as unresolved variable | Medium | Medium | Orient phase resolves NNN first; prompts use the literal number |
| Phase 5 sprint doesn't conform to sprint-work's expected format | Medium | High | Phase 5 explicitly references `docs/sprints/README.md`; output contract DoD check |
| Finding schema drifts between phases | Low | High | Schema defined in command body; all phases reference it |
| Zero findings → empty sprint → noise in ledger | Low | Medium | DoD: no-findings produces "Verify no findings" P0 task |
| Command text too long for Gemini TOML prompt field | Low | Low | `sprint-plan.md` is already long; document if limit hit |

## Security Considerations

- `commands/audit-security.md` flows into agent system prompts — review
  phrasing for unintended scope expansion or privilege escalation
- **SR-005 (High)**: `$ARGUMENTS` scope must be validated as a path in
  Phase 1 before being used in any Codex exec prompt — do not
  interpolate raw user input into shell strings. DoD requirement.
- **SR-009 (High)**: When auditing the agent-config repo itself, the
  Codex independent review is especially important — Claude reviewing
  its own command files has systematic blind spots. Phase 2 Codex
  prompt should specifically cover `commands/*.md` and `skills/*/SKILL.md`.
  Disagreements between Claude and Codex on agent/command file findings
  should be flagged for devil's advocate attention.
- Codex exec prompts must not instruct Codex to execute shell commands
  beyond reading files and writing to `docs/security/`
- Sprint tasks in the output will be executed by agents via `/sprint-work`
  — ensure task descriptions are specific enough to be safe but not so
  broad as to cause unintended file modifications
- `docs/security/` files may contain sensitive findings — P1-B README
  should document that these should be reviewed before committing to
  public repos

## Observability & Rollback

- Verification: invoke `/audit-security` on this repo; confirm
  `docs/security/NNN-*.md` files and `docs/sprints/SPRINT-NNN.md`
  are produced correctly; confirm sprint is workable by `/sprint-work`
- Rollback: text files only; use `git restore` or `git revert` as
  appropriate

## Documentation

- [ ] P1-A: Add `audit-security` to `README.md` with invocation example
- [ ] P1-B: Create `docs/security/README.md` with naming convention and
      finding schema

## Dependencies

- SPRINT-001 (completed) — commands/ architecture
- SPRINT-002 (completed) — docs/ conventions, sprint template
- SPRINT-003 (completed) — ledger skill integration, `/ledger add` syntax

## Open Questions

None — all design questions resolved.
