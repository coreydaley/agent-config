---
description: >-
  Multi-agent collaborative planning - draft, interview,
  compete with Codex, merge
---

# Superplan: Collaborative Multi-Agent Planning

You are orchestrating a sophisticated planning workflow that
produces high-quality sprint documents through competitive
ideation and synthesis with Codex.

## Seed Prompt

$ARGUMENTS

## Workflow Overview

This is an **8-phase workflow**:

1. **Orient** - Review project state, git history,
   in-progress sprints, and lessons from recent sprints
2. **Intent** - Write concentrated intent document including
   alternative approaches considered
3. **Draft** - Create your draft plan with P0/P1 tiering,
   observability, and rollback sections
4. **Interview** - Clarify with the human planner
5. **Compete** - Codex creates competing draft + critiques
   yours; Claude formally critiques Codex's draft
6. **Merge** - Synthesize best ideas, apply simplest viable
   filter, and run sprint sizing gate
7. **Devil's Advocate** - Codex tears apart the merged plan
   as a skeptical critic
8. **Security Review** - Claude audits the final plan for
   security risks; Definition of Ready pre-flight before
   approval

Use TodoWrite to track progress through each phase.

---

## Phase 1: Orient

**Goal**: Understand current project state and recent
direction.

### Orient Steps

1. Read `CLAUDE.md` for project conventions
2. Check sprint ledger status using the `/ledger stats`
   skill.
   - Note any **in-progress** sprints and their relationship
     to the seed prompt — a sprint already in flight is
     critical context
3. Review recent git activity to see what was actually
   shipped vs. what was planned:

   ```bash
   git log --oneline -20
   ```

4. Read the **3 highest-numbered sprint documents** to
   understand recent work:
   - Use `ls docs/sprints/SPRINT-*.md | tail -3` to find
     them
   - Focus especially on what was **deferred,
     underestimated, or left incomplete** — not just what
     was planned
5. Identify relevant code areas for the seed prompt:
   - Search for related modules, types, or patterns
   - Note existing implementations that this plan might
     extend

### Orient Deliverable

Write a brief **Orientation Summary** (3-5 bullet points)
covering:

- Current project state relevant to the seed
- Recent sprint themes/direction, including any recurring
  underestimates or deferred items
- Any in-progress sprints and how they interact with the
  seed
- Key modules/files likely involved
- Constraints or patterns to respect

---

## Phase 2: Intent

**Goal**: Create a concentrated intent document that both
agents will use.

### Intent Steps

1. Determine the next sprint number:

   ```bash
   ls docs/sprints/SPRINT-*.md | tail -1
   ```

   Extract NNN and increment. If no sprint files exist yet,
   start at SPRINT-001.

2. Create the drafts directory if needed:

   ```bash
   mkdir -p docs/sprints/drafts
   ```

3. Write the intent document to
   `docs/sprints/drafts/SPRINT-NNN-INTENT.md`:

```markdown
# Sprint NNN Intent: [Title]

## Seed

[The original $ARGUMENTS prompt]

## Context

[Your orientation summary from Phase 1]

## Recent Sprint Context

[Brief summaries of the 3 recent sprints you reviewed]

## Relevant Codebase Areas

[Key modules, files, patterns identified during orientation]

## Constraints

- Must follow project conventions in CLAUDE.md
- Must integrate with existing architecture
- [Any other constraints identified]

## Success Criteria

What would make this sprint successful?

## Verification Strategy

How will we know the implementation is correct?

- Reference implementation: [if any, how will we verify
  conformance?]
- Spec/documentation: [what defines correct behavior?]
- Edge cases identified: [list known edge cases that must
  be handled]
- Testing approach: [unit tests, differential testing,
  conformance suite, etc.]

## Uncertainty Assessment

- Correctness uncertainty: [Low/Medium/High] - [why]
- Scope uncertainty: [Low/Medium/High] - [why]
- Architecture uncertainty: [Low/Medium/High] - [why]

## Approaches Considered

Enumerate 2-3 distinct implementation approaches before
committing to a direction:

| Approach | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| [Approach A] | ... | ... | **Selected** — [reason] |
| [Approach B] | ... | ... | Rejected — [reason] |
| [Approach C] | ... | ... | Rejected — [reason] |

## Open Questions

Questions that the drafts should attempt to answer.
```

1. Before moving to Phase 3, ensure the intent document's
   **Approaches Considered** table is complete. The selected
   approach should be clear; rejected approaches should have
   explicit reasons. Both agents will see this document —
   the approaches table prevents Codex from rediscovering an
   approach you already evaluated and discarded.

---

## Phase 3: Draft (Claude)

**Goal**: Create your comprehensive draft plan.

Before writing, apply the **simplest viable filter**: for
every proposed task or feature, ask "is this strictly
necessary for the sprint's stated goal, or can it be
deferred?" Move anything non-essential to a Deferred
section. A plan that ships is better than a plan that's
complete.

### Write to `docs/sprints/drafts/SPRINT-NNN-CLAUDE-DRAFT.md`

```markdown
# Sprint NNN: [Title]

## Overview

2-3 paragraphs on the "why" and high-level approach.

## Use Cases

1. **Use case name**: Description
2. ...

## Architecture

Diagrams (ASCII art), component descriptions, data flow.

## Implementation Plan

### P0: Must Ship

**Files:**
- `path/to/file.ext` - Description

**Tasks:**
- [ ] Task 1
- [ ] Task 2

### P1: Ship If Capacity Allows

**Tasks:**
- [ ] Task 1

### Deferred

- Item 1 — [reason for deferral]

## Files Summary

| File | Action | Purpose |
|------|--------|---------|
| `path/to/file` | Create/Modify | Description |

## Definition of Done

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Tests pass

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| ... | ... | ... | ... |

## Security Considerations

- Item 1
- Item 2

## Observability & Rollback

- How will we verify the implementation is working
  correctly post-ship?
- What logs, metrics, or output changes prove correctness?
- Rollback plan if something breaks: [describe revert
  steps or fallback]

## Documentation

- [ ] Doc update 1
- [ ] Doc update 2

## Dependencies

- Sprint NNN (if any)
- External requirements

## Open Questions

Uncertainties needing resolution.
```

---

## Phase 4: Interview

**Goal**: Refine understanding through human dialogue, with
depth proportional to uncertainty.

### Step 1 - Assess Uncertainty

Before asking questions, evaluate the uncertainty level of
this sprint:

| Factor | Low Uncertainty | High Uncertainty |
| --- | --- | --- |
| **Correctness** | Well-understood domain | Reference impl, spec compliance |
| **Scope** | Seed is specific and bounded | Seed is vague or ambitious |
| **Architecture** | Extends existing patterns | New patterns, integration points |
| **Verification** | Standard testing sufficient | Conformance/differential testing |

Assign an uncertainty level:

- **Low**: 1-2 questions (routine feature, clear
  requirements)
- **Medium**: 3-4 questions (some ambiguity, moderate
  complexity)
- **High**: 5-7 questions (reference implementations,
  specs, novel architecture)

### Step 2 - Prioritize Questions by Impact

Order questions by their impact on sprint success. Always
include an escape hatch.

**Question categories** (ask in this priority order):

1. **Verification Strategy** (HIGH impact when correctness
   matters)
   - "Your verification strategy is [X]. Given [domain
     complexity], is this sufficient?"
   - "The reference implementation handles [edge cases].
     Should DoD require conformance tests for each?"
   - "How will we know the implementation matches the spec
     for [specific behavior]?"

2. **Scope Validation** (HIGH impact when seed is ambiguous)
   - "Does this scope match your intent, or should we
     expand/narrow?"
   - "I've included [X] but excluded [Y]. Is that right?"

3. **Priority/Trade-offs** (MEDIUM impact)
   - "Which aspects are most critical vs. nice-to-have?"
   - "If we hit constraints, what should we cut?"

4. **Technical Preferences** (MEDIUM impact)
   - "Any strong opinions on [specific technical choice]?"
   - "I'm planning to use [approach]. Any concerns?"

5. **Sequencing/Dependencies** (LOW impact unless external
   factors)
   - "Any external dependencies or ordering constraints?"

### Step 3 - Conduct Adaptive Interview

Use AskUserQuestion iteratively. **Every question must
include an option to end the interview.**

Structure each question round like this:

```text
AskUserQuestion with options:
- [Substantive answer option 1]
- [Substantive answer option 2]
- "Skip - proceed to next phase" (ALWAYS include this)
```

**Interview flow:**

1. Ask the highest-impact question for this sprint's
   uncertainty profile
2. If user selects "Skip - proceed to next phase",
   immediately end interview and move to Phase 5
3. Otherwise, incorporate the answer and ask the next
   question
4. Repeat until questions exhausted or user skips

After the interview, note any refinements to carry into the
merge phase.

---

## Phase 5: Compete (Codex)

**Goal**: Get Codex's independent draft and critique of your
draft.

### Launch Codex for Competition

Run this command (substitute the actual sprint number for
NNN):

```bash
codex exec "Please read docs/sprints/drafts/SPRINT-NNN-INTENT.md \
  - this is a concentrated intent for our next sprint. \
  Fully familiarize yourself with our sprint planning style \
  (see docs/sprints/README.md) and project structure \
  (see CLAUDE.md) and project goals. Then I want you to \
  draft docs/sprints/drafts/SPRINT-NNN-CODEX-DRAFT.md. \
  Only AFTER your draft is complete, I want you to read \
  Claude's draft at \
  docs/sprints/drafts/SPRINT-NNN-CLAUDE-DRAFT.md and write \
  docs/sprints/drafts/SPRINT-NNN-CLAUDE-DRAFT-CODEX-CRITIQUE.md"
```

Once Codex completes, read both output files:

- `docs/sprints/drafts/SPRINT-NNN-CODEX-DRAFT.md`
- `docs/sprints/drafts/SPRINT-NNN-CLAUDE-DRAFT-CODEX-CRITIQUE.md`

Then write your own formal critique of Codex's draft to
`docs/sprints/drafts/SPRINT-NNN-CODEX-DRAFT-CLAUDE-CRITIQUE.md`.
Cover:

- What did Codex get right that your draft missed?
- What gaps, weaknesses, or over-engineering does Codex's
  draft have?
- Which of your own draft's choices would you defend
  against Codex's approach, and why?

This makes the critique symmetric: both drafts are attacked
before the merge begins.

---

## Phase 6: Merge

**Goal**: Synthesize the best ideas into a final sprint
document.

### Merge Process

1. **Analyze both critiques**:
   - From Codex's critique of your draft: which criticisms
     are valid? What did you miss? What should you defend?
   - From your critique of Codex's draft: what weaknesses
     did you identify? Which of your own choices does that
     reinforce?

2. **Compare the two drafts**:
   - Architecture approach differences
   - Phasing/ordering differences
   - Risk identification gaps
   - Definition of Done completeness

3. **Document the synthesis**:

   Write to
   `docs/sprints/drafts/SPRINT-NNN-MERGE-NOTES.md`:

   ```markdown
   # Sprint NNN Merge Notes

   ## Claude Draft Strengths
   - ...

   ## Claude Draft Weaknesses (from Codex critique)
   - ...

   ## Codex Draft Strengths
   - ...

   ## Codex Draft Weaknesses (from Claude critique)
   - ...

   ## Valid Critiques Accepted
   - ...

   ## Critiques Rejected (with reasoning)
   - ...

   ## Interview Refinements Applied
   - ...

   ## Final Decisions
   - ...
   ```

4. **Apply the simplest viable filter**: Before writing the
   final document, review every proposed task across both
   drafts. Ask: "Is this strictly necessary for the
   sprint's stated goal, or can it be deferred?" Move
   non-essential items to the Deferred section. Prefer the
   implementation that ships over the implementation that's
   comprehensive.

5. **Sprint sizing gate**: Assess whether the merged plan
   is appropriately scoped for a single sprint:
   - Does the plan have more than one natural delivery
     milestone?
   - Would a reasonable team realistically complete all P0
     tasks in one sprint?
   - If the plan is oversized, propose splitting it now
     (before hardening phases), confirm with the user, and
     adjust scope before proceeding to Phase 7.

6. **Write the initial sprint document**:

   Create `docs/sprints/SPRINT-NNN.md` incorporating:
   - Best ideas from both drafts
   - Responses to valid critiques
   - Interview refinements
   - P0/P1/Deferred tiering
   - Observability & Rollback and Documentation sections

---

## Phase 7: Devil's Advocate

**Goal**: Have Codex act as a skeptical critic of the final
merged plan, stress-testing assumptions and surfacing weak
spots before execution begins.

### Launch Codex for Devil's Advocate

Run this command (substitute the actual sprint number for
NNN):

```bash
codex exec "Read docs/sprints/SPRINT-NNN.md. This is a \
  finalized sprint plan. Your job is NOT to improve it — \
  your job is to attack it. Act as a senior skeptic who \
  must approve this plan before a single line of code is \
  written. Write \
  docs/sprints/drafts/SPRINT-NNN-DEVILS-ADVOCATE.md with \
  your critique. Cover: (1) flawed assumptions — what is \
  this plan taking for granted that could be wrong? \
  (2) scope risks — what could balloon, be underestimated, \
  or have hidden dependencies? (3) design weaknesses — \
  what architectural choices might we regret? (4) gaps in \
  the Definition of Done — what's missing that could let \
  a bad implementation 'pass'? (5) what's the most likely \
  way this sprint fails? Be specific and harsh. Every \
  concern should cite the relevant section of the plan."
```

Once Codex completes, read
`docs/sprints/drafts/SPRINT-NNN-DEVILS-ADVOCATE.md` and
respond:

1. Read
   `docs/sprints/drafts/SPRINT-NNN-DEVILS-ADVOCATE.md`
2. Evaluate each critique: is it valid? If so, patch it in
   the sprint document now.
3. If a critique is invalid, note why in the document
   (brief inline comment or a "Critiques Addressed"
   section).
4. Update `docs/sprints/SPRINT-NNN.md` with any revisions.

Show the user a brief summary (in your own words) of the
devil's advocate findings and what you addressed vs.
rejected, then ask for their input before proceeding to
Phase 8.

---

## Phase 8: Security Review

**Goal**: You (Claude) perform a thorough security audit of
the final plan before it goes to the user for approval.

### Security Review Steps

Review `docs/sprints/SPRINT-NNN.md` with a security-focused
lens. Write your audit to
`docs/sprints/drafts/SPRINT-NNN-SECURITY-REVIEW.md`
covering:

1. **Attack surface** — what new inputs, APIs, or trust
   boundaries does this plan introduce?
2. **Data handling** — any risks around sensitive data,
   secrets, or PII?
3. **Injection and parsing risks** — new parsers, template
   engines, query builders, or eval-adjacent code?
4. **Authentication/authorization** — does this plan touch
   auth flows or permission checks? Any gaps?
5. **Dependency risks** — new libraries or external
   services, and their known risk profile
6. **Threat model** — given the project context in
   `CLAUDE.md`, what's a realistic adversarial scenario
   for this sprint's changes?

Rate each finding: **Critical / High / Medium / Low**, and
suggest a concrete mitigation or DoD addition.

### Incorporate Findings and Finalize

1. For Critical or High findings: update
   `docs/sprints/SPRINT-NNN.md` to add mitigations to the
   relevant tasks or Definition of Done.
2. For Medium/Low findings: use your judgment; add to the
   Security Considerations section if relevant.
3. Update the ledger using the `/ledger sync` skill.

### Pre-Flight - Definition of Ready

Before presenting to the user, verify every item below. If
any fails, address it first.

- [ ] All **blocking open questions** are resolved — no
  unresolved items in the Open Questions section
- [ ] All **dependencies** are identified and either
  complete or explicitly tracked with a plan
- [ ] **Sprint sizing gate passed** in Phase 6 — plan is
  scoped for a single delivery
- [ ] **Critical/High security findings** from Phase 8 are
  incorporated into tasks or Definition of Done
- [ ] **P0 tasks are clearly distinguished** from P1 and
  Deferred — nothing P1 or Deferred is blocking the sprint
- [ ] **Rollback plan** is documented for any changes to
  shared infrastructure or agent configs
- [ ] **Documentation tasks** are listed for anything that
  introduces new behavior or changes existing behavior

Once all items pass, show the user a summary of security
findings and what was incorporated, then ask for approval
of the final document.

---

## File Structure

After superplan completes, you'll have:

```text
docs/sprints/
├── drafts/
│   ├── SPRINT-NNN-INTENT.md
│   ├── SPRINT-NNN-CLAUDE-DRAFT.md
│   ├── SPRINT-NNN-CODEX-DRAFT.md
│   ├── SPRINT-NNN-CLAUDE-DRAFT-CODEX-CRITIQUE.md
│   ├── SPRINT-NNN-CODEX-DRAFT-CLAUDE-CRITIQUE.md
│   ├── SPRINT-NNN-MERGE-NOTES.md
│   ├── SPRINT-NNN-DEVILS-ADVOCATE.md
│   └── SPRINT-NNN-SECURITY-REVIEW.md
└── SPRINT-NNN.md
```

---

## Output Checklist

At the end of this workflow, you should have:

- [ ] Orientation summary complete (includes in-progress
  sprints + git log review)
- [ ] Intent document written
  (`drafts/SPRINT-NNN-INTENT.md`) with Approaches
  Considered table
- [ ] Alternative approaches enumerated; one selected with
  rejections documented
- [ ] Claude draft written
  (`drafts/SPRINT-NNN-CLAUDE-DRAFT.md`) with P0/P1/Deferred
  tiering, Observability & Rollback, and Documentation
  sections
- [ ] Interview conducted (adaptive to uncertainty, user
  may exit early)
- [ ] Codex draft received
  (`drafts/SPRINT-NNN-CODEX-DRAFT.md`)
- [ ] Codex critique received
  (`drafts/SPRINT-NNN-CLAUDE-DRAFT-CODEX-CRITIQUE.md`)
- [ ] Claude critique of Codex draft written
  (`drafts/SPRINT-NNN-CODEX-DRAFT-CLAUDE-CRITIQUE.md`)
- [ ] Simplest viable filter applied to merged plan
- [ ] Sprint sizing gate passed (plan is scoped for a
  single sprint)
- [ ] Merge notes written
  (`drafts/SPRINT-NNN-MERGE-NOTES.md`)
- [ ] Initial merged sprint document written
  (`SPRINT-NNN.md`)
- [ ] Devil's advocate critique received
  (`drafts/SPRINT-NNN-DEVILS-ADVOCATE.md`)
- [ ] Valid critiques incorporated into `SPRINT-NNN.md`
- [ ] Security review received
  (`drafts/SPRINT-NNN-SECURITY-REVIEW.md`)
- [ ] Critical/High security findings incorporated into
  `SPRINT-NNN.md`
- [ ] Definition of Ready pre-flight passed (all 7 items
  checked)
- [ ] Ledger updated via the `/ledger sync` skill
- [ ] User approved the final document

---

## Reference

- Sprint conventions: `docs/sprints/README.md`
- Project overview: `CLAUDE.md`
- Recent sprints: `docs/sprints/SPRINT-*.md` (highest
  numbers)
