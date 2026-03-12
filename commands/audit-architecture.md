---
description: >-
  Dual-agent architecture audit — Claude and Codex review structural decisions
  independently, synthesize, devil's advocate pass, output as executable sprint
---

# Architecture Audit: Dual-Agent Review

You are orchestrating a dual-agent architecture audit that produces an
executable sprint document. Claude and Codex review independently,
findings are synthesized, Codex attacks the synthesis, and the final
output is a standard `SPRINT-NNN.md` sprint worked by `/sprint-work`.

This command is part of the `audit-*` family and follows the same
5-phase workflow as `audit-security`. The `audit-architecture` finding
schema extends the core schema with `Pattern/Principle`, `Alternative`,
and `Migration Cost` columns that anchor each finding to a named
architectural principle or observable trade-off.

**Inherent limitations**: LLM architectural review cannot replace domain
knowledge about runtime behavior, team conventions, or organizational
constraints. The output is a structured starting point for team
discussion, not a mandate to refactor. Architecture is uniquely
susceptible to LLM overconfidence: unlike security (external anchors:
CVEs, exploitability) or accessibility (external anchors: WCAG criteria),
architectural "correctness" is context-dependent. Treat every finding as
a hypothesis requiring team validation before execution. The evidence
discipline (named principle + concrete alternative) reduces noise but
cannot eliminate it.

## Arguments

`$ARGUMENTS` is an optional path or paths to audit. Examples:

- `audit-architecture` — audits the current working directory
- `audit-architecture src/` — scopes the audit to `src/`
- `audit-architecture commands/ skills/` — scopes to multiple paths

If no argument is provided, the scope is the current working directory.
Scope is validated as a path in Phase 1 before being used anywhere else —
raw user input is never interpolated into shell strings.

## Workflow Overview

This is a **5-phase workflow**:

1. **Orient** — Validate scope, survey structure, identify module
   boundaries and dependency direction, determine next sprint number
2. **Independent Reviews** — Claude and Codex review in parallel (Codex
   in background, Claude simultaneously)
3. **Synthesis** — Deduplicate findings; calibrate severity on evidence;
   note single-reviewer findings
4. **Devil's Advocate** — Codex attacks the synthesis for false positives
   (including intentional design choices), severity miscalibrations,
   missing findings, and impractical alternatives
5. **Sprint Output** — Produce `SPRINT-NNN.md` with findings as tasks;
   register in ledger; hand off to `/sprint-work`

---

## Finding Schema

`audit-architecture` extends the `audit-*` base schema with
architecture-specific columns. All intermediate audit files must use
this table format so synthesis and devil's advocate phases operate on
consistent data:

**Core columns** (preserved from `audit-*` base):
`ID`, `Severity`, `Title`, `Location`, `Why It Matters`,
`Recommended Fix`, `Evidence/Notes`

**Architecture extension columns** (added after `Location`):
`Pattern/Principle`, `Alternative`, `Migration Cost`

```
| ID | Severity | Title | Location | Pattern/Principle | Why It Matters | Alternative | Migration Cost | Recommended Fix | Evidence/Notes |
|----|----------|-------|----------|-------------------|----------------|-------------|----------------|-----------------|----------------|
| A001 | High | Example | path/to/file:line | Separation of Concerns | Impact explanation | Specific alternative approach | Medium | Concrete fix step | Observable evidence |
```

**ID prefix convention:**
- Claude's review: `A001`, `A002`... (Architecture)
- Codex's review: `C001`, `C002`... (Codex)
- Synthesis: `S001`, `S002`... (Synthesis)

**Severity levels:** Critical, High, Medium, Low

**Severity anchors:**
- Critical: prevents correct behavior or creates an unmaintainable trajectory
- High: significantly impedes extensibility, causes repeated defects, or
  creates systematic blind spots
- Medium: notable friction, inconsistency, or a pattern that degrades over time
- Low: minor improvement backed by a named principle

Severity is assessed on evidence: impact on maintainability, extensibility,
defect rate. Agreement between reviewers raises **confidence**, not severity.

**Pattern/Principle column**: the named architectural rule or observable
trade-off in tension. Examples: `SOLID:SRP`, `DRY`, `Separation of Concerns`,
`Low Coupling`, `High Cohesion`, `YAGNI`, `Explicit over Implicit`. For
agent-config repos: `Command/Skill Boundary`, `Agent Scope Creep`,
`Prompt Composability`. When no formal principle applies, describe the
trade-off explicitly (e.g., "Coupling: invocation config embedded in output
template").

**Alternative column**: the better structural design to move toward — not
"refactor this" but a specific alternative approach. When no clear alternative
exists, document "Investigate options for [issue]" as the alternative — this
is preferable to forcing an overconfident redesign proposal.

**Migration Cost column**: `Low`, `Medium`, or `High` — effort to change,
including coordination risk and touching shared boundaries.

**Evidence discipline**: a finding without a named `Pattern/Principle` (or
explicit trade-off description) and a concrete `Alternative` is **not a valid
finding** and must be skipped. When principle labels feel redundant, prefer
concrete trade-off language. Opinion-only observations without a named
architectural principle or observable structural tension must be omitted.

---

## Phase 1: Orient

**Goal**: Validate scope, survey structure and module boundaries, check
for pre-existing audit artifacts, and determine the next sprint number.

### Orient Steps

1. **Validate and resolve scope** from `$ARGUMENTS`:
   - If no argument: scope is the current working directory
   - If arguments are provided: verify each path exists via filesystem
     check before storing as resolved scope — do not proceed with a
     path that does not exist
   - Supports multiple space-separated paths; store all resolved paths
   - Scope automatically excludes: `build/`, `dist/`, `.next/`,
     lockfiles (`package-lock.json`, `yarn.lock`, `Pipfile.lock`),
     `vendor/`, `node_modules/`, generated files, and binary assets
     unless explicitly included in `$ARGUMENTS`
   - Store the resolved scope — do not use raw `$ARGUMENTS` text in
     any Codex exec prompt string

2. **Survey the scope** (minimum discovery before findings are allowed):
   - Identify owned entry points and major module boundaries
   - Survey `git log --oneline -10` for recent structural changes
   - Identify dependency direction or import hotspots where visible
   - For agent-config repos: survey `commands/`, `skills/`, `agents/`,
     `prompts/`, `scripts/` — these define the agent system architecture
   - Read at least 5 representative files before generalizing a pattern —
     do not generalize from top-level directory structure alone
   - If no recognizable formal structure is found: warn
     ("No formal structure detected in [scope] — findings may be limited")
     and continue; do not stop — every codebase has architecture

3. **Check for pre-existing artifacts**:
   - Determine next sprint number:
     ```bash
     ls docs/sprints/SPRINT-*.md | tail -1
     ```
     Extract NNN and increment. If no sprint files exist, start at `001`.
     Call this `AUDIT_NNN` — use the literal number in all subsequent
     file references, not a variable.
   - Before proceeding: check whether `docs/architecture/AUDIT_NNN-*.md`
     files already exist for the chosen sprint number. If they do, warn
     the user and stop — do not silently overwrite a previous audit run.

4. **Create output directory**:
   ```bash
   mkdir -p docs/architecture
   ```

### Orient Deliverable

A brief orientation note (3-5 bullets) covering:
- Resolved scope path(s) and what is included/excluded
- Key module boundaries and structural patterns identified
- The next sprint number (`AUDIT_NNN`)
- Any immediately obvious high-priority structural areas

---

## Phase 2: Independent Reviews (Parallel)

**Goal**: Get two independent architectural perspectives without
cross-contamination.

### Step 1 — Launch Codex in Background

Run this command, substituting the resolved scope and `AUDIT_NNN`.
This prompt is self-contained — AUDIT_NNN and the resolved scope path
must be embedded literally (not as shell variables):

```bash
codex exec "Perform a thorough architecture review of [RESOLVED_SCOPE]. \
  Write all findings to docs/architecture/AUDIT_NNN-CODEX.md using this \
  exact table format for each finding: \
  | ID | Severity | Title | Location | Pattern/Principle | Why It Matters | \
  Alternative | Migration Cost | Recommended Fix | Evidence/Notes | \
  where ID uses prefix C (e.g. C001, C002). \
  Review these 7 categories: \
  (1) Module boundaries and separation of concerns — are responsibilities \
  clearly separated? Is business logic mixed with infrastructure or output? \
  (2) Coupling and cohesion — are components tightly coupled where they \
  should be independent? Do related things live together? \
  (3) Naming and conventions — are names consistent, intention-revealing, \
  and following a documented convention? \
  (4) Data flow and state management — is data flow easy to trace? Is state \
  centralized or scattered? \
  (5) Extensibility and DRY — is there unnecessary duplication? Are extension \
  points well-defined or does new behavior require copy-paste? \
  (6) YAGNI and over-engineering — is there abstraction without current use? \
  Configurability no one needs? \
  (7) For agent-config repos (commands/, skills/, agents/, prompts/, \
  scripts/): how are commands and skills structured? Is the boundary between \
  commands (user-facing workflows) and skills (reusable components) clear? \
  Are agents scoped appropriately? Is the invocation chain traceable? Is \
  there prompt duplication or inconsistent phase structure across command \
  files? \
  Every finding MUST include a named Pattern/Principle (or explicit \
  trade-off description) and a concrete Alternative. Skip any observation \
  that is purely aesthetic preference without a named architectural principle \
  or observable structural tension. When no clear alternative exists, write \
  'Investigate options for [issue]' as the Alternative rather than forcing \
  an overconfident redesign proposal. \
  Rate severity on: does this prevent correct behavior, impede \
  extensibility, or create systematic debt? \
  Exclude from scope: build/, dist/, lockfiles, vendored/third-party code, \
  generated files, binary assets. \
  Only write to docs/architecture/. Do not run shell commands beyond \
  reading files. Do not read or reference any other review file."
```

### Step 2 — Claude's Independent Review (Simultaneous)

While Codex runs, write your own independent architecture review to
`docs/architecture/AUDIT_NNN-CLAUDE.md` using the same finding schema
(ID prefix `A`). Cover the same 7 categories:

1. **Module boundaries and separation of concerns** — are responsibilities
   clearly separated? Is business logic mixed with infrastructure or output?
2. **Coupling and cohesion** — are components tightly coupled where they
   should be independent? Do related things live together?
3. **Naming and conventions** — are names consistent, intention-revealing,
   and following a documented convention?
4. **Data flow and state management** — is data flow easy to trace? Is
   state centralized or scattered?
5. **Extensibility and DRY** — is there unnecessary duplication? Are
   extension points well-defined or does new behavior require copy-paste?
6. **YAGNI and over-engineering** — is there abstraction without current
   use? Configurability no one needs?
7. **Agent-config specific** — how are commands and skills structured?
   Is the boundary between commands (user-facing workflows) and skills
   (reusable components) clear? Are agents scoped appropriately? Is the
   invocation chain traceable? Is there prompt duplication or inconsistent
   phase structure across command files? When auditing an agent-config
   repo, apply extra scrutiny — these are your own instruction files and
   you may have systematic blind spots here.

Evidence discipline applies to your own review: every finding must have
a named `Pattern/Principle` and a concrete `Alternative`. Skip
opinion-only observations without a named principle or observable tension.
Read at least 5 representative files before generalizing any pattern.

Wait for Codex to finish before proceeding to Phase 3.

---

## Phase 3: Synthesis

**Goal**: Produce a unified, deduplicated finding list with calibrated
severity and confidence.

### Synthesis Steps

1. **Verify both reviews exist and are non-empty**:
   - Check `docs/architecture/AUDIT_NNN-CLAUDE.md` and
     `docs/architecture/AUDIT_NNN-CODEX.md` exist and contain at least
     one finding row
   - If one file is missing or empty: proceed with single-agent synthesis
     and add a prominent warning at the top of
     `AUDIT_NNN-SYNTHESIS.md`: "⚠️ Single-agent synthesis — [agent]
     review was unavailable. Coverage may be incomplete."

2. **Deduplicate findings**:
   - Compare both reviews for overlapping findings
   - When the same structural issue appears in both, merge into one
     synthesis row — note both source IDs (e.g. `A002, C003`)
   - When merging: preserve the most specific `Alternative` and the
     best `Evidence/Notes` from either reviewer; preserve the most
     specific `Location`
   - When the same pattern-violation appears across many locations,
     create one finding and document extent in `Evidence/Notes`
   - For multi-path scopes: merge findings across paths; when path
     context is material to a finding, preserve it in `Location`
   - Agreement = higher confidence, not higher severity

3. **Calibrate severity**:
   - Re-evaluate severity based on evidence: impact on maintainability,
     extensibility, defect rate
   - Do not automatically escalate severity because both reviewers
     flagged the same issue

4. **Write synthesis**:

   Write `docs/architecture/AUDIT_NNN-SYNTHESIS.md`:

   ```markdown
   # Architecture Audit Synthesis — AUDIT_NNN

   ## Scope
   [Resolved scope path(s)]

   ## Summary
   - Total findings: N (Critical: X, High: X, Medium: X, Low: X)
   - Reviewers: Claude (A-prefix), Codex (C-prefix)
   - [Single-agent warning if applicable]

   ## Unified Findings

   | ID | Severity | Title | Location | Pattern/Principle | Why It Matters | Alternative | Migration Cost | Recommended Fix | Evidence/Notes | Sources |
   |----|----------|-------|----------|-------------------|----------------|-------------|----------------|-----------------|----------------|---------|
   | S001 | ... | ... | ... | ... | ... | ... | ... | ... | ... | A001, C002 |

   ## Findings Present in Only One Review
   [Note findings not corroborated by the other reviewer and why
   retained or dropped]

   ## Rejected Devil's Advocate Challenges
   [Added after Phase 4]
   | Finding/Claim | Reason Rejected |
   |---|---|
   ```

Phase 3 is complete when `AUDIT_NNN-SYNTHESIS.md` is written.

---

## Phase 4: Devil's Advocate

**Goal**: Challenge the synthesis for false positives (including
intentional design choices), severity miscalibrations, missed findings,
and impractical alternatives.

### Step 1 — Launch Codex Devil's Advocate

```bash
codex exec "Read docs/architecture/AUDIT_NNN-SYNTHESIS.md. Your job is \
  to attack it, not improve it. Write your challenge to \
  docs/architecture/AUDIT_NNN-DEVILS-ADVOCATE.md covering: \
  (1) False positives — 'violations' that are intentional design decisions \
  appropriate for this project's scale or constraints, or principles cited \
  without observed evidence. \
  (2) Severity miscalibrations — findings rated too high or too low given \
  actual impact on maintainability and extensibility. \
  (3) Missing findings — structural issues both reviewers missed. \
  (4) Alternatives that are impractical, create worse problems, or have \
  misestimated migration cost. \
  Be specific. Every challenge must cite the finding ID. \
  Only write to docs/architecture/. Do not run shell commands beyond \
  reading files."
```

### Step 2 — Incorporate Valid Challenges

Once `AUDIT_NNN-DEVILS-ADVOCATE.md` is written, read it and:

- **Remove** confirmed false positives from the working finding list
- **Recalibrate** severity where the challenge is valid and evidence
  supports it
- **Add** genuinely missed findings with new synthesis IDs
- **Document every rejected challenge** with explicit reasoning in the
  "Rejected Devil's Advocate Challenges" section of
  `AUDIT_NNN-SYNTHESIS.md`:

  ```markdown
  ## Rejected Devil's Advocate Challenges

  | Finding/Claim | Reason Rejected |
  |---|---|
  | [Claim from devil's advocate] | [Why it was not accepted] |
  ```

Phase 4 is complete when challenges are incorporated and all rejections
are documented with explicit reasoning.

---

## Phase 5: Sprint Output

**Goal**: Produce a standard `SPRINT-NNN.md` sprint document with
architecture findings as executable tasks.

### Sprint Mapping Rules

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

**Migration Cost nuance**: High findings with `Migration Cost=High`
are placed in P0, but the task description must include the note:
"Requires team alignment and design discussion before execution — do
not begin implementation without broader agreement."

Each sprint task must include:
- Finding ID (from synthesis)
- Location (file and line where applicable)
- Pattern/Principle in tension
- Issue description
- Specific alternative approach (the target design)
- Migration cost
- Concrete remediation step (the implementation action)
- Verification: how to confirm the fix is correct

Tasks must be scoped to specific, enumerable changes — no task broadly
modifies a directory without listing the affected files.

### No-Findings Case

If the synthesis contains zero findings after Phase 4:
- Create a single P0 task: "Verify no findings — [scope], [date]"
- The task description must document: scope covered, all 7 categories
  reviewed (list them), date, reviewer agents, approximate number of
  files read, and specific areas that received the most scrutiny
- Do not produce an empty sprint

### Multi-Path Scope in Title

When multiple paths were audited, sprint title is:
`Architecture Audit: [path1], [path2] ([YYYY-MM-DD])`
Ledger entry uses the same comma-separated scope string.

### Write the Sprint

Create `docs/sprints/SPRINT-NNN.md` following the standard sprint
template from `docs/sprints/README.md`:

```markdown
# Sprint NNN: Architecture Audit — [scope] ([YYYY-MM-DD])

## Overview

[1-2 paragraphs: audit scope, total findings by severity, top 3 issues.
Remind the reader that LLM architectural review is a hypothesis-generating
starting point — findings require team validation before execution.]

## Audit Summary

| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Total | N |

Intermediate audit artifacts: `docs/architecture/AUDIT_NNN-*.md`

## Implementation Plan

### P0: Must Ship

[One task per Critical/High finding]

**Task: [Finding ID] — [Title]**
- Location: `path/to/file:line`
- Pattern/Principle: [named principle or trade-off]
- Issue: [architectural issue description]
- Alternative: [target design to move toward]
- Migration Cost: [Low/Medium/High]
- Remediation: [specific implementation step]
- Verification: [how to confirm the fix is correct]
- [For High + Migration Cost=High: "Requires team alignment and design
  discussion before execution — do not begin implementation without
  broader agreement."]

### P1: Ship If Capacity Allows

[One task per Medium finding, same format]

### Deferred

[Low findings with brief rationale]

## Definition of Done

- [ ] All P0 tasks completed and verified
- [ ] No new Critical/High findings introduced by the remediations
- [ ] P0 tasks with Migration Cost=High reviewed with team before
      implementation begins
- [ ] Reviewer confirms task ordering was appropriate for dependencies
[add finding-specific verification items]

## Architecture Considerations

- Review task ordering before executing — architecture changes often
  have sequencing dependencies
- Findings are LLM hypotheses under shallow discovery — validate each
  P0/P1 finding against team knowledge before executing tasks
- P0 tasks with Migration Cost=High require team alignment before
  implementation; do not begin those without broader design discussion

## Dependencies

- AUDIT_NNN intermediate files: `docs/architecture/AUDIT_NNN-*.md`
```

### Register and Hand Off

1. Register the sprint in the ledger using the `/ledger add NNN
   "Architecture: [scope]"` skill. If it fails, instruct the user to
   run it manually:
   ```
   /ledger add NNN "Architecture: [scope]"
   ```

2. Inform the user:

   > ✅ Architecture audit complete. SPRINT-NNN has been created and
   > added to the ledger.
   >
   > **Important**: architecture findings are LLM hypotheses under
   > shallow discovery — validate each P0/P1 finding against team
   > knowledge before executing tasks.
   >
   > **Before running /sprint-work**: review task ordering in
   > `docs/sprints/SPRINT-NNN.md` — architecture changes often have
   > sequencing dependencies. P0 tasks with Migration Cost=High require
   > team alignment before implementation; do not begin those without
   > broader design discussion.
   >
   > When ready: `/sprint-work NNN`

---

## Output Checklist

At the end of this workflow, verify:

- [ ] `docs/architecture/AUDIT_NNN-CLAUDE.md` — written using finding
      schema with extension columns, ID prefix A
- [ ] `docs/architecture/AUDIT_NNN-CODEX.md` — written using finding
      schema with extension columns, ID prefix C
- [ ] Both files are non-empty (or single-agent warning added to synthesis)
- [ ] `docs/architecture/AUDIT_NNN-SYNTHESIS.md` — unified findings with
      canonical S-prefix IDs, all extension columns preserved
- [ ] `docs/architecture/AUDIT_NNN-DEVILS-ADVOCATE.md` — Codex challenge
      complete
- [ ] Valid devil's advocate challenges incorporated into synthesis
- [ ] Every rejected challenge documented with explicit reasoning
- [ ] `docs/sprints/SPRINT-NNN.md` — written with P0/P1/Deferred tiering
- [ ] Each P0/P1 task has: finding ID, location, principle, alternative,
      migration cost, remediation, verification
- [ ] High + Migration Cost=High tasks include "requires team alignment" note
- [ ] No-findings case handled if applicable (with files-read and
      scrutiny-areas documented)
- [ ] Multi-path scope carried through: Phase 2 prompts, sprint title,
      ledger entry
- [ ] `/ledger add NNN` completed (or user instructed to run manually)
- [ ] User instructed to review task ordering and migration costs before
      running `/sprint-work NNN`
- [ ] No `--model` or `--full-auto` flags in any Codex exec call
- [ ] No raw `$ARGUMENTS` text in any Codex exec prompt

---

## Reference

- Sprint conventions: `docs/sprints/README.md`
- Architecture audit artifacts: `docs/architecture/`
- Audit family: `audit-*` commands in `commands/`
- Base pattern: `commands/audit-security.md`
