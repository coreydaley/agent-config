# Claude's Critique of SPRINT-006-CODEX-DRAFT.md

## What Codex Got Right

1. **Guiding Principles section** — the opening principles block ("reuse workflow instead
   of inventing architecture-specific orchestration," "favor smallest viable scope") is
   excellent framing that my draft lacks. Worth incorporating into the merged draft.

2. **Explicit Out of Scope section** — Codex calls out ADR workflow, scoring systems,
   and architecture automation as explicitly out of scope. More precise than my "Deferred"
   section and prevents scope creep at authoring time.

3. **Schema example row** — Codex provides a concrete example row in the finding schema
   block. This is more useful than a format-only template; it shows reviewers exactly what
   "DRY / consistency tension" looks like as a finding. Strong improvement over my draft.

4. **Verification Plan section** — Codex has a dedicated, numbered verification plan
   covering compare-to-audit-security, schema inspection, codex-exec-prompt audit, and
   specific edge-case checks. My draft folds verification into the Definition of Done.
   The separate section is clearer and easier to follow during sprint execution.

5. **P0 split into A/B/C sub-tasks** — breaking implementation into "author the command"
   (P0-A), "synthesis + devil's advocate behavior" (P0-B), and "sprint output contract"
   (P0-C) makes it easier to track incremental progress on a single file. My single P0-A
   is harder to check off partially.

6. **Agent-config coverage** — Codex explicitly mentions `prompts/` and `scripts/` in
   addition to `commands/`, `skills/`, `agents/`. More complete for repos with those
   additional directories.

7. **Assumptions section** — explicit assumptions about `audit-security` as canonical
   base, agent-config awareness as default (not a mode), and README as optional. Good
   documentation hygiene.

## What Codex Missed or Got Wrong

1. **Schema redundancy: `Alternative` and `Recommended Fix` are duplicate columns.**
   Codex's schema has 10 columns including both `Alternative` (the better approach) and
   `Recommended Fix` (the concrete next step). For architecture findings, the alternative
   IS the recommended fix. Keeping both will create reviewer confusion about which column
   to populate. Should merge: use `Alternative` to capture the better approach, and
   incorporate the concrete step into that column. My draft has the same set but without
   the redundancy.

2. **Missing `docs/architecture/README.md` as P1-B.** Codex's P1 is only `README.md`.
   The `audit-security` sprint (SPRINT-004) shipped with a `docs/security/README.md`
   for the artifact directory; SPRINT-005 similarly included directory READMEs for
   `docs/design/` and `docs/accessibility/`. Omitting `docs/architecture/README.md`
   breaks family consistency and leaves the artifact directory undocumented.

3. **Evidence discipline instruction is in the principles but not in the Phase 2 prompt.**
   Codex says "require findings to be grounded in observed structure, named principles,
   or explicit tradeoff reasoning" in P0-B, but doesn't explicitly include this
   instruction in the Phase 2 Codex exec prompt. The discipline must be stated IN the
   prompt — agents following the command won't read P0-B task descriptions while
   running Phase 2. My draft includes this directly in the prompt text.

4. **No explicit phase deliverable format.** Codex describes each phase's tasks well but
   doesn't specify the exact format of intermediate artifacts (e.g., the header structure
   for `NNN-SYNTHESIS.md`). `audit-security` provides an explicit synthesis document
   template with `## Scope`, `## Summary`, `## Unified Findings`, and
   `## Rejected Devil's Advocate Challenges` sections. Without this, synthesis outputs
   will vary across runs.

5. **No-findings case is in acceptance criteria but not in Phase 5 instructions.**
   Codex mentions "the no-findings path still produces a verifiable sprint artifact" in
   P0-C acceptance but doesn't specify what the no-findings sprint looks like. My draft
   has an explicit no-findings task template ("Verify no findings — [scope], [date]")
   matching `audit-security`'s pattern.

6. **Missing migration cost note in the user handoff.** Codex's Phase 5 correctly
   instructs the user to review ordering before running `/sprint-work`, but doesn't
   specifically call out migration cost as a reason — high-migration-cost P0 tasks may
   need team alignment before execution. A one-line note would close this.

## What I Would Defend From My Own Draft Against Codex's Approach

- **Explicit evidence discipline in the Phase 2 prompt body**: critical for consistency
  across runs, must live in the prompt not just the principle description.
- **`docs/architecture/README.md` as P1-B**: family consistency with SPRINT-004/005
  pattern.
- **Explicit synthesis document template**: needed to get consistent, mergeable output
  from Phase 3 across different runs.
- **No-findings explicit task template**: needed for completeness; Codex acknowledges it
  but doesn't specify it.

## Net Verdict

Codex's draft is cleaner at the structural level (guiding principles, out-of-scope,
verification plan, P0 sub-task breakdown, example schema row). My draft is stronger on
implementation detail (evidence discipline in prompts, synthesis template, no-findings
handling, P1-B directory README). The merge should take Codex's structural framing and
my implementation specifics, and resolve the `Alternative`/`Recommended Fix` redundancy
in favor of a single column.
