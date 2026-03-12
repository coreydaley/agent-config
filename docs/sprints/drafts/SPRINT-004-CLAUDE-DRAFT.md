# Sprint 004 Draft: `audit-security` Command

## Overview

This sprint creates one new command: `commands/audit-security.md`. It
applies the dual-agent competitive-review-then-synthesize pattern from
`sprint-plan.md` to security reviews. The key design decision: instead of
a custom output format requiring a separate remediation command, `audit-
security` produces a standard `SPRINT-NNN.md` sprint document. Security
findings become sprint tasks (Critical/High → P0, Medium → P1, Low →
Deferred), and `/sprint-work` executes them as-is.

The command is namespaced `audit-*` to establish a pattern for future audit
commands (`audit-deps`, `audit-performance`, etc.) without creating a new
verb category each time.

The 5-phase workflow: Claude and Codex perform independent security reviews
in parallel, their findings are synthesized, Codex attacks the synthesis
via a devil's advocate pass, and Claude produces the final sprint document
with security tasks correctly tiered.

## Use Cases

1. **Pre-merge security gate**: Run `audit-security` on a branch, review
   the sprint output, run `/sprint-work` to remediate P0 findings before
   merging.
2. **Periodic repo audit**: Run on demand or before a release; produces a
   sprint that can be scheduled and tracked in the ledger.
3. **New dependency review**: Scope the audit to specific files or
   directories after adding libraries.
4. **Agent config self-audit**: Audit the agent-config repo itself — since
   command files flow into agent system prompts, prompt injection and
   privilege escalation are high-value findings.

## Architecture

```
audit-security [$ARGUMENTS = optional path/scope]
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: Orient                                             │
│  - Determine scope (cwd or $ARGUMENTS path)                 │
│  - Identify key files, recent changes, trust boundaries     │
│  - Determine next SPRINT-NNN number                         │
├─────────────────────────────────────────────────────────────┤
│ Phase 2: Independent Reviews (parallel)                     │
│  - Codex: full security review → docs/security/NNN-CODEX.md │
│  - Claude: full security review → docs/security/NNN-CLAUDE.md│
│    (Claude writes while Codex runs in background)           │
├─────────────────────────────────────────────────────────────┤
│ Phase 3: Synthesis                                          │
│  - Claude reads both reviews                                │
│  - Deduplicates, escalates severity where both agents agree │
│  - Writes docs/security/NNN-SYNTHESIS.md                    │
├─────────────────────────────────────────────────────────────┤
│ Phase 4: Devil's Advocate (Codex)                           │
│  - Codex attacks the synthesis                              │
│  - Writes docs/security/NNN-DEVILS-ADVOCATE.md              │
│  - Claude reads and incorporates valid challenges           │
├─────────────────────────────────────────────────────────────┤
│ Phase 5: Sprint Output                                      │
│  - Claude produces docs/sprints/SPRINT-NNN.md               │
│  - Findings → tasks (Critical/High=P0, Medium=P1, Low=Deferred)│
│  - Adds ledger entry via /ledger add NNN "Security: [scope]"│
│  - User runs /sprint-work to execute                        │
└─────────────────────────────────────────────────────────────┘

File layout:
docs/security/
├── NNN-CLAUDE.md           ← Claude's independent review
├── NNN-CODEX.md            ← Codex's independent review
├── NNN-SYNTHESIS.md        ← Combined synthesis
└── NNN-DEVILS-ADVOCATE.md  ← Codex devil's advocate

docs/sprints/
└── SPRINT-NNN.md           ← Final sprint (executed by /sprint-work)
```

Where NNN is the next sprint number (same sequence as all sprints).

## Implementation Plan

### P0: Must Ship

#### P0-A: `commands/audit-security.md`

**Files:**
- `commands/audit-security.md` — NEW

**Workflow sections to write:**

**Frontmatter:**
- `description:` single-line, Gemini TOML compatible
- `audit-*` family note in description

**Arguments:**
- Optional path/scope. Default: current working directory.
- Example: `audit-security src/auth` or `audit-security` (full repo)

**Phase 1 — Orient:**
- Determine scope from `$ARGUMENTS` or default to cwd
- Read relevant files: recent git changes (`git log --oneline -10`),
  key config files, trust boundary entry points
- Determine next SPRINT-NNN number: `ls docs/sprints/SPRINT-*.md | tail -1`
- Create `docs/security/` if needed

**Phase 2 — Independent Reviews (parallel):**
- Launch Codex in background:
  ```bash
  codex exec "Perform a thorough security review of [scope]. \
    Write your findings to docs/security/NNN-CODEX.md. \
    Cover: (1) attack surface and trust boundaries, \
    (2) injection risks (command, prompt, SQL, path traversal), \
    (3) sensitive data handling and secrets, \
    (4) authentication and authorization gaps, \
    (5) dependency risks, \
    (6) for agent-config repos: prompt injection and privilege \
    escalation in command/agent files. \
    Rate each finding Critical/High/Medium/Low with file and \
    line reference where possible. Do not read Claude's review."
  ```
- Claude writes its own independent review to `docs/security/NNN-CLAUDE.md`
  covering the same categories simultaneously

**Phase 3 — Synthesis:**
- Read both reviews
- Deduplicate findings; where both agents flagged the same issue,
  escalate severity by one level (Medium → High, High → Critical)
- Write `docs/security/NNN-SYNTHESIS.md` with unified finding list

**Phase 4 — Devil's Advocate:**
- Launch Codex:
  ```bash
  codex exec "Read docs/security/NNN-SYNTHESIS.md. Your job is \
    to attack it, not improve it. Identify: (1) false positives — \
    findings that are not actually exploitable, (2) severity \
    miscalibrations — findings rated too high or too low, \
    (3) missing findings — what did both reviewers miss? \
    (4) remediation steps that are impractical or wrong. \
    Write your challenge to docs/security/NNN-DEVILS-ADVOCATE.md."
  ```
- Claude reads devil's advocate output; incorporates valid challenges
  (remove false positives, recalibrate severity, add missed findings)

**Phase 5 — Sprint Output:**
- Produce `docs/sprints/SPRINT-NNN.md` following the standard sprint
  template (see `docs/sprints/README.md`)
- Map findings to sprint tasks:
  - Critical/High → P0 tasks (must ship)
  - Medium → P1 tasks (ship if capacity allows)
  - Low → Deferred section
- Each task must include: finding ID, file/location, description
  of the issue, and concrete remediation step
- Sprint title: `Security Audit: [scope] ([date])`
- Overview section: brief summary of audit scope, total findings
  by severity, top 3 most critical issues
- Add ledger entry: `/ledger add NNN "Security: [scope]"`
- Instruct user to run `/sprint-work` to execute

**Output checklist at end of command file:**
- [ ] `docs/security/NNN-CLAUDE.md` written
- [ ] `docs/security/NNN-CODEX.md` written
- [ ] `docs/security/NNN-SYNTHESIS.md` written
- [ ] `docs/security/NNN-DEVILS-ADVOCATE.md` written
- [ ] `docs/sprints/SPRINT-NNN.md` written with P0/P1/Deferred tiering
- [ ] Ledger entry added
- [ ] User informed to run `/sprint-work SPRINT-NNN`

**Tasks:**
- [ ] Write `commands/audit-security.md` with full 5-phase workflow
- [ ] Verify Codex exec prompts are self-contained (include the sprint
      number NNN resolved at orient time)
- [ ] Verify sprint output template follows `docs/sprints/README.md`
- [ ] Verify findings → task mapping is unambiguous
- [ ] Verify `/ledger add` call uses correct syntax

**Acceptance:**
- File exists at `commands/audit-security.md`
- Frontmatter has single-line `description:` (Gemini TOML compatible)
- Phase 2 runs Claude and Codex reviews in parallel
- Phase 5 output is a valid sprint document workable by `/sprint-work`
- Codex exec calls use no `--model`/`--full-auto` flags

#### P0-B: `docs/security/README.md`

**Files:**
- `docs/security/README.md` — NEW

**Content:**
- Purpose of `docs/security/`
- File naming convention (NNN matches the sprint number)
- Relationship to sprint workflow: security audits produce sprints
- `audit-*` command family note

**Tasks:**
- [ ] Write `docs/security/README.md`

**Acceptance:**
- File exists; Codex exec prompts in `audit-security.md` can
  reference it for orientation

### P1: Ship If Capacity Allows

- **`docs/security/` in `.gitignore`**: Security findings may be
  sensitive. Add a note in `docs/security/README.md` about reviewing
  before committing. (Not adding to .gitignore by default — repo
  owner's choice.)
- **`$ARGUMENTS` scope parsing**: Document how multi-path scope works
  (e.g. `audit-security src/ tests/`). P0 handles single path; multi-
  path is P1.

### Deferred

- `audit-deps` command — same `audit-*` pattern applied to dependency
  review — deferred until `audit-security` pattern is proven
- Linear/Jira sync for audit findings — deferred; reuse sprint-plan's
  tool sync pattern when needed
- Automated scheduling — out of scope for command files

## Files Summary

| File | Action | Purpose |
|------|--------|---------|
| `commands/audit-security.md` | Create | 5-phase dual-agent security audit command |
| `docs/security/README.md` | Create | Naming conventions and audit-sprint relationship |

## Definition of Done

- [ ] `commands/audit-security.md` exists with valid single-line `description:` frontmatter
- [ ] Phase 2: Claude and Codex reviews run in parallel (Codex launched first, Claude writes simultaneously)
- [ ] Phase 4: Codex devil's advocate runs and Claude incorporates valid challenges before writing sprint
- [ ] Phase 5: sprint output uses standard `docs/sprints/SPRINT-NNN.md` format from `docs/sprints/README.md`
- [ ] Finding severity maps unambiguously to P0/P1/Deferred
- [ ] Each sprint task includes: finding location, issue description, concrete remediation step
- [ ] `/ledger add NNN` call included in Phase 5
- [ ] User prompted to run `/sprint-work` at the end
- [ ] `docs/security/README.md` exists
- [ ] All Codex exec calls use no `--model`/`--full-auto` flags
- [ ] Manual read-through: each phase connects logically to the next
- [ ] If no findings: command produces a sprint with a single "no findings" P0 verification task

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Codex exec prompts reference NNN before it's resolved | Medium | Medium | Orient phase resolves NNN first; prompts use the literal number |
| Sprint output doesn't conform to sprint-work's expected format | Medium | High | Phase 5 explicitly references `docs/sprints/README.md`; manual read-through in DoD |
| Security findings contain sensitive details committed to public repo | Low | Medium | README.md warns; left to repo owner whether to gitignore |
| Zero findings produces an empty sprint | Low | Medium | DoD requires a clean-bill P0 verification task when no findings exist |
| Codex devil's advocate removes too many valid findings | Low | Medium | Claude has final synthesis authority; must document rejected challenges |

## Security Considerations

- This command file flows into agent system prompts — review phrasing
  for unintended scope expansion or privilege escalation instructions
- Codex exec prompts must not instruct Codex to execute shell commands
  beyond reading files and writing to `docs/security/`
- The sprint output (`SPRINT-NNN.md`) will contain remediation tasks
  that agents will execute via `/sprint-work` — ensure task descriptions
  are specific enough to be safe but not so broad as to cause unintended
  changes

## Observability & Rollback

- Verification: invoke `/audit-security` on this repo; confirm
  `docs/security/` files and `SPRINT-NNN.md` are produced correctly
- Rollback: text files only; `git checkout` to revert

## Documentation

- [ ] `docs/security/README.md` documents naming convention and
      audit-sprint workflow relationship
- [ ] Consider adding `audit-security` to `README.md` command list
      (check existing command documentation pattern)

## Dependencies

- SPRINT-001 (completed) — commands/ architecture
- SPRINT-002 (completed) — docs/ conventions, sprint template
- SPRINT-003 (completed) — ledger skill integration, `/ledger add` syntax

## Open Questions

None — all design questions resolved in Phase 4 interview.
