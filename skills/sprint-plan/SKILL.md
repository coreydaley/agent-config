---
name: sprint-plan
description: >-
  Multi-agent collaborative planning with strict orchestrator/worker
  separation — drafts, critiques, and reviews are delegated to fresh
  workers at per-phase model tiers so no context judges its own output
argument-hint: "[flags] <seed prompt>"
disable-model-invocation: true
---

# Sprint Plan: Collaborative Multi-Agent Planning

You are orchestrating a sprint-planning workflow built on **strict
separation of duties**. The orchestrator handles analysis, synthesis,
and human dialogue, but never drafts, critiques, or reviews.
Generative and adversarial work is delegated to fresh workers —
either same-family subagents or opposite-family agents invoked via
`exec` — so no single context writes a plan and then judges its
own output. Each delegated phase runs at a model tier chosen by
the orchestrator based on perceived scope, and the user can
override every tier before work begins.

## Roles

- **Orchestrator** — the agent running this command (you). Runs at
  whatever model the user invoked the command with; its tier is
  not configurable. Handles: Orient, Phase Selection, Intent,
  Interview, Merge/Promote, Incorporate Findings, DoR Pre-Flight,
  Approval, Register.
- **Orch-side worker** — a fresh same-family subagent. Handles
  orch-side drafts, critiques, and any review whose expert side
  matches yours.
  - If you are Claude: spawn via the `Agent` tool with
    `subagent_type=general-purpose` and `model=<tier>`.
  - If you are Codex: invoke via `codex exec -m <tier> "<prompt>"`.
- **Opposite-side worker** — an agent from the other model family.
  Handles opposite-side drafts, critiques, and any review whose
  expert side is the opposite of yours.
  - If you are Claude: invoke via `codex exec -m <tier> "<prompt>"`.
  - If you are Codex: invoke via
    `claude -p --model <tier> "<prompt>"`.

**Identity substitution**: throughout this doc, `ORCH_NAME` means
your own side's literal name (`claude` or `codex`) and `OPPO_NAME`
means the other side's. Substitute these when you construct
delegation prompts and file paths. Artifacts keep literal agent
names in their filenames so they stay self-documenting when read
later.

## Model Tiers

Two tiers only — no Haiku-equivalent is ever used. Tiers govern
**delegated workers only**; the orchestrator's own model is fixed
by how the user invoked the command.

| Tier | Claude-side | Codex-side    |
|------|-------------|---------------|
| High | `opus`      | `gpt-5.4`     |
| Mid  | `sonnet`    | `gpt-5.4-mini`|

### Per-Phase Tier Defaults

| Phase | Default tier | Rationale |
|---|---|---|
| 5a Orch-side draft             | High | Shapes the rest of the workflow |
| 5b Opposite-side draft         | High | Competing draft must be substantive to earn the merge cost |
| 6a Opposite critiques orch     | Mid  | Critique of an existing document |
| 6b Orch critiques opposite     | Mid  | Critique of an existing document |
| 8a Devil's Advocate            | High | Blunt adversary is worthless — must be sharp |
| 8b Security Review             | High | Blunt adversary is worthless — must be sharp |
| 8c Architecture Review         | Mid  | Bump to High if novel architecture or new abstractions |
| 8d Test Strategy Review        | Mid  | Bump to High if correctness risk is high (parsers, migrations, spec work) |
| 8e Observability Review        | Mid  | Bump to High if distributed, long-running, or SLO-bearing |
| 8f Performance & Scale Review  | Mid  | Bump to High if hot path, load-bearing infra, or throughput SLOs |
| 8g Breaking Change Review      | Mid  | Bump to High if touches public APIs, schemas, config, or CLI |

### Tier-Adjustment Heuristics

Use Orient + seed signals to override defaults when recommending
tiers in Phase 2:

| Signal | Adjustment |
|---|---|
| Novel architecture, new patterns, spec/parser/migration work | Bump 8c and 8d to High |
| Auth, secrets, external APIs, user data | Confirm 8b High; nothing lower than Mid elsewhere |
| Any High uncertainty anywhere in intent | All delegated phases ≥ Mid; drafts High |
| Vague/ambitious scope, history of underestimates | All drafts + critiques High |
| Distributed system, long-running processes, prod telemetry | Bump 8e to High |
| Touches hot paths, benchmarks, resource limits, autoscaling | Bump 8f to High |
| Modifies public APIs, protocol buffers, schemas, config format, CLI | Bump 8g to High |
| Small, well-understood change in familiar territory | Drop 5a/5b/6a/6b to Mid |

## Arguments

`$ARGUMENTS` may begin with flags, followed by the seed prompt for
the sprint. See the **Flags** section below for available options.

- Example: `improve sprint planning workflow`
- Example: `--auto add deployment rollback guardrails`
- Example: `--full --tier=high migrate session store`
- Example: `--dry add deployment rollback guardrails`
- Example: `--help`

## Flags

All flags are optional. Without any, the command runs the full
interactive flow: Orient → Phase 2 menu → confirm → execute.

### Tier

| Flag | Behavior |
|---|---|
| `--tier=high` | All delegated phases run at High tier |
| `--tier=mid`  | All delegated phases run at Mid tier |

No per-phase tier flags. For finer control, omit `--tier` and
adjust in the Phase 2 menu.

### Workflow shortcuts

Mutually exclusive. Each skips the Phase 2 menu entirely.

| Flag     | Behavior |
|----------|---|
| `--base` | Only required phases run (5a Draft, 7 Promote, 9 Finalize). All optional phases skipped. |
| `--full` | All optional phases enabled at their Orient-recommended tiers. |
| `--auto` | Accept Orient's phase-by-phase recommendations as-is (some optional phases enabled, some not, based on heuristics). |

### Dry-run preview

| Flag | Behavior |
|---|---|
| `--dry` | Run Phase 1 (Orient), compute Phase 2 selections, compose Phase 3 (Intent) in memory, display the preview, then exit. **No files are written.** No drafts, critiques, or reviews run. |

`--dry` combines freely with every other flag — it only changes
execution mode from "run" to "preview":

| Combination | Preview shows |
|---|---|
| `--dry` alone | Orient + recommended phases at recommended tiers + intent |
| `--dry --tier=high` | Same, but all tiers forced High |
| `--dry --auto` | Same as `--dry` alone (both accept Orient) |
| `--dry --full` | All optional phases enabled at recommended tiers |
| `--dry --base` | Minimum workflow preview (required phases only) |
| `--dry --full --tier=high` | Everything on, all at High |

The preview output has four parts, assembled inline at the end of
Phase 3:

1. **Orientation Summary** — Phase 1's bullets
2. **Phase Selection table** — enabled/disabled + tier per phase
3. **Intent Document** — composed in memory and shown inline
4. **Scope summary** — one line: "Would spawn N delegated workers
   across M phases; tier mix X High / Y Mid; expert routing
   A claude-side, B codex-side"

Close with: *"Dry run complete. Re-run without `--dry` to execute."*

### Help

| Flag | Behavior |
|---|---|
| `--help` | Display usage summary and exit. Overrides every other flag — nothing else runs, no phase is entered. |

When `--help` is passed (alone or combined with any other flag),
emit the text below verbatim and exit. Do not enter Phase 1, do
not ask for input, do not write any files.

```
/sprint-plan — multi-agent collaborative sprint planning

Usage:
  /sprint-plan [flags] <seed prompt>

Without flags, runs the full interactive workflow: Orient, Phase
Selection menu, Intent, Interview, delegated drafts/critiques/
reviews, synthesis, approval, register in ledger.

Flags:
  --tier=high    Force all delegated phases to High tier
                 (opus / gpt-5.4)
  --tier=mid     Force all delegated phases to Mid tier
                 (sonnet / gpt-5.4-mini)

  --base         Required phases only (5a, 7, 9). Skips menu.
  --full         All optional phases enabled at recommended tiers.
                 Skips menu.
  --auto         Accept Orient's recommendations as-is. Skips menu.
                 (--base / --full / --auto are mutually exclusive)

  --dry          Preview only. No files written. Exits after
                 composing intent. Combines freely with --tier
                 and any workflow shortcut.

  --help         Show this help and exit.

Examples:
  /sprint-plan add rollback guardrails
  /sprint-plan --auto add rollback guardrails
  /sprint-plan --full --tier=high critical auth rewrite
  /sprint-plan --base fix typo in CLAUDE.md
  /sprint-plan --dry add rollback guardrails

Full documentation: ~/.claude/skills/sprint-plan/SKILL.md
```

### Precedence and combinations

- `--help` trumps everything else. If `--help` appears anywhere in
  the flags, emit the help text and exit; do not enter any phase.
- `--tier=` combines with any workflow shortcut: the shortcut
  picks *which* phases run; `--tier=` picks the level at which
  they run.
- Without a workflow shortcut, the Phase 2 menu displays normally.
- Passing two workflow shortcuts (e.g., `--full --base`) is a
  configuration error — fail loudly with a clear message; do not
  proceed.
- Unknown flags are a configuration error — fail loudly; do not
  silently ignore.
- `--dry` does not conflict with any other flag. It only
  suppresses side effects (no delegated work, no file writes).
- `--dry` exits after Phase 3. Phase 4 (Interview) and beyond
  do not run.
- No flags at all → normal interactive flow (Orient → menu →
  confirm).

## Workflow Overview

This is a **9-phase workflow**:

1. **Orient** *(orchestrator)* — project state, ledger, recent
   sprints + retros, prior-art + dependency checks, per-phase tier
   assessment
2. **Phase Selection** *(orchestrator)* — menu with
   Orient-informed phase + tier recommendations
3. **Intent** *(orchestrator)* — concentrated intent document
   including alternative approaches considered
4. **Interview** *(orchestrator)* — adaptive human dialogue; exit
   early via "Skip"
5. **Draft** *(delegated, parallel)* — orch-side worker +
   opposite-side worker write competing drafts
6. **Critique** *(delegated, parallel, optional)* — orch-side
   worker critiques opposite's draft; opposite-side worker
   critiques orch's draft
7. **Merge / Promote** *(orchestrator)* — synthesize, apply
   simplest-viable filter, run sprint-sizing gate
8. **Reviews** *(delegated, parallel, optional)* — Devil's
   Advocate, Security, Architecture, Test Strategy, Observability,
   Performance/Scale, Breaking Change; each routed to its expert
   side
9. **Finalize** *(orchestrator)* — incorporate findings, DoR
   pre-flight, spike escape hatch, user approval, register in
   ledger

Use `TaskCreate` and `TaskUpdate` to track progress through each
phase.

---

## Phase 1: Orient

**Goal**: Understand current project state and recent direction,
surface any prior-art or dependency blockers, then assess
per-phase tier needs.

### Orient Steps

1. Read `CLAUDE.md` for project conventions.
2. Check sprint ledger status using the `/sprints --stats` skill.
   - Note any **in-progress** sprints and their relationship to the
     seed prompt — a sprint already in flight is critical context.
3. Review recent git activity to see what was actually shipped vs.
   what was planned:

   ```bash
   git log --oneline -20
   ```

4. Read the **3 most recent sprint documents + their retros** to
   understand recent work and what past sprints actually taught us:

   ```bash
   ls ./docs/sprints/*-sprint-plan-SPRINT-*.md 2>/dev/null | tail -3
   ls ./docs/sprints/*-sprint-retro-SPRINT-*.md 2>/dev/null | tail -3
   ```

   Focus especially on what was **deferred, underestimated, or
   left incomplete** — the retros are explicit about this. If a
   retro flags a recurring issue, weight it in the current plan.
5. Identify relevant code areas for the seed prompt:
   - Search for related modules, types, or patterns.
   - Note existing implementations that this plan might extend.
   - **Prior-art check**: before proposing new code, ask whether
     an existing OSS tool, library, framework, or internal skill
     already solves this. Prefer reuse over build. Note any
     candidates here; the drafts should defend the build-vs-reuse
     decision.
6. **Dependency prereq check**: list anything this sprint depends
   on that is *not yet done* — blocked upstream sprints, external
   approvals, infrastructure that must be stood up first,
   third-party releases. If a hard blocker exists, surface it
   before Phase 2 so the user can decide whether to plan this
   sprint at all. Soft dependencies go into the Intent
   Dependencies section; hard blockers may abort the workflow.
7. **Tier assessment**: using everything gathered above, make a
   best-effort pre-fill of the per-phase tier table (see
   "Per-Phase Tier Defaults" and "Tier-Adjustment Heuristics" in
   the Model Tiers section). Record one tier recommendation per
   delegated phase (5a, 5b, 6a, 6b, 8a–8g). These are just
   defaults — the user will see them in Phase 2 and may override.

### Orient Deliverable

Write a brief **Orientation Summary** (4–6 bullet points) covering:

- Current project state relevant to the seed
- Recent sprint themes/direction, including retro lessons and any
  recurring underestimates or deferred items
- Any in-progress sprints and how they interact with the seed
- Key modules/files likely involved
- Prior-art candidates (OSS, internal skills) worth considering
  before building
- Hard dependency blockers (if any) — call these out explicitly
- Constraints or patterns to respect

---

## Phase 2: Phase Selection

**Goal**: Present the phase menu (with tier recommendations) so the
user can confirm or adjust before any delegated work begins.

### Recommendation Heuristics

Use what you learned in Orient to pre-fill the optional phase
recommendations. Apply these signals:

| Signal from Orient | Suggested action |
|---|---|
| Novel architecture, new patterns, or significant refactor | Recommend Critique + Architecture Review |
| Touches auth, secrets, external APIs, or user data | Recommend Security Review |
| High correctness risk (parsers, migrations, spec compliance) | Recommend Test Strategy Review |
| Scope is vague, ambitious, or has prior history of underestimates | Recommend Devil's Advocate + Critique |
| Distributed system, long-running processes, prod telemetry | Recommend Observability Review |
| Hot paths, benchmarks, resource limits, autoscaling | Recommend Performance & Scale Review |
| Public APIs, schemas, config format, CLI changes | Recommend Breaking Change Review |
| Small, well-understood change in familiar territory | Suggest Lightweight |
| Opposite-side worker unavailable in this environment | Omit all opposite-side phases with a note |

### Present the Menu

Show the menu with each phase's enabled/disabled status, its
**expert side** where applicable, and its **recommended tier**
(from the Phase 1 tier assessment). Use `[✓]` for recommended,
`[ ]` for not recommended, and always show the tier:

```
  [✓] Phase 5a  Orch-side draft                              [High]   required
  [?] Phase 5b  Opposite-side draft                          [High]   optional
  [?] Phase 6a  Opposite critiques orch                      [Mid]    optional (needs 5b)
  [?] Phase 6b  Orch critiques opposite                      [Mid]    optional (needs 5b)
  [?] Phase 8a  Devil's Advocate (expert: codex)             [High]   optional
  [?] Phase 8b  Security Review (expert: claude)             [High]   optional
  [?] Phase 8c  Architecture Review (expert: claude)         [Mid]    optional
  [?] Phase 8d  Test Strategy Review (expert: codex)         [Mid]    optional
  [?] Phase 8e  Observability Review (expert: claude)        [Mid]    optional
  [?] Phase 8f  Performance & Scale Review (expert: codex)   [Mid]    optional
  [?] Phase 8g  Breaking Change Review (expert: claude)      [Mid]    optional
```

Replace each `[?]` with `[✓]` or `[ ]` per heuristics. Add a brief
rationale after each optional phase (enable/disable + any tier
bump relative to default).

**Flag-driven selection (skip the menu):** if `--auto`, `--full`,
`--base`, or `--dry` was passed, *do not* show the menu — the flag
already decided:

- `--auto` → treat as **Auto** (Orient recommendations)
- `--full` → treat as **Full** (all optional phases on)
- `--base` → treat as **Base** (required phases only)
- `--dry` → compute selections the same way `--auto` would (unless
  combined with `--full` or `--base`, which override), then hand
  off to Phase 3's dry-run exit

If `--tier=high` or `--tier=mid` was passed, override every
enabled phase's tier to that value — regardless of how the
phase set was chosen.

**Interactive menu (no workflow flags passed):** use
`AskUserQuestion` with these options:

- **Auto** — accept the pre-filled phase + tier selections
- **Full** — enable all optional phases (use recommended tiers)
- **Base** — skip all optional phases (tier decisions irrelevant
  for disabled phases)
- **Custom** — I'll choose each phase (and its tier) individually

If the user selects **Custom**, ask for each enabled phase in
sequence (one at a time via `AskUserQuestion`):

1. **Phase enable/disable** — keep enabled, or disable?
2. **Phase tier** — keep [recommended tier], or switch to
   [other tier]?

Skip the tier question for disabled phases. Record final
selections; reference them at the start of each delegated phase.

**Special case — Phase 5b skipped**: If the opposite-side draft
is disabled, Phase 6 is automatically skipped, and Phase 7
("Merge") becomes "Promote": write
`$REPORT_DIR/$REPORT_TS-sprint-plan-sprint.md` directly from the
orch-side draft, apply the simplest viable filter, run the sprint
sizing gate. Skip writing merge notes.

---

## Phase 3: Intent

**Goal**: Create a concentrated intent document that both draft
workers will use. In `--dry` mode, also produce the dry-run
preview at the end of this phase and exit.

### Intent Steps

1. Set up the report output directory (**skip in `--dry` mode** —
   no files will be written):

   ```bash
   REPORT_DIR=./docs/sprints
   REPORT_TS=$(date +%Y-%m-%dT%H-%M-%S)
   mkdir -p $REPORT_DIR
   ```

2. Compose the intent document.

   - **Normal mode**: write it to
     `$REPORT_DIR/$REPORT_TS-sprint-plan-intent.md`.
   - **`--dry` mode**: keep the content in memory only — do not
     write to disk.

   Use this template for the intent content:

```markdown
# Sprint Intent: [Title]

## Seed

[The original $ARGUMENTS prompt]

## Context

[Your orientation summary from Phase 1]

## Recent Sprint Context

[Brief summaries of the 3 recent sprints + retro lessons]

## Relevant Codebase Areas

[Key modules, files, patterns identified during orientation]

## Prior Art

[OSS tools, libraries, internal skills that might already solve
this. For each candidate: why use it, or why not.]

## Constraints

- Must follow project conventions in CLAUDE.md
- Must integrate with existing architecture
- [Any other constraints identified]

## Dependencies

- Hard blockers (must be resolved before this sprint starts): ...
- Soft dependencies (will be resolved during or alongside): ...

## Success Criteria

What would make this sprint successful?

## Verification Strategy

How will we know the implementation is correct?

- Reference implementation: [if any, how will we verify conformance?]
- Spec/documentation: [what defines correct behavior?]
- Edge cases identified: [list known edge cases that must be handled]
- Testing approach: [unit tests, differential testing, conformance
  suite, etc.]

## Uncertainty Assessment

- Correctness uncertainty: [Low/Medium/High] — [why]
- Scope uncertainty: [Low/Medium/High] — [why]
- Architecture uncertainty: [Low/Medium/High] — [why]

## Approaches Considered

Enumerate 2–3 distinct implementation approaches before committing
to a direction:

| Approach | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| [Approach A] | ... | ... | **Selected** — [reason] |
| [Approach B] | ... | ... | Rejected — [reason] |
| [Approach C] | ... | ... | Rejected — [reason] |

## Open Questions

Questions that the drafts should attempt to answer.

## Interview Refinements

*(Populated after Phase 4 — leave empty for now.)*
```


### Dry-run exit

If `--dry` was passed, after composing the intent above:

1. Assemble the preview output inline in your response:
   - **Orientation Summary** (Phase 1 bullets)
   - **Phase Selection table** (enabled/disabled + tier per phase,
     computed from flags or Orient recommendations)
   - **Intent Document** (rendered inline — *not written to disk*)
   - **Scope Summary** — one line: *"Would spawn N delegated
     workers across M phases; tier mix X High / Y Mid; expert
     routing A claude-side, B codex-side."*
2. Close with: *"Dry run complete. Re-run without `--dry` to
   execute."*
3. **Exit.** Do not proceed to Phase 4 or any later phase. Do not
   ask for user input.

### Handoff to Phase 4 (non-dry mode)

Before moving to Phase 4, ensure the **Approaches Considered** table
is complete. The selected approach should be clear; rejected
approaches should have explicit reasons. Both draft workers will
see this document — the approaches table prevents the opposite-side
worker from rediscovering an approach you already evaluated and
discarded.

---

## Phase 4: Interview

**Goal**: Refine understanding through human dialogue, with depth
proportional to uncertainty, **before** drafts are commissioned.
Drafting is compute-expensive; interview first so both workers start
from a refined intent.

### Step 1 — Assess Uncertainty

Before asking questions, evaluate the uncertainty level of this
sprint:

| Factor | Low Uncertainty | High Uncertainty |
| --- | --- | --- |
| **Correctness** | Well-understood domain | Reference impl, spec compliance |
| **Scope** | Seed is specific and bounded | Seed is vague or ambitious |
| **Architecture** | Extends existing patterns | New patterns, integration points |
| **Verification** | Standard testing sufficient | Conformance/differential testing |

Assign an uncertainty level:

- **Low**: 1–2 questions (routine feature, clear requirements)
- **Medium**: 3–4 questions (some ambiguity, moderate complexity)
- **High**: 5–7 questions (reference implementations, specs, novel
  architecture)

### Step 2 — Prioritize Questions by Impact

Order questions by their impact on sprint success. Always include
an escape hatch.

**Question categories** (ask in this priority order):

1. **Verification Strategy** (HIGH impact when correctness matters)
2. **Scope Validation** (HIGH impact when seed is ambiguous)
3. **Priority/Trade-offs** (MEDIUM impact)
4. **Technical Preferences** (MEDIUM impact)
5. **Sequencing/Dependencies** (LOW impact unless external factors)

### Step 3 — Conduct Adaptive Interview

Use `AskUserQuestion` iteratively. **Every question must include an
option to end the interview.**

```text
AskUserQuestion with options:
- [Substantive answer option 1]
- [Substantive answer option 2]
- "Skip — proceed to next phase" (ALWAYS include this)
```

**Interview flow**:

1. Ask the highest-impact question for this sprint's uncertainty
   profile.
2. If user selects "Skip — proceed to next phase", immediately end
   interview and move to Phase 5.
3. Otherwise, incorporate the answer and ask the next question.
4. Repeat until questions exhausted or user skips.

### Step 4 — Append Refinements to Intent

After the interview, populate the **Interview Refinements** section
of `$REPORT_DIR/$REPORT_TS-sprint-plan-intent.md` with a concise
summary of what the user clarified. Both draft workers read this
document, so refinements captured here will reach both drafts.


---

## Phase 5: Draft (delegated, parallel)

**Goal**: Commission two independent drafts from fresh workers. The
orchestrator does not draft.

Apply the **simplest viable filter** in the delegation prompts: for
every proposed task, workers should ask "is this strictly necessary
for the sprint's stated goal, or can it be deferred?" A plan that
ships is better than a plan that's complete.

### Phase 5a: Orch-side draft (required)

Delegate to an **orch-side worker** at the tier selected in Phase 2
for 5a (see Roles for how to pass the model flag for your side).
Substitute `ORCH_NAME` with your own side's literal name.

**Prompt**:

```
Read $REPORT_DIR/$REPORT_TS-sprint-plan-intent.md — this is a
concentrated intent for the next sprint. Read CLAUDE.md and
familiarize yourself with the project structure. Then write a
comprehensive sprint draft to
$REPORT_DIR/$REPORT_TS-sprint-plan-ORCH_NAME-draft.md using the
template in the "Draft Template" section of
~/.claude/skills/sprint-plan/SKILL.md. Do not read or reference any
opposite-side draft; write independently. Apply the simplest
viable filter — anything non-essential belongs in a Deferred
section. If the intent's Prior Art section lists reusable
alternatives, the draft must defend the build-vs-reuse decision
explicitly.
```

### Phase 5b: Opposite-side draft *(optional)*

> Skip if the opposite-side draft was disabled in Phase 2.

Delegate to an **opposite-side worker** at the tier selected in
Phase 2 for 5b. Substitute `OPPO_NAME`.

**Prompt**:

```
Please read $REPORT_DIR/$REPORT_TS-sprint-plan-intent.md — this
is a concentrated intent for our next sprint. Fully familiarize
yourself with the project structure (see CLAUDE.md) and project
goals. Then draft
$REPORT_DIR/$REPORT_TS-sprint-plan-OPPO_NAME-draft.md only. Do
not read or reference any other draft; write independently.
Apply the simplest viable filter — anything non-essential
belongs in a Deferred section. If the intent's Prior Art section
lists reusable alternatives, the draft must defend the
build-vs-reuse decision explicitly.
```

Launch 5a and 5b in parallel when both are enabled. Wait for both
to finish before moving on.

### Draft Template

Workers should produce drafts structured like this:

```markdown
# Sprint: [Title]

## Overview

2–3 paragraphs on the "why" and high-level approach.

## Build vs. Reuse

Address the Prior Art candidates from the intent. For each: why
we're building ourselves, or why we're adopting the existing
solution instead.

## Use Cases

1. **Use case name**: Description
2. ...

## Architecture

Diagrams (ASCII art), component descriptions, data flow.

## Implementation Plan

### P0: Must Ship

**Files:**
- `path/to/file.ext` — Description

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

## Performance & Scale Considerations

- Expected load, concurrency, resource ceilings
- Hot paths and their cost

## Breaking Changes

- What external contract changes, if any
- Compatibility shims or migration paths

## Observability & Rollback

- How will we verify the implementation is working correctly
  post-ship?
- What logs, metrics, or output changes prove correctness?
- Rollback plan if something breaks: [describe revert steps or
  fallback]

## Documentation

- [ ] Doc update 1

## Dependencies

- Sprint NNN (if any)
- External requirements

## Open Questions

Uncertainties needing resolution.
```


---

## Phase 6: Critique (delegated, parallel) *(optional)*

> **Skip this phase** if Phase 5b (opposite-side draft) was
> disabled in Phase 2 — there is nothing to compare against.
> Proceed directly to Phase 7 in Promote mode.

**Goal**: Get symmetric critiques of both drafts from fresh workers.
The orchestrator does not critique.

Each critique uses the tier selected in Phase 2 for its sub-phase.
Both critiques run in parallel.

### Phase 6a: Opposite-side critiques orch-side draft

Delegate to an **opposite-side worker** at Phase 6a's tier.

**Prompt**:

```
Read $REPORT_DIR/$REPORT_TS-sprint-plan-ORCH_NAME-draft.md and
write a formal critique to
$REPORT_DIR/$REPORT_TS-sprint-plan-ORCH_NAME-draft-OPPO_NAME-critique.md.
Cover: what ORCH_NAME got right, what it missed, what you would
do differently, and any over-engineering or gaps. Do not
reference or defer to your own draft; critique independently.
```

### Phase 6b: Orch-side critiques opposite-side draft

Delegate to an **orch-side worker** at Phase 6b's tier.

**Prompt**:

```
Read $REPORT_DIR/$REPORT_TS-sprint-plan-OPPO_NAME-draft.md and
write a formal critique to
$REPORT_DIR/$REPORT_TS-sprint-plan-OPPO_NAME-draft-ORCH_NAME-critique.md.
Cover: what OPPO_NAME got right that you missed, what gaps or
weaknesses the draft has, and what your own approach would
defend against it. Do not reference or defer to your own draft;
critique independently.
```

Launch 6a and 6b in parallel. Wait for both before moving on.

---

## Phase 7: Merge / Promote

**Goal**: Synthesize the best ideas into a final sprint document —
or, if the opposite-side draft was skipped, promote the orch-side
draft directly.

> **Promote mode** (Phase 5b skipped): Apply the simplest viable
> filter and sprint-sizing gate to the orch-side draft, then write
> it directly to `$REPORT_DIR/$REPORT_TS-sprint-plan-sprint.md`.
> Skip merge notes. Continue to Phase 8.
>
> **Merge mode** (Phase 5b ran): Follow the full merge process
> below.

### Merge Process

1. **Analyze both critiques**:
   - From the opposite-side critique of the orch-side draft: which
     criticisms are valid? What did the orch-side draft miss? What
     should be defended?
   - From the orch-side critique of the opposite-side draft: what
     weaknesses were identified? Which of the orch-side draft's
     choices does that reinforce?

2. **Compare the two drafts**:
   - Architecture approach differences
   - Phasing/ordering differences
   - Risk identification gaps
   - Definition of Done completeness
   - Build-vs-reuse verdicts

3. **Document the synthesis**:

   Write to `$REPORT_DIR/$REPORT_TS-sprint-plan-merge-notes.md`:

   ```markdown
   # Sprint NNN Merge Notes

   ## Orch-side Draft Strengths
   - ...

   ## Orch-side Draft Weaknesses (from opposite-side critique)
   - ...

   ## Opposite-side Draft Strengths
   - ...

   ## Opposite-side Draft Weaknesses (from orch-side critique)
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

4. **Apply the simplest viable filter**: review every proposed task
   across both drafts. Ask: "Is this strictly necessary for the
   sprint's stated goal, or can it be deferred?" Move non-essential
   items to the Deferred section.

5. **Sprint sizing gate**: assess whether the merged plan is
   appropriately scoped for a single sprint:
   - Does the plan have more than one natural delivery milestone?
   - Would a reasonable team realistically complete all P0 tasks in
     one sprint?
   - If oversized, propose splitting it now (before reviews),
     confirm with the user, and adjust scope before proceeding to
     Phase 8.

6. **Write the initial sprint document**:

   Create `$REPORT_DIR/$REPORT_TS-sprint-plan-sprint.md` using the
   Draft Template, incorporating:
   - Best ideas from both drafts
   - Responses to valid critiques
   - Interview refinements
   - P0/P1/Deferred tiering
   - Observability & Rollback, Performance & Scale, Breaking
     Changes, and Documentation sections


---

## Phase 8: Reviews (delegated, parallel) *(optional)*

**Goal**: Run any enabled review lenses against the final sprint
document. Each review is routed to its **expert side** — the model
family best suited to the lens, regardless of which side is
orchestrating — and runs at the tier selected in Phase 2.

### Expertise Routing

| Review | Expert side |
|---|---|
| Devil's Advocate | codex |
| Security | claude |
| Architecture | claude |
| Test Strategy | codex |
| Observability | claude |
| Performance & Scale | codex |
| Breaking Change | claude |

**Routing rule**: if the expert side equals `ORCH_NAME`, delegate
to the orch-side worker. If it equals `OPPO_NAME`, delegate to the
opposite-side worker. Tier for each review comes from Phase 2.

> Group enabled reviews by destination side and launch each group's
> delegations in parallel. Reviews on different sides are fully
> independent and can run simultaneously.

Each review operates on `$REPORT_DIR/$REPORT_TS-sprint-plan-sprint.md`.
Skip disabled reviews cleanly with no stub files.

### Phase 8a: Devil's Advocate *(expert: codex)*

> Skip if disabled in Phase 2.

**Prompt**:

```
Read $REPORT_DIR/$REPORT_TS-sprint-plan-sprint.md. This is a
finalized sprint plan. Your job is NOT to improve it — your job
is to attack it. Act as a senior skeptic who must approve this
plan before a single line of code is written. Write
$REPORT_DIR/$REPORT_TS-sprint-plan-devils-advocate.md with your
critique. Cover: (1) flawed assumptions — what is this plan
taking for granted that could be wrong? (2) scope risks — what
could balloon, be underestimated, or have hidden dependencies?
(3) design weaknesses — what architectural choices might we
regret? (4) gaps in the Definition of Done — what's missing
that could let a bad implementation 'pass'? (5) what's the most
likely way this sprint fails? Be specific and harsh. Every
concern should cite the relevant section of the plan.
```

### Phase 8b: Security Review *(expert: claude)*

> Skip if disabled in Phase 2.

**Prompt**:

```
Read $REPORT_DIR/$REPORT_TS-sprint-plan-sprint.md with a
security-focused lens. Write your audit to
$REPORT_DIR/$REPORT_TS-sprint-plan-security-review.md covering:
(1) attack surface — what new inputs, APIs, or trust boundaries
does this plan introduce? (2) data handling — any risks around
sensitive data, secrets, or PII? (3) injection and parsing risks
— new parsers, template engines, query builders, or eval-adjacent
code? (4) authentication/authorization — does this plan touch
auth flows or permission checks? (5) dependency risks — new
libraries or external services, and their known risk profile;
(6) threat model — given the project context in CLAUDE.md, what
is a realistic adversarial scenario for this sprint's changes?
Rate each finding: Critical / High / Medium / Low, and suggest
a concrete mitigation or DoD addition.
```

### Phase 8c: Architecture Review *(expert: claude)*

> Skip if disabled in Phase 2.

**Prompt**:

```
Read $REPORT_DIR/$REPORT_TS-sprint-plan-sprint.md for conformance
to existing project patterns and structural soundness. Write your
audit to
$REPORT_DIR/$REPORT_TS-sprint-plan-architecture-review.md covering:
(1) pattern conformance — does the plan's approach align with
conventions in CLAUDE.md? Note deviations. (2) coupling and
cohesion — does this plan introduce inappropriate coupling?
(3) schema and data model changes — are migrations, backwards
compatibility, or rollback implications addressed? (4) new
abstractions — are any new patterns proposed? Are they justified,
or does an existing pattern suffice? (5) integration points — are
all touch points with existing systems correctly identified and
handled? Rate each finding: Critical / High / Medium / Low, and
suggest a concrete plan adjustment or DoD addition.
```

### Phase 8d: Test Strategy Review *(expert: codex)*

> Skip if disabled in Phase 2.

**Prompt**:

```
Read $REPORT_DIR/$REPORT_TS-sprint-plan-sprint.md. Your job is to
attack the test strategy and Definition of Done. Act as a senior
engineer who must sign off on the testing approach before
implementation begins. Write
$REPORT_DIR/$REPORT_TS-sprint-plan-test-strategy-review.md. Cover:
(1) DoD gaps — which criteria are vague, unverifiable, or could
be gamed by a bad implementation? (2) missing edge cases — what
scenarios does the test plan fail to cover? (3) test approach
weaknesses — is the testing strategy proportionate to the
correctness risk? (4) verification blindspots — what could go
wrong in production that the tests would not catch? Be specific.
Every concern should cite the relevant section of the plan.
```


### Phase 8e: Observability Review *(expert: claude)*

> Skip if disabled in Phase 2.

**Prompt**:

```
Read $REPORT_DIR/$REPORT_TS-sprint-plan-sprint.md with an
observability lens. Write your audit to
$REPORT_DIR/$REPORT_TS-sprint-plan-observability-review.md
covering: (1) post-ship verification — can we actually prove this
is working correctly in production using only the logs, metrics,
and traces the plan describes? (2) failure-mode coverage — for
each Risk in the plan, is there a signal that would catch it
before users do? (3) rollback executability — is the rollback
plan actually runnable under load, with partial state, or mid-
incident? (4) alerting proportionality — are there SLO-bearing
paths that need alerts, or conversely alerts that would be noisy?
(5) debuggability — if a prod issue arises, what's the path from
symptom to root cause, and is the plan sufficient to support it?
Rate each finding: Critical / High / Medium / Low, and suggest
a concrete telemetry addition or DoD update.
```

### Phase 8f: Performance & Scale Review *(expert: codex)*

> Skip if disabled in Phase 2.

**Prompt**:

```
Read $REPORT_DIR/$REPORT_TS-sprint-plan-sprint.md with a
performance and scalability lens. Write your audit to
$REPORT_DIR/$REPORT_TS-sprint-plan-performance-review.md covering:
(1) hot paths — which code paths will see the most traffic, and
does the plan account for their cost? (2) resource ceilings —
memory, CPU, I/O, connection pools, file descriptors: anywhere
the plan could hit a limit under realistic load? (3) concurrency
— are there race conditions, lock contention, or serialization
bottlenecks introduced? (4) scaling behavior — does the plan
scale horizontally and vertically? Are autoscaling assumptions
documented? (5) load characteristics — what throughput, latency,
and tail-latency targets matter, and does the plan meet them?
(6) benchmark plan — how will performance be measured before and
after? Rate each finding: Critical / High / Medium / Low, and
suggest a concrete plan adjustment or DoD addition.
```

### Phase 8g: Breaking Change Review *(expert: claude)*

> Skip if disabled in Phase 2.

**Prompt**:

```
Read $REPORT_DIR/$REPORT_TS-sprint-plan-sprint.md with a
backwards-compatibility lens. Write your audit to
$REPORT_DIR/$REPORT_TS-sprint-plan-breaking-change-review.md
covering: (1) contract changes — enumerate every external
contract this plan modifies (public APIs, RPC signatures, schema
definitions, config formats, CLI flags, file formats, event
shapes). (2) consumer impact — for each contract change, who are
the consumers (internal callers, downstream services, external
users), and what breaks for them? (3) migration path — is there
a concrete migration plan (dual-write, feature flag, deprecation
window, version skew handling)? (4) compatibility shims — are
any needed, and is their removal tracked? (5) version signaling —
do version numbers, API headers, or schema versions reflect the
change? Rate each finding: Critical / High / Medium / Low, and
suggest a concrete plan adjustment or DoD addition.
```

Wait for all enabled review workers to finish before proceeding to
Phase 9.


---

## Phase 9: Finalize

### Step 1 — Incorporate Findings

Process each enabled review's output and patch findings into the
sprint document.

- **Devil's Advocate** — read
  `$REPORT_DIR/$REPORT_TS-sprint-plan-devils-advocate.md`. Evaluate
  each critique: if valid, patch into the sprint document now; if
  invalid, note why (brief inline comment or a "Critiques
  Addressed" section).
- **Security Review** — for Critical/High findings: update the
  sprint doc with mitigations in the relevant tasks or DoD. For
  Medium/Low: use judgment; add to Security Considerations if
  relevant.
- **Architecture Review** — for Critical/High findings: adjust the
  implementation plan or add DoD criteria. For Medium/Low: add to
  the Architecture section or note as a known trade-off.
- **Test Strategy Review** — read
  `$REPORT_DIR/$REPORT_TS-sprint-plan-test-strategy-review.md`. For
  each valid gap, strengthen the corresponding DoD criterion or
  add a missing test case.
- **Observability Review** — for Critical/High findings: add
  specific log/metric/trace requirements to tasks or DoD; tighten
  the rollback plan if flagged. For Medium/Low: extend the
  Observability & Rollback section.
- **Performance & Scale Review** — for Critical/High findings: add
  benchmark requirements, resource-limit assertions, or scaling
  assumptions to tasks or DoD. For Medium/Low: extend the
  Performance & Scale Considerations section.
- **Breaking Change Review** — for Critical/High findings: add
  migration tasks, compatibility shims, deprecation tracking, or
  version-signaling requirements. For Medium/Low: extend the
  Breaking Changes section.

### Step 2 — Spike Escape Hatch

If the incorporated findings reveal that uncertainty is *too high*
to commit a full sprint — e.g., Architecture Review says the chosen
approach is unvalidated, or Devil's Advocate flags assumptions that
can't be resolved without prototyping — propose a **feasibility
spike** instead:

- Surface the specific unresolved uncertainty.
- Recommend a time-boxed spike sprint (1–3 days, clear exit
  criteria) to resolve that uncertainty.
- Ask the user whether to (a) ship a spike plan instead, (b)
  proceed with the full sprint plan accepting the risk, or (c)
  narrow scope to what *can* be committed now and defer the rest.

Only trigger the spike escape hatch when the findings are
*structural* (the plan can't be saved by patching) — not for
routine patch-level critiques.

### Step 3 — Recommended Execution

Based on everything learned through Phases 1–8, recommend which
Claude model tier the user should run `/sprint-work` with. This
recommendation is separate from sprint-plan's own `--tier=`
(which only governs sprint-plan's delegated workers during
planning). Sprint-work supports three tiers:

| Recommended tier | Model  | Use when |
|---|---|---|
| `high`   | `opus`   | Complex / novel / high-risk sprints |
| `medium` | `sonnet` | Standard sprints with moderate scope |
| `low`    | `haiku`  | Trivial sprints (typo fixes, small refactors) |

**Recommendation heuristics:**

Bump toward **high** when any of these apply:

- Any Critical or High finding from Security, Architecture,
  Devil's Advocate, Breaking Change, Performance & Scale, Test
  Strategy, or Observability reviews
- Novel architecture, new abstractions, or spec/parser/migration work
- High uncertainty in Correctness, Scope, or Architecture
- Touches auth, secrets, PII, or production data paths

Settle on **medium** when:

- Standard extension of existing patterns
- Moderate scope, low-to-medium uncertainty
- Review findings all Medium/Low and already incorporated

Settle on **low** when:

- Trivial scope (typo, cosmetic, docstring, one-line bug fix)
- No review phases surfaced anything, or they weren't enabled
- Confident the work is mechanical

**Write the recommendation** as a dedicated section appended to
`$REPORT_DIR/$REPORT_TS-sprint-plan-sprint.md`:

```markdown
## Recommended Execution

**Model**: sonnet (medium tier)

Before running `/sprint-work`, set the session model:

    /model sonnet
    /sprint-work SPRINT-NNN

**Rationale**: Standard extension of existing patterns. Security
Review flagged one Medium finding (incorporated in DoD).
Architecture Review had no findings. Sonnet's capabilities match
this scope without overkill.
```

Populate **Model**, the two command lines, and the **Rationale**
with specifics drawn from the actual reviews and uncertainty
assessment for this sprint.

### Step 4 — Definition of Ready Pre-Flight

Before presenting to the user, verify every item below. If any
fails, address it first.

- [ ] All **blocking open questions** are resolved — no unresolved
  items in the Open Questions section
- [ ] All **dependencies** are identified and either complete or
  explicitly tracked with a plan
- [ ] **Sprint sizing gate passed** in Phase 7 — plan is scoped
  for a single delivery
- [ ] **Critical/High findings** from any enabled Phase 8 reviews
  are incorporated into tasks or Definition of Done
- [ ] **P0 tasks are clearly distinguished** from P1 and Deferred
  — nothing P1 or Deferred is blocking the sprint
- [ ] **Rollback plan** is documented for any changes to shared
  infrastructure or agent configs
- [ ] **Documentation tasks** are listed for anything that
  introduces new behavior or changes existing behavior
- [ ] **Recommended Execution** section is populated with a tier,
  command lines, and rationale

### Step 5 — User Approval

Present the final plan to the user for review, in this order:

1. **Review findings summary** — bullet list of what was
   incorporated from each enabled Phase 8 review and what was
   explicitly rejected, with brief reasoning for rejections.
2. **Full sprint document rendered inline** — emit the entire
   contents of `$REPORT_DIR/$REPORT_TS-sprint-plan-sprint.md`
   directly in your response so the user can read what they are
   about to approve without opening a separate file. Render it as
   markdown inside a fenced block or as native markdown content
   (whichever presents more readably in the Claude Code
   transcript).
3. **Recommended Execution block** — repeat the Recommended
   Execution section last and prominently so it's the final thing
   the user reads before deciding. Tier, `/model` command,
   `/sprint-work` command, and rationale.
4. **Approval prompt** — ask the user to approve the plan as
   shown, or request changes.

If the user requests changes, iterate on the sprint document
directly (the file on disk), then re-render Steps 1–3 before
re-prompting.


### Step 6 — Register Sprint

After the user approves, register the sprint so `/sprint-work` can
find it:

1. Determine the next sprint number using the sprints skill:

   ```bash
   /sprints --stats
   ```

   Use the next available sprint number (one greater than the
   highest numbered sprint in the ledger; start at `001` if the
   ledger is empty). Zero-pad to three digits.

2. Extract the sprint title from the first `# Sprint:` heading in
   `$REPORT_DIR/$REPORT_TS-sprint-plan-sprint.md`.

3. Rename the sprint document to include the sprint number:

   ```bash
   mv "$REPORT_DIR/$REPORT_TS-sprint-plan-sprint.md" \
      "$REPORT_DIR/$REPORT_TS-sprint-plan-SPRINT-NNN.md"
   ```

4. **Compute the participants list** — who actually produced
   planning artifacts for this sprint. Compute from which phases
   *ran*, not which were enabled. A phase that was enabled but
   produced no artifact (e.g., worker failed, skipped at runtime)
   does not count.

   - Include `claude` if any Claude-side worker ran:
     - Phase 5a or 5b delegated to a Claude-side worker
       (orch-side when orchestrator is Claude; opposite-side when
       orchestrator is Codex)
     - Phase 6a or 6b delegated to a Claude-side worker
     - Any Phase 8 review routed to Claude (Security,
       Architecture, Observability, Breaking Change)
   - Include `codex` if any Codex-side worker ran:
     - Phase 5a or 5b delegated to a Codex-side worker
     - Phase 6a or 6b delegated to a Codex-side worker
     - Any Phase 8 review routed to Codex (Devil's Advocate,
       Test Strategy, Performance & Scale)
   - The orchestrator itself does not count as a participant —
     only delegated workers that produced artifacts do.
   - Emit the list alphabetically (the ledger normalizes this,
     but emit in order for readability).

   Single-agent example (only Claude-side workers ran):
   `claude`

   Both-sides example (Phase 5b ran as opposite-side, or any
   Phase 8 review routed to the opposite side):
   `claude,codex`

   This participants list is what the `/commit` skill will later
   read to build multi-agent `Co-authored-by:` trailers for the
   sprint-artifact commit.

5. Register the sprint in the ledger:

   ```bash
   /sprints --add NNN "Title" --recommended-model=<tier> --participants=<list>
   ```

   `<tier>` is the model name from the Recommended Execution block
   (`opus` / `sonnet` / `haiku`). Recording it lets `/sprints
   --velocity` compare recommendations to the model that actually
   ran the sprint.

   `<list>` is the comma-separated participants list computed in
   step 4 above (e.g. `claude` or `claude,codex`).

6. Tell the user the sprint was registered as `SPRINT-NNN` at
   `$REPORT_DIR/$REPORT_TS-sprint-plan-SPRINT-NNN.md`. Repeat
   the **Recommended Execution** block in this final message so
   the exact `/model` and `/sprint-work` commands are the last
   thing the user sees before running the sprint.

---

## File Structure

After `/sprint-plan` completes, you'll have (files marked `*` are
only created when the corresponding optional phase ran):

```text
./docs/sprints/
├── $REPORT_TS-sprint-plan-intent.md
├── $REPORT_TS-sprint-plan-ORCH_NAME-draft.md
├── $REPORT_TS-sprint-plan-OPPO_NAME-draft.md                       * (Phase 5b)
├── $REPORT_TS-sprint-plan-ORCH_NAME-draft-OPPO_NAME-critique.md    * (Phase 6a)
├── $REPORT_TS-sprint-plan-OPPO_NAME-draft-ORCH_NAME-critique.md    * (Phase 6b)
├── $REPORT_TS-sprint-plan-merge-notes.md                           * (Merge mode)
├── $REPORT_TS-sprint-plan-devils-advocate.md                       * (Phase 8a)
├── $REPORT_TS-sprint-plan-security-review.md                       * (Phase 8b)
├── $REPORT_TS-sprint-plan-architecture-review.md                   * (Phase 8c)
├── $REPORT_TS-sprint-plan-test-strategy-review.md                  * (Phase 8d)
├── $REPORT_TS-sprint-plan-observability-review.md                  * (Phase 8e)
├── $REPORT_TS-sprint-plan-performance-review.md                    * (Phase 8f)
├── $REPORT_TS-sprint-plan-breaking-change-review.md                * (Phase 8g)
└── $REPORT_TS-sprint-plan-SPRINT-NNN.md  (renamed after approval)
```

Retros live alongside plans at
`$REPORT_TS-sprint-retro-SPRINT-NNN.md` and are written by
`/sprint-work` after completion.


---

## Output Checklist

At the end of this workflow, you should have:

- [ ] Orientation summary complete (includes retros, prior-art,
  dependency prereq check, tier assessment)
- [ ] Per-phase tier defaults pre-filled based on Orient signals
- [ ] `REPORT_DIR` and `REPORT_TS` set; `$REPORT_DIR` created
- [ ] Phase selections **and tier selections** recorded and
  respected
- [ ] Intent document written
  (`$REPORT_TS-sprint-plan-intent.md`) with Prior Art and
  Approaches Considered tables
- [ ] Alternative approaches enumerated; one selected with
  rejections documented
- [ ] Interview conducted (adaptive to uncertainty; user may exit
  early via "Skip"); refinements appended to intent
- [ ] Orch-side draft received
  (`$REPORT_TS-sprint-plan-ORCH_NAME-draft.md`) from delegated
  worker at the selected tier
- [ ] *(optional)* Opposite-side draft received at the selected
  tier
- [ ] *(optional)* Opposite-side critique of orch-side draft
  received at the selected tier
- [ ] *(optional)* Orch-side critique of opposite-side draft
  received at the selected tier
- [ ] Simplest viable filter applied to merged/promoted plan
- [ ] Sprint sizing gate passed (plan is scoped for a single
  sprint)
- [ ] *(optional)* Merge notes written — skipped in Promote mode
- [ ] Sprint document written
  (`$REPORT_TS-sprint-plan-sprint.md`)
- [ ] *(optional)* Each enabled review received at the selected
  tier (Devil's Advocate, Security, Architecture, Test Strategy,
  Observability, Performance & Scale, Breaking Change)
- [ ] *(optional)* All enabled review findings incorporated or
  explicitly rejected in the sprint document
- [ ] Spike escape hatch evaluated (trigger or bypass — explicit
  decision)
- [ ] **Recommended Execution** section populated in the sprint
  document with tier, `/model` command, `/sprint-work` command,
  and rationale
- [ ] Definition of Ready pre-flight passed (all 8 items checked)
- [ ] User approved the final document; Recommended Execution
  block shown prominently at approval time
- [ ] Participants list computed from which phases actually ran
  (claude-side workers → include `claude`; codex-side workers →
  include `codex`)
- [ ] Sprint registered in ledger with `/sprints --add NNN "Title" --recommended-model=<tier> --participants=<list>`
  and renamed to
  `$REPORT_DIR/$REPORT_TS-sprint-plan-SPRINT-NNN.md`
- [ ] Recommended Execution block repeated in the final message
  so `/model` + `/sprint-work` commands are the last thing the
  user sees

---

## Reference

- Report output: `./docs/sprints/` (relative to cwd)
- Sprint documents: `./docs/sprints/$REPORT_TS-sprint-plan-SPRINT-NNN.md`
- Retros: `./docs/sprints/$REPORT_TS-sprint-retro-SPRINT-NNN.md`
- Project overview: `CLAUDE.md`
