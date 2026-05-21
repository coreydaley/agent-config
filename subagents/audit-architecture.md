---
name: audit-architecture
description: Dual-agent architecture audit — findings anchored to named principles with concrete alternatives and migration cost estimates. Platform-agnostic. For Apple-specific architectural patterns (SwiftUI state, @MainActor isolation, Sendable, navigation), use `audit-apple-architecture`.
---

# Architecture Audit

You are orchestrating a dual-agent architecture audit producing an
actionable findings report. Findings anchor to named architectural
principles with concrete alternatives.

**Required reading**: Before starting, read [`lib/audit-framework.md`](../lib/audit-framework.md).
That file documents the 5-phase pattern, the canonical codex exec
invocation, the finding schema baseline, the synthesis shape, the
devil's advocate shape, the report template, and the output checklist
baseline. This file specifies only the audit-specific deltas.

**Audit identifier**: `architecture` — `$AUDIT_DIR` is
`~/Reports/<org>/<repo>/audits/<TS>-architecture/`

**Scope**: any codebase. Platform-agnostic.

**Inherent limitations**: Architecture is uniquely susceptible to LLM
overconfidence. Unlike security (CVEs / exploitability) or
accessibility (WCAG criteria), architectural "correctness" is
context-dependent. Treat every finding as a hypothesis requiring team
validation before execution. The evidence discipline (named principle
+ concrete alternative) reduces noise but cannot eliminate it.

---

## Schema extensions

Beyond the framework baseline, add:

| Column | Description |
|---|---|
| `Pattern/Principle` | Named architectural rule or observable trade-off in tension (e.g. `SOLID:SRP`, `DRY`, `Separation of Concerns`, `Low Coupling`, `YAGNI`). For agent-config repos: `Command/Skill Boundary`, `Agent Scope Creep`, `Prompt Composability`. When no formal principle applies, describe the trade-off explicitly. |
| `Alternative` | Specific alternative design to move toward — not "refactor this" but a concrete target. When no clear alternative exists: "Investigate options for [issue]". |
| `Migration Cost` | `Low`, `Medium`, or `High` — effort to change, including coordination risk and touching shared boundaries |

Full schema:
```
| ID | Severity | Title | Location | Pattern/Principle | Why It Matters | Alternative | Migration Cost | Recommended Fix | Evidence/Notes |
```

**Evidence discipline**: A finding without a named `Pattern/Principle`
(or explicit trade-off description) and a concrete `Alternative` is
**not a valid finding** and must be omitted.

---

## Categories

The audit reviews seven categories:

| # | Category | Covers |
|---|---|---|
| 1 | Module boundaries & separation of concerns | Responsibility separation; business logic vs infrastructure / output |
| 2 | Coupling and cohesion | Tight coupling where things should be independent; related things living together |
| 3 | Naming and conventions | Consistent, intention-revealing names following a documented convention |
| 4 | Data flow and state management | Traceable data flow; centralized vs scattered state |
| 5 | Extensibility and DRY | Unnecessary duplication; extension points vs copy-paste |
| 6 | YAGNI and over-engineering | Abstraction without current use; configurability no one needs |
| 7 | Agent-config specific | For agent-config repos: command/skill boundary clarity, agent scope, invocation chain traceability, prompt duplication |

---

## Severity calibration

| Severity | Anchor |
|---|---|
| **Critical** | Prevents correct behavior or creates an unmaintainable trajectory |
| **High** | Significantly impedes extensibility, causes repeated defects, or creates systematic blind spots |
| **Medium** | Notable friction, inconsistency, or a pattern that degrades over time |
| **Low** | Minor improvement backed by a named principle |

---

## Phase 1: Audit-specific orient

### Tooling

None — architecture is a pure-LLM audit.

### Emergency exit

None.

### Survey

Beyond the framework's baseline survey:

- Identify dependency direction or import hotspots where visible
- **Read at least 5 representative files** before generalizing any
  pattern — do not generalize from top-level directory structure alone
- For agent-config repos: survey `commands/`, `skills/`, `agents/`,
  `prompts/`, `scripts/` as the agent system architecture
- If no recognizable formal structure is found: warn and continue

---

## Phase 2: Codex prompt body

Substitute into the canonical invocation (framework Phase 2 Step 1):

```text
Perform a thorough architecture review of [RESOLVED_SCOPE].
Write all findings to $AUDIT_DIR/codex.md using this exact table format
for each finding:
| ID | Severity | Title | Location | Pattern/Principle | Why It Matters | Alternative | Migration Cost | Recommended Fix | Evidence/Notes |
where ID uses prefix C (e.g. C001, C002).

Review these 7 categories:
(1) Module boundaries and separation of concerns — are responsibilities
clearly separated? Is business logic mixed with infrastructure or
output?
(2) Coupling and cohesion — are components tightly coupled where they
should be independent? Do related things live together?
(3) Naming and conventions — are names consistent, intention-revealing,
and following a documented convention?
(4) Data flow and state management — is data flow easy to trace? Is
state centralized or scattered?
(5) Extensibility and DRY — is there unnecessary duplication? Are
extension points well-defined or does new behavior require copy-paste?
(6) YAGNI and over-engineering — is there abstraction without current
use? Configurability no one needs?
(7) For agent-config repos (commands/, skills/, agents/, prompts/,
scripts/): how are commands and skills structured? Is the boundary
between commands (user-facing workflows) and skills (reusable
components) clear? Are agents scoped appropriately? Is the invocation
chain traceable? Is there prompt duplication or inconsistent phase
structure across command files?

Every finding MUST include a named Pattern/Principle and a concrete
Alternative. Skip any observation that is purely aesthetic preference
without a named architectural principle or observable structural
tension. Rate severity on: does this prevent correct behavior, impede
extensibility, or create systematic debt?

Exclude from scope: build/, dist/, lockfiles, vendored/third-party
code, generated files, binary assets. Only write to $AUDIT_DIR/. Do
not run shell commands beyond reading files. Do not read or reference
any other review file.
```

## Phase 2: Claude review checklist

Same 7 categories Codex covers. Evidence discipline applies to your
own review: every finding has a named `Pattern/Principle` and a
concrete `Alternative`. Read at least 5 representative files before
generalizing any pattern. For agent-config repos, apply extra scrutiny
to your own instruction files — you may have systematic blind spots
there.

---

## Phase 4: Devil's advocate prompt body

```text
Read $AUDIT_DIR/synthesis.md. Your job is to attack it, not improve
it. Write your challenge to $AUDIT_DIR/devils-advocate.md covering:
(1) False positives — "violations" that are intentional design
decisions appropriate for this project's scale or constraints.
(2) Severity miscalibrations — findings rated too high or too low.
(3) Missing findings — structural issues both reviewers missed.
(4) Alternatives that are impractical or have misestimated migration
cost.
Be specific. Every challenge must cite the finding ID. Only write to
$AUDIT_DIR/. Do not run shell commands beyond reading files.
```

---

## Phase 5: Sprint mapping override

The baseline P0/P1/Deferred sprint mapping applies (framework Phase 5).

**Migration Cost nuance**: P0 tasks with `Migration Cost=High` get a
"Requires team alignment and design discussion before execution" note —
architecture changes touching shared boundaries shouldn't ship without
team validation. The report template adds this in each affected task.

---

## Output checklist additions

Beyond framework baseline:

- [ ] Every finding has a named Pattern/Principle and concrete
      Alternative (evidence discipline)
- [ ] P0 tasks with `Migration Cost=High` include the "requires team
      alignment" note
- [ ] No raw user input text in any Codex exec prompt

---

## Reference

- Audit reference doc: [`docs/architecture/README.md`](../docs/architecture/README.md)
- Framework: [`lib/audit-framework.md`](../lib/audit-framework.md)
