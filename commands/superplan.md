---
description: Multi-agent collaborative planning - draft, interview, compete with Codex, merge
---

# Mega Plan: Collaborative Multi-Agent Planning

You are orchestrating a sophisticated planning workflow that produces high-quality sprint documents through competitive ideation and synthesis with Codex.

## Seed Prompt

$ARGUMENTS

## Workflow Overview

This is a **6-phase workflow**:
1. **Orient** - Review project and recent sprints
2. **Intent** - Write concentrated intent document
3. **Draft** - Create your draft plan
4. **Interview** - Clarify with the human planner
5. **Compete** - Codex creates competing draft + critiques yours
6. **Merge** - Synthesize best ideas into final sprint document

Use TodoWrite to track progress through each phase.

---

## Phase 1: Orient

**Goal**: Understand current project state and recent direction.

### Steps:
1. Read `CLAUDE.md` for project conventions
2. Check sprint ledger status:
   ```bash
   python3 docs/sprints/ledger.py stats
   ```
3. Read the **3 highest-numbered sprint documents** to understand recent work:
   - Use `ls docs/sprints/SPRINT-*.md | tail -3` to find them
   - Read each one to understand recent trajectory
4. Identify relevant code areas for the seed prompt:
   - Search for related modules, types, or patterns
   - Note existing implementations that this plan might extend

### Deliverable:
Write a brief **Orientation Summary** (3-5 bullet points) covering:
- Current project state relevant to the seed
- Recent sprint themes/direction
- Key modules/files likely involved
- Constraints or patterns to respect

---

## Phase 2: Intent

**Goal**: Create a concentrated intent document that both agents will use.

### Steps:

1. Determine the next sprint number:
   ```bash
   ls docs/sprints/SPRINT-*.md | tail -1
   ```
   Extract NNN and increment.

2. Create the drafts directory if needed:
   ```bash
   mkdir -p docs/sprints/drafts
   ```

3. Write the intent document to `docs/sprints/drafts/SPRINT-NNN-INTENT.md`:

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

- Reference implementation: [if any, how will we verify conformance?]
- Spec/documentation: [what defines correct behavior?]
- Edge cases identified: [list known edge cases that must be handled]
- Testing approach: [unit tests, differential testing, conformance suite, etc.]

## Uncertainty Assessment

- Correctness uncertainty: [Low/Medium/High] - [why]
- Scope uncertainty: [Low/Medium/High] - [why]
- Architecture uncertainty: [Low/Medium/High] - [why]

## Open Questions

Questions that the drafts should attempt to answer.
```

---

## Phase 3: Draft (Claude)

**Goal**: Create your comprehensive draft plan.

### Write to: `docs/sprints/drafts/SPRINT-NNN-CLAUDE-DRAFT.md`

Follow the standard sprint template from `docs/sprints/README.md`:

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

### Phase 1: [Name] (~X%)

**Files:**
- `path/to/file.rs` - Description

**Tasks:**
- [ ] Task 1
- [ ] Task 2

### Phase 2: ...

## Files Summary

| File | Action | Purpose |
|------|--------|---------|
| `path/to/file` | Create/Modify | Description |

## Definition of Done

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Tests pass
- [ ] No compiler warnings

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| ... | ... | ... | ... |

## Security Considerations

- Item 1
- Item 2

## Dependencies

- Sprint NNN (if any)
- External requirements

## Open Questions

Uncertainties needing resolution.
```

---

## Phase 4: Interview

**Goal**: Refine understanding through human dialogue, with depth proportional to uncertainty.

### Step 1: Assess Uncertainty

Before asking questions, evaluate the uncertainty level of this sprint:

| Factor | Low Uncertainty | High Uncertainty |
|--------|-----------------|------------------|
| **Correctness** | Well-understood domain, simple logic | Reference impl, spec compliance, edge cases |
| **Scope** | Seed is specific and bounded | Seed is vague or ambitious |
| **Architecture** | Extends existing patterns | New patterns, integration points |
| **Verification** | Standard testing sufficient | Needs conformance/differential testing |

Assign an uncertainty level:
- **Low**: 1-2 questions (routine feature, clear requirements)
- **Medium**: 3-4 questions (some ambiguity, moderate complexity)
- **High**: 5-7 questions (reference implementations, specs, novel architecture)

### Step 2: Prioritize Questions by Impact

Order questions by their impact on sprint success. Always include an escape hatch.

**Question categories** (ask in this priority order):

1. **Verification Strategy** (HIGH impact when correctness matters)
   - "Your verification strategy is [X]. Given [domain complexity], is this sufficient?"
   - "The reference implementation handles [edge cases]. Should DoD require conformance tests for each?"
   - "How will we know the implementation matches the spec for [specific behavior]?"

2. **Scope Validation** (HIGH impact when seed is ambiguous)
   - "Does this scope match your intent, or should we expand/narrow?"
   - "I've included [X] but excluded [Y]. Is that right?"

3. **Priority/Trade-offs** (MEDIUM impact)
   - "Which aspects are most critical vs. nice-to-have?"
   - "If we hit constraints, what should we cut?"

4. **Technical Preferences** (MEDIUM impact)
   - "Any strong opinions on [specific technical choice]?"
   - "I'm planning to use [approach]. Any concerns?"

5. **Sequencing/Dependencies** (LOW impact unless external factors)
   - "Any external dependencies or ordering constraints?"

### Step 3: Conduct Adaptive Interview

Use AskUserQuestion iteratively. **Every question must include an option to end the interview.**

Structure each question round like this:

```
AskUserQuestion with options:
- [Substantive answer option 1]
- [Substantive answer option 2]
- "Skip - proceed to next phase" (ALWAYS include this)
```

**Interview flow:**

1. Ask the highest-impact question for this sprint's uncertainty profile
2. If user selects "Skip - proceed to next phase", immediately end interview and move to Phase 5
3. Otherwise, incorporate the answer and ask the next question
4. Repeat until questions exhausted or user skips

**Example for high-uncertainty sprint (reference implementation):**

Round 1 (Verification):
> "You mentioned using the Rust implementation for correctness. How should we verify conformance?"
> - Generate shared test vectors from Rust tests
> - Differential testing: run both implementations, compare outputs
> - Manual edge case enumeration from the spec
> - Skip - proceed to next phase

Round 2 (Verification follow-up, if not skipped):
> "For type resolution edge cases (forward references, qualified names, recursive types), should the DoD require explicit test coverage for each?"
> - Yes, enumerate and test each edge case explicitly
> - Cover the major ones, trust the differential testing for the rest
> - Skip - proceed to next phase

Round 3 (Scope):
> "I've scoped this to [X]. Does that match your intent?"
> - ...

### Step 4: Document Interview Results

Record:
- Uncertainty level assessed
- Questions asked and answers received
- Point at which user chose to proceed (if early exit)
- Refinements to incorporate in merge phase

---

## Phase 5: Compete (Codex)

**Goal**: Get Codex's independent draft and critique of your draft.

### Execute Codex:

Run this command (substitute the actual sprint number for NNN):

```bash
codex --model gpt-5.2 --full-auto exec "Please read docs/sprints/drafts/SPRINT-NNN-INTENT.md - this is a concentrated intent for our next sprint. Fully familiarize yourself with our sprint planning style (see docs/sprints/README.md) and project structure (see CLAUDE.md) and project goals. Then I want you to draft docs/sprints/drafts/SPRINT-NNN-CODEX-DRAFT.md. Only AFTER your draft is complete, I want you to read Claude's draft at docs/sprints/drafts/SPRINT-NNN-CLAUDE-DRAFT.md and write docs/sprints/drafts/SPRINT-NNN-CLAUDE-DRAFT-CODEX-CRITIQUE.md"
```

### Wait for Codex to complete.

Codex will produce:
- `docs/sprints/drafts/SPRINT-NNN-CODEX-DRAFT.md` - Its independent draft
- `docs/sprints/drafts/SPRINT-NNN-CLAUDE-DRAFT-CODEX-CRITIQUE.md` - Its critique of your draft

### Read the outputs:

Once Codex completes, read both files:
1. `docs/sprints/drafts/SPRINT-NNN-CODEX-DRAFT.md`
2. `docs/sprints/drafts/SPRINT-NNN-CLAUDE-DRAFT-CODEX-CRITIQUE.md`

---

## Phase 6: Merge

**Goal**: Synthesize the best ideas into a final sprint document.

### Merge process:

1. **Analyze Codex's critique** of your draft:
   - Which criticisms are valid?
   - What did you miss?
   - What should you defend?

2. **Compare the two drafts**:
   - Architecture approach differences
   - Phasing/ordering differences
   - Risk identification gaps
   - Definition of Done completeness

3. **Document the synthesis**:

   Write to `docs/sprints/drafts/SPRINT-NNN-MERGE-NOTES.md`:
   ```markdown
   # Sprint NNN Merge Notes

   ## Claude Draft Strengths
   - ...

   ## Codex Draft Strengths
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

4. **Write the final sprint document**:

   Create `docs/sprints/SPRINT-NNN.md` incorporating:
   - Best ideas from both drafts
   - Responses to valid critiques
   - Interview refinements

5. **Update the ledger**:
   ```bash
   python3 docs/sprints/ledger.py sync
   ```

6. **Show the user** the final document and ask for approval.

---

## File Structure

After megaplan completes, you'll have:

```
docs/sprints/
├── drafts/
│   ├── SPRINT-NNN-INTENT.md                    # Concentrated intent (Phase 2)
│   ├── SPRINT-NNN-CLAUDE-DRAFT.md              # Your draft (Phase 3)
│   ├── SPRINT-NNN-CODEX-DRAFT.md               # Codex draft (Phase 5)
│   ├── SPRINT-NNN-CLAUDE-DRAFT-CODEX-CRITIQUE.md  # Codex critique (Phase 5)
│   └── SPRINT-NNN-MERGE-NOTES.md               # Synthesis notes (Phase 6)
└── SPRINT-NNN.md                               # Final merged sprint
```

---

## Output Checklist

At the end of this workflow, you should have:
- [ ] Orientation summary complete
- [ ] Intent document written (`drafts/SPRINT-NNN-INTENT.md`)
- [ ] Claude draft written (`drafts/SPRINT-NNN-CLAUDE-DRAFT.md`)
- [ ] Interview conducted (adaptive to uncertainty, user may exit early)
- [ ] Codex executed and completed
- [ ] Codex draft received (`drafts/SPRINT-NNN-CODEX-DRAFT.md`)
- [ ] Codex critique received (`drafts/SPRINT-NNN-CLAUDE-DRAFT-CODEX-CRITIQUE.md`)
- [ ] Merge notes written (`drafts/SPRINT-NNN-MERGE-NOTES.md`)
- [ ] Final sprint document written (`SPRINT-NNN.md`)
- [ ] Ledger updated via `python3 docs/sprints/ledger.py sync`
- [ ] User approved the final document

---

## Reference

- Sprint conventions: `docs/sprints/README.md`
- Project overview: `CLAUDE.md`
- Recent sprints: `docs/sprints/SPRINT-*.md` (highest numbers)
