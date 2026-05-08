---
name: audit-architecture
description: Dual-agent architecture audit — Claude and Codex review structural decisions independently, synthesize, devil's advocate pass, output as findings report. Invoke with a scope path or leave empty to audit the current working directory.
---

# Architecture Audit: Dual-Agent Review

You are orchestrating a dual-agent architecture audit that produces an
findings report. Claude and Codex review independently,
findings are synthesized, Codex attacks the synthesis, and the final
output is a sprint document written to `$AUDIT_DIR/REPORT.md`.

The scope to audit is provided in your input prompt. If no scope is
specified, audit the current working directory.

The `audit-architecture` finding schema extends the core schema with
`Pattern/Principle`, `Alternative`, and `Migration Cost` columns that
anchor each finding to a named architectural principle or observable
trade-off.

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

## Scope Handling

Parse your input prompt for a path or paths to audit. Examples:
- No path specified → scope is the current working directory
- `src/` → scope is `src/`
- `commands/ skills/` → scope is multiple paths

Scope is validated as a path in Phase 1 before being used anywhere else —
raw user input is never interpolated into shell strings.

## Workflow Overview

This is a **5-phase workflow**:

1. **Orient** — Validate scope, survey structure, identify module
   boundaries and dependency direction
2. **Independent Reviews** — Claude and Codex review in parallel (Codex
   in background, Claude simultaneously)
3. **Synthesis** — Deduplicate findings; calibrate severity on evidence;
   note single-reviewer findings
4. **Devil's Advocate** — Codex attacks the synthesis for false positives
   (including intentional design choices), severity miscalibrations,
   missing findings, and impractical alternatives
5. **Report Output** — Produce `$AUDIT_DIR/REPORT.md` with findings as tasks for human review;
   present to user for review

---

## Finding Schema

All intermediate audit files must use this table format:

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

**Pattern/Principle column**: the named architectural rule or observable
trade-off in tension. Examples: `SOLID:SRP`, `DRY`, `Separation of Concerns`,
`Low Coupling`, `High Cohesion`, `YAGNI`, `Explicit over Implicit`. For
agent-config repos: `Command/Skill Boundary`, `Agent Scope Creep`,
`Prompt Composability`. When no formal principle applies, describe the
trade-off explicitly.

**Alternative column**: the better structural design to move toward — not
"refactor this" but a specific alternative approach. When no clear alternative
exists, document "Investigate options for [issue]" as the alternative.

**Migration Cost column**: `Low`, `Medium`, or `High` — effort to change,
including coordination risk and touching shared boundaries.

**Evidence discipline**: a finding without a named `Pattern/Principle` and a
concrete `Alternative` is **not a valid finding** and must be skipped.

---

## Phase 1: Orient

**Goal**: Validate scope, survey structure and module boundaries, check
for pre-existing audit artifacts, and determine the output location.

### Orient Steps

1. **Validate and resolve scope** from the input prompt:
   - If no path specified: scope is the current working directory
   - If paths are provided: verify each path exists via filesystem
     check before storing — do not proceed with a path that does not exist
   - Supports multiple space-separated paths; store all resolved paths
   - Scope automatically excludes: `build/`, `dist/`, `.next/`,
     lockfiles, `vendor/`, `node_modules/`, generated files, and
     binary assets unless explicitly included
   - Store the resolved scope — do not use raw input text in any
     Codex exec prompt string

2. **Survey the scope** (minimum discovery before findings are allowed):
   - Identify owned entry points and major module boundaries
   - Survey `git log --oneline -10` for recent structural changes
   - Identify dependency direction or import hotspots where visible
   - For agent-config repos: survey `commands/`, `skills/`, `agents/`,
     `prompts/`, `scripts/` — these define the agent system architecture
   - Read at least 5 representative files before generalizing a pattern —
     do not generalize from top-level directory structure alone
   - If no recognizable formal structure is found: warn and continue

3. **Determine output location**:
   ```bash
   REMOTE=$(git remote get-url upstream 2>/dev/null || git remote get-url origin 2>/dev/null || echo "")
   ORG_REPO=$(echo "$REMOTE" | sed 's|.*github\.com[:/]||; s|\.git$||')
   REPORTS_BASE="$HOME/Reports/$ORG_REPO"
   REPORT_TS=$(date +%Y-%m-%dT%H-%M-%S)
   AUDIT_DIR="$REPORTS_BASE/audits/$REPORT_TS-architecture"
   mkdir -p "$AUDIT_DIR"
   ```
   Each audit run gets its own timestamped folder under
   `~/Reports/<org>/<repo>/audits/`, matching the layout
   `/sprint-plan` uses for sprint sessions. All audit artifacts
   for this run live in `$AUDIT_DIR`.

### Orient Deliverable

A brief orientation note (3-5 bullets) covering:
- Resolved scope path(s) and what is included/excluded
- Key module boundaries and structural patterns identified
- Audit output directory (`AUDIT_DIR`) — all artifacts for this audit run live here
- Any immediately obvious high-priority structural areas

---

## Phase 2: Independent Reviews (Parallel)

**Goal**: Get two independent architectural perspectives without
cross-contamination.

### Step 1 — Launch Codex in Background

Run this command, substituting the resolved scope and the literal value of `AUDIT_DIR`.
The output path and resolved scope path must be embedded literally (not as shell variables):

```bash
codex exec "Perform a thorough architecture review of [RESOLVED_SCOPE]. \
  Write all findings to $AUDIT_DIR/codex.md using this \
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
  Every finding MUST include a named Pattern/Principle and a concrete \
  Alternative. Skip any observation that is purely aesthetic preference \
  without a named architectural principle or observable structural tension. \
  Rate severity on: does this prevent correct behavior, impede \
  extensibility, or create systematic debt? \
  Exclude from scope: build/, dist/, lockfiles, vendored/third-party code, \
  generated files, binary assets. \
  Only write to $AUDIT_DIR/. Do not run shell commands beyond \
  reading files. Do not read or reference any other review file."
```

### Step 2 — Claude's Independent Review (Simultaneous)

While Codex runs, write your own independent architecture review to
`$AUDIT_DIR/claude.md` using the same finding schema
(ID prefix `A`). Cover the same 7 categories:

1. **Module boundaries and separation of concerns**
2. **Coupling and cohesion**
3. **Naming and conventions**
4. **Data flow and state management**
5. **Extensibility and DRY**
6. **YAGNI and over-engineering**
7. **Agent-config specific** — apply extra scrutiny when auditing an
   agent-config repo — these are your own instruction files and you
   may have systematic blind spots here.

Evidence discipline applies to your own review: every finding must have
a named `Pattern/Principle` and a concrete `Alternative`. Read at least
5 representative files before generalizing any pattern.

Wait for Codex to finish before proceeding to Phase 3.

---

## Phase 3: Synthesis

**Goal**: Produce a unified, deduplicated finding list with calibrated
severity and confidence.

### Synthesis Steps

1. **Verify both reviews exist and are non-empty**:
   - If one is missing or empty: proceed with single-agent synthesis
     and add warning: "⚠️ Single-agent synthesis — [agent] review was
     unavailable. Coverage may be incomplete."

2. **Deduplicate findings**:
   - Merge overlapping findings — note both source IDs
   - Preserve the most specific `Alternative` and best `Evidence/Notes`
   - When the same pattern-violation appears across many locations,
     create one finding and document extent in `Evidence/Notes`
   - Agreement = higher confidence, not higher severity

3. **Calibrate severity**:
   - Re-evaluate based on evidence: impact on maintainability,
     extensibility, defect rate
   - Do not automatically escalate because both reviewers flagged the same issue

4. **Write synthesis** to `$AUDIT_DIR/synthesis.md`:

   ```markdown
   # Architecture Audit Synthesis — [REPORT_TS]

   ## Scope
   [Resolved scope path(s)]

   ## Summary
   - Total findings: N (Critical: X, High: X, Medium: X, Low: X)
   - Reviewers: Claude (A-prefix), Codex (C-prefix)

   ## Unified Findings

   | ID | Severity | Title | Location | Pattern/Principle | Why It Matters | Alternative | Migration Cost | Recommended Fix | Evidence/Notes | Sources |
   |----|----------|-------|----------|-------------------|----------------|-------------|----------------|-----------------|----------------|---------|

   ## Findings Present in Only One Review

   ## Rejected Devil's Advocate Challenges
   [Added after Phase 4]
   ```

---

## Phase 4: Devil's Advocate

**Goal**: Challenge the synthesis for false positives (including
intentional design choices), severity miscalibrations, missed findings,
and impractical alternatives.

```bash
codex exec "Read $AUDIT_DIR/synthesis.md. Your job is \
  to attack it, not improve it. Write your challenge to \
  $AUDIT_DIR/devils-advocate.md covering: \
  (1) False positives — 'violations' that are intentional design decisions \
  appropriate for this project's scale or constraints. \
  (2) Severity miscalibrations — findings rated too high or too low. \
  (3) Missing findings — structural issues both reviewers missed. \
  (4) Alternatives that are impractical or have misestimated migration cost. \
  Be specific. Every challenge must cite the finding ID. \
  Only write to $AUDIT_DIR/. Do not run shell commands beyond reading files."
```

Incorporate valid challenges: remove false positives, recalibrate severity,
add missed findings, document every rejected challenge in the synthesis.

---

## Phase 5: Report Output

### Sprint Mapping Rules

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

**Migration Cost nuance**: High findings with `Migration Cost=High`
are placed in P0, but the task description must include: "Requires team
alignment and design discussion before execution."

Each sprint task must include: finding ID, location, Pattern/Principle,
issue description, Alternative (target design), migration cost, remediation
step, verification.

Tasks must be scoped to specific, enumerable changes.

### Write the Sprint

Create `$AUDIT_DIR/REPORT.md`:

```markdown
# Architecture Audit — [scope] ([YYYY-MM-DD])

## Overview
[1-2 paragraphs. Remind the reader that LLM architectural review is
a hypothesis-generating starting point — findings require team
validation before execution.]

## Audit Summary
| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Total | N |

## Implementation Plan

### P0: Must Ship
**Task: [Finding ID] — [Title]**
- Location: `path/to/file:line`
- Pattern/Principle: [named principle or trade-off]
- Issue: [architectural issue description]
- Alternative: [target design]
- Migration Cost: [Low/Medium/High]
- Remediation: [specific implementation step]
- Verification: [how to confirm]

### P1: Ship If Capacity Allows
### Deferred

## Definition of Done
- [ ] All P0 tasks completed and verified
- [ ] P0 tasks with Migration Cost=High reviewed with team before implementation
- [ ] No new Critical/High findings introduced

## Architecture Considerations
- Findings are LLM hypotheses — validate each P0/P1 finding against team
  knowledge before executing
- P0 tasks with Migration Cost=High require team alignment before implementation

## Dependencies
- Audit intermediate files: `$AUDIT_DIR/{claude,codex,synthesis,devils-advocate}.md`
```

### Hand Off

   > ✅ Architecture audit complete.
   >
   > **Report:** <literal absolute path to $AUDIT_DIR/REPORT.md>
   >
   > **Next:** Run `/sprint-plan` against the report to create an actionable sprint:
   >
   > ```
   > /sprint-plan <literal absolute path>
   > ```
   >
   > **Important**: architecture findings are LLM hypotheses — validate each P0/P1 finding against team knowledge before executing tasks. Migration Cost=High items require team alignment before implementation.

Substitute the literal absolute path of `$AUDIT_DIR/REPORT.md`
(e.g. `/Users/corey/Reports/myorg/myrepo/audits/2026-04-22T10-30-00-architecture/REPORT.md`)
so the user can copy-paste the `/sprint-plan` command directly.

---

## Output Checklist

- [ ] `$AUDIT_DIR/claude.md` — finding schema with extension columns, ID prefix A
- [ ] `$AUDIT_DIR/codex.md` — finding schema with extension columns, ID prefix C
- [ ] Both non-empty (or single-agent warning in synthesis)
- [ ] `$AUDIT_DIR/synthesis.md` — canonical S-prefix IDs, all extension columns preserved
- [ ] `$AUDIT_DIR/devils-advocate.md` — Codex challenge complete
- [ ] Valid challenges incorporated; every rejection documented with reasoning
- [ ] `$AUDIT_DIR/REPORT.md` — P0/P1/Deferred tiering
- [ ] High + Migration Cost=High tasks include "requires team alignment" note
- [ ] No-findings case handled
- [ ] No raw user input text in any Codex exec prompt
