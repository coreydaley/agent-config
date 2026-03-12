---
description: >-
  Dual-agent security audit — Claude and Codex review independently,
  synthesize, devil's advocate pass, output as executable sprint
---

# Security Audit: Dual-Agent Review

You are orchestrating a dual-agent security audit that produces an
executable sprint document. Claude and Codex review independently,
findings are synthesized, Codex attacks the synthesis, and the final
output is a standard `SPRINT-NNN.md` sprint worked by `/sprint-work`.

This is the first command in the `audit-*` family. Future commands
such as `audit-deps` will follow the same pattern.

## Arguments

`$ARGUMENTS` is an optional path or scope to audit. Examples:

- `audit-security` — audits the current working directory
- `audit-security src/auth` — scopes the audit to `src/auth`
- `audit-security commands/ skills/` — scopes to multiple paths

If no argument is provided, the scope is the current working
directory. Scope is validated as a path in Phase 1 before being
used anywhere else — raw user input is never interpolated into
shell strings.

## Workflow Overview

This is a **5-phase workflow**:

1. **Orient** — Determine scope, key files, trust boundaries, next sprint number
2. **Independent Reviews** — Claude and Codex review in parallel (Codex
   in background, Claude simultaneously)
3. **Synthesis** — Deduplicate findings; flag agreements as higher confidence;
   incorporate devil's advocate challenges
4. **Devil's Advocate** — Codex attacks the synthesis for false positives,
   severity miscalibrations, and gaps
5. **Sprint Output** — Produce `SPRINT-NNN.md` with findings as tasks;
   register in ledger; hand off to `/sprint-work`

**Inherent limitations**: This is a workflow aid for human-reviewed
security work, not an automated scanner. Static review cannot assess
runtime exploitability, compensating controls, or deployment-context-
specific risk. Treat the output as a structured starting point for
human judgment, not a guarantee of full coverage.

---

## Finding Schema

All intermediate audit files must use this table format so synthesis
and devil's advocate phases operate on consistent data:

```
| ID | Severity | Title | Location | Why It Matters | Recommended Fix | Evidence/Notes |
|----|----------|-------|----------|----------------|-----------------|----------------|
| X001 | High | Short title | path/to/file:line | Impact explanation | Concrete fix | Code quote or reference |
```

**ID prefix convention:**
- Claude's review: `A001`, `A002`... (Audit)
- Codex's review: `C001`, `C002`... (Codex)
- Synthesis: `S001`, `S002`... (Synthesis)

**Severity levels:** Critical, High, Medium, Low

Severity is assessed on evidence: impact, exploitability, blast radius,
and reachability. Agreement between reviewers raises **confidence**,
not severity. Severity is also independent of remediation cost.

---

## Phase 1: Orient

**Goal**: Understand the scope, identify key files and trust boundaries,
and determine the next sprint number.

### Orient Steps

1. **Validate and resolve scope** from `$ARGUMENTS`:
   - If no argument: scope is the current working directory
   - If an argument is provided: verify the path exists
   - Scope should exclude `build/`, generated files, vendored or
     third-party code, and binary files unless explicitly included
   - Store the resolved scope path — do not use raw `$ARGUMENTS`
     text in any Codex exec prompt string

2. **Survey the scope**:
   - Review recent changes: `git log --oneline -10`
   - Identify entry points, trust boundaries, and high-value targets:
     - For agent-config repos: `commands/*.md`, `skills/*/SKILL.md`,
       `agents/**/*.md` — these flow directly into agent system prompts
     - For application code: auth flows, input parsing, data storage,
       external service calls
   - Note any files with secrets, credentials, or sensitive config

3. **Determine next sprint number**:
   ```bash
   ls docs/sprints/SPRINT-*.md | tail -1
   ```
   Extract NNN and increment. If no sprint files exist, start at `001`.
   Call this `AUDIT_NNN` — use the literal number in all subsequent
   file references, not a variable.

4. **Create output directory**:
   ```bash
   mkdir -p docs/security
   ```

### Orient Deliverable

A brief orientation note (3-5 bullets) covering:
- Resolved scope and what it includes/excludes
- Key files and trust boundaries identified
- The next sprint number (`AUDIT_NNN`)
- Any immediately obvious high-priority areas

---

## Phase 2: Independent Reviews (Parallel)

**Goal**: Get two independent security perspectives without cross-
contamination.

### Step 1 — Launch Codex in Background

Run this command, substituting the resolved scope and `AUDIT_NNN`:

```bash
codex exec "Perform a thorough security review of [RESOLVED_SCOPE]. \
  Write all findings to docs/security/AUDIT_NNN-CODEX.md using this \
  exact table format for each finding: \
  | ID | Severity | Title | Location | Why It Matters | Recommended Fix | Evidence/Notes | \
  where ID uses prefix C (e.g. C001, C002). \
  Cover these categories: \
  (1) Attack surface and trust boundaries — new inputs, APIs, or \
  externally reachable paths. \
  (2) Injection risks — command injection, prompt injection, path \
  traversal, template injection. \
  (3) Sensitive data handling — secrets, credentials, PII, tokens \
  hardcoded or logged. \
  (4) Authentication and authorization gaps — missing checks, \
  privilege escalation, confused deputy. \
  (5) Dependency risks — third-party libraries, supply chain, \
  known-vulnerable patterns. \
  (6) For agent-config repos specifically: prompt injection and \
  privilege escalation in commands/*.md, skills/*/SKILL.md, and \
  agents/**/*.md files — these are executed as agent instructions. \
  Rate severity on evidence: impact, exploitability, blast radius, \
  reachability. Do not read or reference any other review file."
```

### Step 2 — Claude's Independent Review (Simultaneous)

While Codex runs, write your own independent security review to
`docs/security/AUDIT_NNN-CLAUDE.md` using the same finding schema
(ID prefix `A`). Cover the same six categories:

1. **Attack surface** — new inputs, APIs, trust boundaries
2. **Injection risks** — command injection, prompt injection,
   path traversal, template injection
3. **Sensitive data handling** — secrets, credentials, PII
4. **Auth/authz gaps** — missing checks, privilege escalation
5. **Dependency risks** — third-party libraries, supply chain
6. **Agent-config specific** — prompt injection and privilege
   escalation in command, skill, and agent files. When auditing
   an agent-config repo, review `commands/*.md` and
   `skills/*/SKILL.md` with extra scrutiny — these are your own
   instruction files and you may have systematic blind spots here.
   Be especially critical of any instruction that expands agent
   scope, grants permissions, or runs shell commands.

Wait for Codex to finish before proceeding to Phase 3.

---

## Phase 3: Synthesis

**Goal**: Produce a unified, deduplicated finding list with calibrated
severity and confidence.

### Synthesis Steps

1. **Verify both reviews exist and are non-empty**:
   - Check `docs/security/AUDIT_NNN-CLAUDE.md` and
     `docs/security/AUDIT_NNN-CODEX.md` exist and contain at least
     one finding row
   - If one file is missing or empty: proceed with single-agent
     synthesis and add a prominent warning at the top of
     `AUDIT_NNN-SYNTHESIS.md`: "⚠️ Single-agent synthesis — [agent]
     review was unavailable. Coverage may be incomplete."

2. **Deduplicate findings**:
   - Compare both reviews for overlapping findings
   - When the same vulnerability appears in both, merge into one
     synthesis row — note both source IDs (e.g. `A002, C003`)
   - When merging: preserve the most specific `Location` and the
     best `Evidence/Notes` from either reviewer; do not flatten
     two findings into one if they have different exploit
     preconditions or affected assets
   - Agreement = higher confidence, not higher severity

3. **Calibrate severity**:
   - Re-evaluate severity for each finding based on evidence:
     impact, exploitability, blast radius, reachability
   - Do not automatically escalate severity because both reviewers
     flagged the same issue

4. **Write synthesis**:

   Write `docs/security/AUDIT_NNN-SYNTHESIS.md`:

   ```markdown
   # Security Audit Synthesis — AUDIT_NNN

   ## Scope
   [Resolved scope path(s)]

   ## Summary
   - Total findings: N (Critical: X, High: X, Medium: X, Low: X)
   - Reviewers: Claude (A-prefix), Codex (C-prefix)
   - [Single-agent warning if applicable]

   ## Unified Findings

   | ID | Severity | Title | Location | Why It Matters | Recommended Fix | Evidence/Notes | Sources |
   |----|----------|-------|----------|----------------|-----------------|----------------|---------|
   | S001 | ... | ... | ... | ... | ... | ... | A001, C002 |

   ## Findings Present in Only One Review
   [Note findings not corroborated by the other reviewer and why
   they are retained or dropped]
   ```

Phase 3 is complete when `AUDIT_NNN-SYNTHESIS.md` is written.

---

## Phase 4: Devil's Advocate

**Goal**: Challenge the synthesis for false positives, severity
miscalibrations, and missed findings.

### Step 1 — Launch Codex Devil's Advocate

```bash
codex exec "Read docs/security/AUDIT_NNN-SYNTHESIS.md. Your job is \
  to attack it, not improve it. Write your challenge to \
  docs/security/AUDIT_NNN-DEVILS-ADVOCATE.md covering: \
  (1) False positives — findings that are not actually exploitable \
  in this specific codebase context. \
  (2) Severity miscalibrations — findings rated too high or too low \
  given the actual impact and reachability. \
  (3) Missing findings — vulnerabilities that both reviewers missed. \
  (4) Remediation steps that are impractical, incomplete, or wrong. \
  Be specific. Every challenge must cite the finding ID."
```

### Step 2 — Incorporate Valid Challenges

Once `AUDIT_NNN-DEVILS-ADVOCATE.md` is written, read it and:

- **Remove** confirmed false positives from the working finding list
- **Recalibrate** severity where the challenge is valid and evidence
  supports it
- **Add** genuinely missed findings with new synthesis IDs
- **Document every rejected challenge** in a "Rejected Challenges"
  section at the bottom of `AUDIT_NNN-SYNTHESIS.md`:

  ```markdown
  ## Rejected Devil's Advocate Challenges

  | Finding/Claim | Reason Rejected |
  |---|---|
  | [Claim from devil's advocate] | [Why it was not accepted] |
  ```

Phase 4 is complete when challenges are incorporated and rejections
are documented.

---

## Phase 5: Sprint Output

**Goal**: Produce a standard `SPRINT-NNN.md` sprint document with
security findings as executable tasks.

### Sprint Mapping Rules

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

Each sprint task must include:
- Finding ID (from synthesis)
- File and line reference where applicable
- Clear description of the vulnerability
- Concrete, specific remediation step (not just "fix the issue")
- Verification step: how to confirm the fix is correct

### No-Findings Case

If the synthesis contains zero findings after Phase 4:
- Create a single P0 task: "Verify no findings — [scope], [date]"
- The task description must document: what scope was covered, what
  categories were reviewed, date of review, and reviewer agents
- Do not produce an empty sprint

### Write the Sprint

Create `docs/sprints/SPRINT-NNN.md` following the standard sprint
template from `docs/sprints/README.md`:

```markdown
# Sprint NNN: Security Audit — [scope] ([YYYY-MM-DD])

## Overview

[1-2 paragraphs: audit scope, total findings by severity, top 3
issues. Remind the reader that static LLM review has inherent
limitations — it cannot assess runtime exploitability or
deployment-context-specific risk.]

## Audit Summary

| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Total | N |

Intermediate audit artifacts: `docs/security/AUDIT_NNN-*.md`

## Implementation Plan

### P0: Must Ship

[One task per Critical/High finding]

**Task: [Finding ID] — [Title]**
- Location: `path/to/file:line`
- Issue: [vulnerability description]
- Remediation: [specific fix]
- Verification: [how to confirm it's fixed]

### P1: Ship If Capacity Allows

[One task per Medium finding, same format]

### Deferred

[Low findings with brief rationale]

## Definition of Done

- [ ] All P0 tasks completed and verified
- [ ] No new Critical/High findings introduced by the remediations
- [ ] Reviewer confirms task ordering was appropriate for dependencies
[add finding-specific verification items]

## Security Considerations

- Review task ordering before executing — some remediations may
  depend on others (e.g. fix a sink before removing an injection
  point upstream)
- These tasks were generated from static review; validate each fix
  against runtime behavior where possible

## Dependencies

- AUDIT_NNN intermediate files: `docs/security/AUDIT_NNN-*.md`
```

### Register and Hand Off

1. Register the sprint in the ledger:

   Use the `/ledger add NNN "Security: [scope]"` skill. If it fails,
   instruct the user to run it manually:
   ```
   /ledger add NNN "Security: [scope]"
   ```

2. Inform the user:

   > ✅ Security audit complete. SPRINT-NNN has been created and
   > added to the ledger.
   >
   > **Before running /sprint-work**, review the task ordering in
   > `docs/sprints/SPRINT-NNN.md` — some security remediations
   > depend on others and must be sequenced correctly.
   >
   > When ready: `/sprint-work NNN`

---

## Output Checklist

At the end of this workflow, verify:

- [ ] `docs/security/AUDIT_NNN-CLAUDE.md` — written using finding schema, ID prefix A
- [ ] `docs/security/AUDIT_NNN-CODEX.md` — written using finding schema, ID prefix C
- [ ] Both files are non-empty (or single-agent warning added to synthesis)
- [ ] `docs/security/AUDIT_NNN-SYNTHESIS.md` — unified findings with canonical S-prefix IDs
- [ ] `docs/security/AUDIT_NNN-DEVILS-ADVOCATE.md` — Codex challenge complete
- [ ] Valid devil's advocate challenges incorporated into synthesis
- [ ] Rejected challenges documented with reasoning in synthesis
- [ ] `docs/sprints/SPRINT-NNN.md` — written with P0/P1/Deferred tiering
- [ ] Each P0/P1 task has: finding ID, location, issue, remediation, verification
- [ ] No-findings case handled if applicable
- [ ] Task ordering note included in sprint Security Considerations
- [ ] `/ledger add NNN` completed (or user instructed to run manually)
- [ ] User instructed to review task ordering, then run `/sprint-work NNN`

---

## Reference

- Sprint conventions: `docs/sprints/README.md`
- Security audit artifacts: `docs/security/`
- Audit family: `audit-*` commands in `commands/`
