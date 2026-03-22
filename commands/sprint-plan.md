---
description: >-
  Multi-agent collaborative planning - draft, interview,
  compete with Codex, merge
---

# Sprint Plan: Collaborative Multi-Agent Planning

You are orchestrating a sophisticated planning workflow that
produces high-quality sprint documents through competitive
ideation and synthesis with Codex.

## Arguments

`$ARGUMENTS` may include an optional tool name followed by
the planning seed.

- Example: `linear improve sprint planning workflow`
- Example: `jira add deployment rollback guardrails`
- If the first argument is a recognized tool name, treat it
  as the sprint system to sync with after planning.
- Supported tool names are tools the agent can actually use
  in the current environment, such as `linear` or `jira`.
- If a tool name is provided but no matching tool or MCP
  integration is available, stop after explaining the gap
  and what integration is missing. Do not pretend the sync
  succeeded.
- If no tool name is provided, use the normal local sprint
  planning flow only.

## Seed Prompt

Use `$ARGUMENTS` as the seed prompt unless the first token
is a supported tool name. In that case, use the remainder
after the tool name as the seed prompt.

## Workflow Overview

This is a **9-phase workflow**:

1. **Orient** - Review project state, git history,
   in-progress sprints, and lessons from recent sprints;
   then present the phase selection menu with recommendations
   informed by what was found
2. **Intent** - Write concentrated intent document including
   alternative approaches considered
3. **Draft** - Create your draft plan with P0/P1 tiering,
   observability, and rollback sections
4. **Interview** - Clarify with the human planner (exit
   early via "Skip" if you have nothing to add)
5. **Compete** *(optional)* - Codex writes competing draft;
   then both critiques run in parallel (Codex critiques
   Claude's draft while Claude critiques Codex's draft)
6. **Merge** - Synthesize best ideas (or promote Claude's
   draft directly if Compete was skipped), apply simplest
   viable filter, and run sprint sizing gate
7. **Devil's Advocate** *(optional)* + **Security Review**
   *(optional)* + **Architecture Review** *(optional)* +
   **Test Strategy Review** *(optional)* - all four run in
   parallel; Codex handles Devil's Advocate and Test
   Strategy Review, Claude handles Security Review and
   Architecture Review; Definition of Ready pre-flight
   before approval
8. **Tool Sync** - If a supported tool name was provided,
   create or update the sprint in that external system,
   including stories and implementation tasks if needed

Use TaskCreate and TaskUpdate to track progress through each phase.

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

## Phase Selection

**Goal**: Present the phase menu with Orient-informed
recommendations so the user can confirm or adjust before
any planning work begins.

### Recommendation Heuristics

Use what you learned in Orient to pre-fill the optional
phase recommendations. Apply these signals:

| Signal from Orient | Suggested action |
|---|---|
| Novel architecture, new patterns, or significant refactor | Recommend Compete + Architecture Review |
| Touches auth, secrets, external APIs, or user data | Recommend Security Review |
| High correctness risk (parsers, migrations, spec compliance) | Recommend Test Strategy Review |
| Scope is vague, ambitious, or has prior history of underestimates | Recommend Devil's Advocate + Compete |
| Small, well-understood change in familiar territory | Suggest Lightweight |
| No Codex integration available or confirmed in this project | Omit all Codex phases with a note |

### Present the Menu

Show the phase menu with each optional phase pre-filled
as recommended (`[✓]`) or not recommended (`[ ]`), with
a one-line rationale for each:

```
  [✓] Phase 2   Intent                  (required)
  [✓] Phase 3   Draft                   (required)
  [✓] Phase 4   Interview               (required — exit early via "Skip")
  [?] Phase 5   Compete                 (optional) Codex draft + mutual critiques
  [✓] Phase 6   Merge / Promote         (required)
  [?] Phase 7a  Devil's Advocate        (optional) Codex — adversarial attack on the plan
  [?] Phase 7b  Security Review         (optional) Claude — security audit
  [?] Phase 7c  Architecture Review     (optional) Claude — conformance to project patterns
  [?] Phase 7d  Test Strategy Review    (optional) Codex — find gaps in DoD and test approach
```

Replace each `[?]` with `[✓]` (recommended) or `[ ]`
(not recommended) based on the heuristics above. Add a
brief rationale after each optional phase, for example:

```
  [✓] Phase 5   Compete          — novel architecture; second opinion valuable
  [ ] Phase 7a  Devil's Advocate — straightforward extension, low scope risk
  [✓] Phase 7b  Security Review  — plan touches auth flows and external API
  [✓] Phase 7c  Architecture Review — new abstraction layer introduced
  [ ] Phase 7d  Test Strategy Review — standard feature, existing test patterns apply
```

Then use AskUserQuestion with these options:

- **Accept recommendations** — proceed with the
  pre-filled selections above
- **Full workflow** — enable all optional phases
- **Lightweight** — skip all optional phases
- **Custom** — I'll choose each phase individually

If the user selects **Custom**, ask each of the following
in sequence (one at a time via AskUserQuestion):

1. **Compete** (Phase 5 — Codex draft + mutual critiques):
   run it, or skip? *(If skipped, Phase 6 becomes a direct
   promotion of Claude's draft rather than a merge.)*
2. **Devil's Advocate** (Phase 7a — Codex attacks the plan):
   run it, or skip?
3. **Security Review** (Phase 7b — Claude security audit):
   run it, or skip?
4. **Architecture Review** (Phase 7c — Claude conformance
   audit): run it, or skip?
5. **Test Strategy Review** (Phase 7d — Codex attacks the
   test strategy and DoD): run it, or skip?

Record the selections. Reference them at the start of each
optional phase and skip cleanly — no stub files, no partial
output — when a phase is disabled.

**Special case — Compete skipped**: If Phase 5 is disabled,
Phase 6 ("Merge") becomes "Promote": write
`docs/sprints/SPRINT-NNN.md` directly from the Claude draft,
apply the simplest viable filter, and run the sprint sizing
gate. Skip writing merge notes.

---

## Phase 2: Intent

**Goal**: Create a concentrated intent document that both
agents will use.

### Intent Steps

1. Determine the next sprint number using the ledger (already
   checked in Phase 1):

   ```bash
   python3 /Users/corey/.claude/skills/ledger/scripts/ledger.py list
   ```

   Find the highest sprint ID in the output and increment by 1
   to get NNN. If the ledger is empty, start at SPRINT-001.

   **Do not use `ls docs/sprints/SPRINT-*.md` to determine the
   number.** Filesystem files may be ahead of the ledger (e.g.
   an in-progress sprint's file already exists), which causes
   the number to be incremented past already-taken IDs. The
   ledger is the authoritative source for sprint numbering.

2. **Reserve the sprint number immediately** by registering it
   in the ledger before writing any files. This prevents
   concurrent planning sessions from claiming the same number:

   ```bash
   python3 /Users/corey/.claude/skills/ledger/scripts/ledger.py add NNN "Draft: [seed title]"
   ```

   If this fails because the sprint already exists (another
   planning session claimed it first), increment NNN and retry
   until you find an available number.

3. Create the drafts directory if needed:

   ```bash
   mkdir -p docs/sprints/drafts
   ```

4. Write the intent document to
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

5. Before moving to Phase 3, ensure the intent document's
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

## Phase 5: Compete (Codex) *(optional)*

> **Skip this phase** if Compete was disabled in Phase 0.
> Proceed directly to Phase 6 (Promote mode).

**Goal**: Get Codex's independent draft and symmetric
critiques of both drafts — run in two parallel steps.

### Step 1 — Codex Draft Only

Run this command (substitute the actual sprint number for
NNN):

```bash
codex exec "Please read docs/sprints/drafts/SPRINT-NNN-INTENT.md \
  - this is a concentrated intent for our next sprint. \
  Fully familiarize yourself with our sprint planning style \
  (see docs/sprints/README.md) and project structure \
  (see CLAUDE.md) and project goals. Then draft \
  docs/sprints/drafts/SPRINT-NNN-CODEX-DRAFT.md only. \
  Do not read or critique Claude's draft yet."
```

Wait for Codex to finish writing its draft before
proceeding.

### Step 2 — Parallel Critiques

Once `SPRINT-NNN-CODEX-DRAFT.md` exists, both critiques
can run at the same time:

**Launch Codex** (in background):

```bash
codex exec "Read docs/sprints/drafts/SPRINT-NNN-CLAUDE-DRAFT.md \
  and write a formal critique to \
  docs/sprints/drafts/SPRINT-NNN-CLAUDE-DRAFT-CODEX-CRITIQUE.md. \
  Cover: what Claude got right, what it missed, what you \
  would do differently, and any over-engineering or gaps."
```

**Simultaneously, write your own critique of Codex's
draft** to
`docs/sprints/drafts/SPRINT-NNN-CODEX-DRAFT-CLAUDE-CRITIQUE.md`.
Cover:

- What did Codex get right that your draft missed?
- What gaps, weaknesses, or over-engineering does Codex's
  draft have?
- Which of your own draft's choices would you defend
  against Codex's approach, and why?

Wait for Codex to finish its critique, then read:

- `docs/sprints/drafts/SPRINT-NNN-CLAUDE-DRAFT-CODEX-CRITIQUE.md`

This makes the critique symmetric: both drafts are attacked
before the merge begins.

---

## Phase 6: Merge / Promote

**Goal**: Synthesize the best ideas into a final sprint
document — or, if Compete was skipped, promote the Claude
draft directly.

> **Promote mode** (Compete skipped): Apply the simplest
> viable filter and sprint sizing gate to the Claude draft,
> then write it directly to `docs/sprints/SPRINT-NNN.md`.
> Skip merge notes. Continue to Phase 7.
>
> **Merge mode** (Compete ran): Follow the full merge
> process below.

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

## Phase 7: Reviews

**Goal**: Run any enabled review lenses in parallel against
the final sprint document before presenting it for approval.

Up to four independent reviews are available. All operate
on `docs/sprints/SPRINT-NNN.md` and can run simultaneously.

> If **all four** are disabled, skip this section and
> proceed directly to the Definition of Ready pre-flight.
>
> Group enabled reviews by agent and launch all Codex tasks
> together, then run all Claude tasks simultaneously:
>
> - **Codex tasks**: Devil's Advocate (7a), Test Strategy
>   Review (7d)
> - **Claude tasks**: Security Review (7b), Architecture
>   Review (7c)
>
> Run whichever subset was enabled; skip the rest with no
> stub files.

### Phase 7a: Devil's Advocate *(optional — Codex)*

> Skip if Devil's Advocate was disabled in Phase 0.

**Launch Codex** (in background):

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

### Phase 7b: Security Review *(optional — Claude)*

> Skip if Security Review was disabled in Phase 0.

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

### Phase 7c: Architecture Review *(optional — Claude)*

> Skip if Architecture Review was disabled in Phase 0.

Review `docs/sprints/SPRINT-NNN.md` for conformance to
existing project patterns and structural soundness. Write
your audit to
`docs/sprints/drafts/SPRINT-NNN-ARCHITECTURE-REVIEW.md`
covering:

1. **Pattern conformance** — does the plan's approach
   align with conventions in `CLAUDE.md` and patterns
   observed during Orient? Note any deviations.
2. **Coupling and cohesion** — does this plan introduce
   inappropriate coupling between modules or components?
3. **Schema and data model changes** — are migrations,
   backwards compatibility, or rollback implications
   addressed?
4. **New abstractions** — are any new patterns or
   abstractions proposed? Are they justified, or does an
   existing pattern suffice?
5. **Integration points** — are all touch points with
   existing systems correctly identified and handled?

Rate each finding: **Critical / High / Medium / Low**, and
suggest a concrete plan adjustment or DoD addition.

### Phase 7d: Test Strategy Review *(optional — Codex)*

> Skip if Test Strategy Review was disabled in Phase 0.

**Launch Codex** (in background):

```bash
codex exec "Read docs/sprints/SPRINT-NNN.md. Your job is \
  to attack the test strategy and Definition of Done. Act \
  as a senior engineer who must sign off on the testing \
  approach before implementation begins. Write \
  docs/sprints/drafts/SPRINT-NNN-TEST-STRATEGY-REVIEW.md. \
  Cover: (1) DoD gaps — which criteria are vague, \
  unverifiable, or could be gamed by a bad implementation? \
  (2) missing edge cases — what scenarios does the test \
  plan fail to cover? (3) test approach weaknesses — is \
  the testing strategy proportionate to the correctness \
  risk? (4) verification blindspots — what could go wrong \
  in production that the tests would not catch? Be \
  specific. Every concern should cite the relevant section \
  of the plan."
```

### Incorporate All Findings

Wait for all enabled Codex tasks to finish, then process
each enabled review:

**Devil's Advocate** — read
`docs/sprints/drafts/SPRINT-NNN-DEVILS-ADVOCATE.md`:

1. Evaluate each critique: valid? Patch it into the sprint
   document now.
2. If invalid, note why (brief inline comment or a
   "Critiques Addressed" section).

**Security Review** — for Critical or High findings: update
`docs/sprints/SPRINT-NNN.md` to add mitigations to the
relevant tasks or Definition of Done. For Medium/Low: use
judgment; add to the Security Considerations section if
relevant.

**Architecture Review** — for Critical or High findings:
update `docs/sprints/SPRINT-NNN.md` to adjust the
implementation plan or add DoD criteria. For Medium/Low:
add to the Architecture section or note as a known
trade-off.

**Test Strategy Review** — read
`docs/sprints/drafts/SPRINT-NNN-TEST-STRATEGY-REVIEW.md`:
for each valid gap, strengthen the corresponding DoD
criterion or add a missing test case to the plan.

Once all findings are incorporated, update the ledger using
the `/ledger sync` skill.

### Pre-Flight - Definition of Ready

Before presenting to the user, verify every item below. If
any fails, address it first.

- [ ] All **blocking open questions** are resolved — no
  unresolved items in the Open Questions section
- [ ] All **dependencies** are identified and either
  complete or explicitly tracked with a plan
- [ ] **Sprint sizing gate passed** in Phase 6 — plan is
  scoped for a single delivery
- [ ] **Critical/High findings** from any enabled Phase 7
  reviews are incorporated into tasks or Definition of Done
- [ ] **P0 tasks are clearly distinguished** from P1 and
  Deferred — nothing P1 or Deferred is blocking the sprint
- [ ] **Rollback plan** is documented for any changes to
  shared infrastructure or agent configs
- [ ] **Documentation tasks** are listed for anything that
  introduces new behavior or changes existing behavior

Once all items pass, show the user a combined summary of
all enabled review findings — what was incorporated and
what was rejected — then ask for approval of the final
document. After approval, direct the user to run
`/sprint-work` to execute the sprint.

---

## Phase 8: Tool Sync

**Goal**: If the command was invoked with a supported tool
name, create the sprint in that external planning system so
execution can later be driven from that tool.

### Tool Sync Steps

1. If no `TOOL_NAME` was provided in `$ARGUMENTS`, skip
   this phase.
2. Verify the agent has usable access to that tool in the
   current environment.
   - Prefer the corresponding MCP/tool integration if one
     exists
   - If access is missing, stop and tell the user exactly
     what is unavailable
3. Using the final approved sprint document
   `docs/sprints/SPRINT-NNN.md`, create the sprint in the
   external tool.
4. Translate the sprint plan into tool-native structure:
   - Create the sprint/cycle/iteration container if needed
   - Create stories/issues for the major P0 workstreams
   - Create subtasks/tasks for implementation and validation
     work when the tool supports them or when they are
     needed to preserve the sprint's Definition of Done
   - Carry over priority, ordering, and any dependencies
     that materially affect execution
5. Keep the external tool representation faithful to the
   sprint document.
   - Do not invent scope not present in the approved plan
   - Prefer P0 items first; P1/Deferred should be clearly
     labeled or omitted based on the tool's structure
6. At the end, report:
   - Which tool was used
   - What sprint/cycle was created or updated
   - Which stories/tasks were created
   - Any plan details that could not be represented exactly

### Tool Sync Output

If a tool name was provided and the sync succeeded, the
final response should include enough detail for `/sprint-work
TOOL_NAME` to locate and execute the same sprint from that
system.

---

## File Structure

After `/sprint-plan` completes, you'll have (files marked
`*` are only created when the corresponding optional phase
ran):

```text
docs/sprints/
├── drafts/
│   ├── SPRINT-NNN-INTENT.md
│   ├── SPRINT-NNN-CLAUDE-DRAFT.md
│   ├── SPRINT-NNN-CODEX-DRAFT.md            * (Compete)
│   ├── SPRINT-NNN-CLAUDE-DRAFT-CODEX-CRITIQUE.md  * (Compete)
│   ├── SPRINT-NNN-CODEX-DRAFT-CLAUDE-CRITIQUE.md  * (Compete)
│   ├── SPRINT-NNN-MERGE-NOTES.md            * (Compete)
│   ├── SPRINT-NNN-DEVILS-ADVOCATE.md        * (Devil's Advocate)
│   ├── SPRINT-NNN-SECURITY-REVIEW.md        * (Security Review)
│   ├── SPRINT-NNN-ARCHITECTURE-REVIEW.md    * (Architecture Review)
│   └── SPRINT-NNN-TEST-STRATEGY-REVIEW.md   * (Test Strategy Review)
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
  may exit early via "Skip")
- [ ] *(optional)* Codex draft received
  (`drafts/SPRINT-NNN-CODEX-DRAFT.md`)
- [ ] *(optional)* Codex critique received
  (`drafts/SPRINT-NNN-CLAUDE-DRAFT-CODEX-CRITIQUE.md`)
- [ ] *(optional)* Claude critique of Codex draft written
  (`drafts/SPRINT-NNN-CODEX-DRAFT-CLAUDE-CRITIQUE.md`)
- [ ] Simplest viable filter applied to merged/promoted plan
- [ ] Sprint sizing gate passed (plan is scoped for a
  single sprint)
- [ ] *(optional)* Merge notes written
  (`drafts/SPRINT-NNN-MERGE-NOTES.md`) — skipped in
  Promote mode
- [ ] Sprint document written (`SPRINT-NNN.md`)
- [ ] *(optional)* Devil's advocate critique received
  (`drafts/SPRINT-NNN-DEVILS-ADVOCATE.md`)
- [ ] *(optional)* Security review received
  (`drafts/SPRINT-NNN-SECURITY-REVIEW.md`)
- [ ] *(optional)* Architecture review received
  (`drafts/SPRINT-NNN-ARCHITECTURE-REVIEW.md`)
- [ ] *(optional)* Test strategy review received
  (`drafts/SPRINT-NNN-TEST-STRATEGY-REVIEW.md`)
- [ ] *(optional)* All enabled review findings incorporated
  or explicitly rejected in `SPRINT-NNN.md`
- [ ] Definition of Ready pre-flight passed (all 7 items
  checked)
- [ ] Ledger updated via the `/ledger sync` skill
- [ ] User approved the final document
- [ ] If a tool name was provided, sprint created or
  updated in that tool with stories/tasks as needed

---

## Reference

- Sprint conventions: `docs/sprints/README.md`
- Project overview: `CLAUDE.md`
- Recent sprints: `docs/sprints/SPRINT-*.md` (highest
  numbers)
