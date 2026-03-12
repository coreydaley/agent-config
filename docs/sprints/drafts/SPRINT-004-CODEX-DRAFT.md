# Sprint 004 Codex Draft: audit-security command

## Sprint Objective
Add `commands/audit-security.md`, a dual-agent security audit command that mirrors the proven `sprint-plan` workflow shape, produces a standard `docs/sprints/SPRINT-NNN.md` remediation sprint, and can be executed directly with `/sprint-work` without inventing separate remediation infrastructure.

## Problem Statement
The repo already has a mature collaborative planning pattern in `commands/sprint-plan.md`: concentrated intent, independent Claude/Codex work, synthesis, a Codex devil's advocate pass, and a final sprint artifact. There is no equivalent command for security auditing, even though security work has the same need for independent review, structured synthesis, and actionable follow-through.

The intent settles the biggest product decision: this sprint should create one command, `audit-security`, not a pair of review/remediation commands. The output should remain a normal sprint document in `docs/sprints/SPRINT-NNN.md` so the existing `/sprint-work` command can execute it. That keeps the architecture aligned with the rest of the repo and avoids duplicating execution logic.

## Guiding Principles
- Reuse existing command and sprint patterns rather than introducing new workflow infrastructure.
- Keep the command machine-usable: prompts, file names, and output sections should be explicit and deterministic.
- Keep Gemini conversion compatibility intact: simple frontmatter, no tricky multiline frontmatter constructs.
- Treat security findings as planning input, not as a separate tracking system.
- Favor narrow text edits over script changes.

## Scope

### In Scope
1. Add `commands/audit-security.md` with a multi-phase dual-agent audit workflow.
2. Define the audit artifact flow in `docs/security/` for intermediate files and `docs/sprints/SPRINT-NNN.md` for the final remediation sprint.
3. Encode severity mapping from findings to sprint priority: Critical/High -> P0, Medium -> P1, Low -> Deferred.
4. Ensure the final output is structured so `/sprint-work` can execute it without manual reshaping.
5. Document the new command in `README.md` so users know how to invoke it across supported agents.

### Out of Scope
1. Adding a second remediation command such as `audit-security-address`.
2. Changing `commands/sprint-work.md` behavior beyond what is already needed to consume a normal sprint document.
3. Building scanners, linters, or automated code-analysis tooling.
4. Creating a separate non-sprint security report format as the primary deliverable.

## Key Decisions
1. **One command, one output contract**: `audit-security` produces a normal sprint document, not a bespoke report workflow.
2. **`audit-*` namespace**: use `audit-security` as the first command in an extensible audit family.
3. **Intermediate artifacts live under `docs/security/`**: keep audit working files separate from sprint planning drafts while preserving `docs/sprints/` as the final source of executable work.
4. **Codex remains the adversarial reviewer**: preserve the established pattern where Codex independently drafts and later attacks the synthesized plan.
5. **No script changes unless proven necessary**: command authoring and README updates should be sufficient.

## Implementation Plan

### P0-A: Author the `audit-security` Command
**Goal**: Create the command file and make its workflow explicit, complete, and consistent with existing command conventions.

**Files:**
- `commands/audit-security.md`
- `commands/sprint-plan.md`
- `commands/sprint-work.md`

**Tasks:**
- [ ] Add `commands/audit-security.md` with the same frontmatter/body style used by existing commands.
- [ ] Define the command arguments clearly: optional path scope or audit target text, with sane default behavior when no scope is provided.
- [ ] Write the full audit workflow so it is sequential and unambiguous for the executing agent.
- [ ] Mirror the proven collaborative shape from `commands/sprint-plan.md`, but adapt the phases for security review rather than feature planning.
- [ ] Ensure all Codex invocations use `codex exec "..."` with no `--model` or `--full-auto` flags.

**Acceptance:**
- `commands/audit-security.md` exists with valid Markdown command structure and YAML frontmatter.
- The command can be read top-to-bottom without unresolved actor or phase ambiguity.
- All Codex calls match repo conventions exactly.

### P0-B: Define Security Audit Artifacts and Final Sprint Output
**Goal**: Make the output format deterministic enough for synthesis and later sprint execution.

**Files:**
- `commands/audit-security.md`
- `docs/sprints/README.md`

**Tasks:**
- [ ] Specify the intermediate files the command should create in `docs/security/` for Claude's audit, Codex's audit, synthesis, and Codex devil's advocate review.
- [ ] Specify how the command determines the next sprint number and writes the final remediation plan to `docs/sprints/SPRINT-NNN.md`.
- [ ] Require that findings be translated into actionable sprint tasks rather than left as prose-only observations.
- [ ] Encode severity mapping rules directly in the command: Critical/High -> P0, Medium -> P1, Low -> Deferred.
- [ ] Align the final sprint shape with the conventions in `docs/sprints/README.md` so `/sprint-work` can consume it.

**Acceptance:**
- The command names every intermediate and final artifact path it expects to create.
- The final output contract is a normal sprint doc, not a one-off template.
- Severity mapping is explicit and cannot be inferred differently by different agents.

### P0-C: Make the Audit Output Actionable and Operator-Safe
**Goal**: Ensure the resulting sprint is useful, bounded, and safe to execute.

**Files:**
- `commands/audit-security.md`

**Tasks:**
- [ ] Require each finding to include affected area, risk summary, concrete remediation action, and verification expectation.
- [ ] Instruct the synthesizing phase to deduplicate overlapping findings from Claude and Codex.
- [ ] Add explicit handling for the "no findings" case: produce a clean-bill report plus a minimal sprint or halt behavior, whichever best preserves ledger and sprint hygiene.
- [ ] Add explicit handling for optional scope input so path-scoped audits do not overclaim repo-wide coverage.
- [ ] Require the final sprint to include verification steps tied to each remediation cluster.

**Acceptance:**
- The command defines what makes a finding actionable.
- The command distinguishes scoped audits from full-repo audits.
- The no-findings path is explicit rather than implied.

### P1: Document and Integrate the New Command
**Goal**: Surface the new command to users and keep repo documentation aligned.

**Files:**
- `README.md`

**Tasks:**
- [ ] Add `audit-security` to the commands overview and invocation examples for Claude, Codex, and Gemini.
- [ ] Describe how `audit-security` relates to `/sprint-work`.
- [ ] Keep wording consistent with the repo's agent capability matrix and command naming style.

**Acceptance:**
- README users can discover and invoke the new command without reading the source file first.
- The docs do not mention a separate remediation command.

### Deferred
- Automatic security scanner integration — deferred because the intent is about workflow orchestration, not tooling expansion.
- Changes to `commands/sprint-work.md` to special-case security sprints — deferred unless the normal sprint format proves insufficient.
- Additional `audit-*` commands such as dependency or performance audits — deferred until the namespace proves useful in practice.

## Files Summary

| File | Action | Purpose |
|---|---|---|
| `commands/audit-security.md` | Create | Define the new dual-agent security audit workflow |
| `README.md` | Modify | Document invocation and relationship to existing sprint commands |
| `commands/sprint-plan.md` | Reference only | Structural model for multi-agent drafting, synthesis, and devil's advocate flow |
| `commands/sprint-work.md` | Reference only | Execution contract the final sprint output must satisfy |
| `docs/sprints/README.md` | Reference only | Canonical sprint document format and naming conventions |

## Acceptance Criteria
- [ ] `commands/audit-security.md` exists and follows the repo's command authoring conventions.
- [ ] The command uses a multi-phase Claude/Codex workflow with independent reviews, synthesis, a Codex devil's advocate pass, and final sprint output.
- [ ] The command writes intermediate audit artifacts under `docs/security/`.
- [ ] The final output is `docs/sprints/SPRINT-NNN.md`.
- [ ] Severity mapping is explicit: Critical/High -> P0, Medium -> P1, Low -> Deferred.
- [ ] The final sprint contains actionable implementation tasks and verification guidance that `/sprint-work` can execute directly.
- [ ] README documentation includes `audit-security` examples for supported agents.
- [ ] No separate remediation command is introduced.

## Verification Plan
1. Read-through verification: walk the command phase by phase and confirm each artifact it references is produced before a later phase consumes it.
2. Prompt verification: inspect every `codex exec` prompt for missing context, forbidden flags, or ambiguous instructions.
3. Output contract verification: compare the command's final sprint requirements against `docs/sprints/README.md` and `commands/sprint-work.md`.
4. Edge-case verification:
   - no scope argument provided
   - path-scoped audit provided
   - overlapping findings from both agents
   - no findings discovered
5. Documentation verification: ensure README examples match actual command names and supported agents.

## Risks and Mitigations
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| The command drifts from the established `sprint-plan` pattern and becomes harder to maintain | Medium | High | Treat `commands/sprint-plan.md` as the reference structure and reuse its proven sequencing |
| The final report is too prose-heavy for `/sprint-work` to execute cleanly | Medium | High | Force findings into sprint tasks with explicit severity-to-priority mapping |
| `docs/security/` artifact naming becomes inconsistent across phases | Medium | Medium | Define every expected file path directly in the command text |
| The no-findings case creates meaningless sprint noise | Low | Medium | Decide and document one deterministic no-findings behavior in the command |
| README examples drift from actual supported invocation patterns | Low | Low | Update examples at the same time as the command file |

## Definition of Done
- [ ] `commands/audit-security.md` is authored and internally consistent.
- [ ] The command's workflow clearly distinguishes independent audit, synthesis, adversarial review, and final sprint generation.
- [ ] The command explicitly creates intermediate artifacts in `docs/security/` and a final sprint in `docs/sprints/`.
- [ ] Severity mapping and finding-to-task translation are explicit in the command text.
- [ ] `README.md` documents the new command and its supported invocation forms.
- [ ] No script changes are required to support the new command.
- [ ] Manual read-through passes for full-repo, scoped, overlapping-findings, and no-findings scenarios.
