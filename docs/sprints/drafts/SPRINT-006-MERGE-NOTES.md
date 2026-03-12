# Sprint 006 Merge Notes

## Claude Draft Strengths

- Correct warn-and-continue behavior for unusual/flat repos
- Strong evidence discipline: named principle + concrete alternative = mandatory
- Explicit evidence discipline instruction placed in the Phase 2 prompt body (not just principles section)
- Synthesis document template with explicit `## Scope`, `## Summary`, `## Unified Findings`,
  `## Rejected Devil's Advocate Challenges` sections
- Explicit no-findings task template matching `audit-security` pattern
- Migration cost note in user handoff before `/sprint-work`
- `docs/architecture/README.md` as P1-B (family consistency with SPRINT-004/005)

## Claude Draft Weaknesses (from Codex critique)

- Schema drift: `Alternative` effectively replaces `Recommended Fix` without explicitly
  reconciling with the family "core + extension" convention
- Missing scope exclusions for generated/vendored/dependency code
- Multi-path support mentioned in Phase 1 but not carried through to prompts, sprint
  titles, and ledger registration
- Phase 1 discovery contract too thin: doesn't specify minimum evidence-gathering
  before findings are allowed

## Codex Draft Strengths

- Opening Guiding Principles section grounds the command before implementation detail
- Explicit Out of Scope section (cleaner than my Deferred section)
- Concrete schema example row showing exactly what a DRY finding looks like
- Verification Plan as a separate numbered section (easier to follow during execution)
- P0 split into A/B/C sub-tasks for incremental progress tracking on a single file
- `prompts/` and `scripts/` directories added to agent-config coverage
- Explicit Assumptions section

## Codex Draft Weaknesses (from Claude critique)

- Schema redundancy: `Alternative` and `Recommended Fix` both present — architecture
  findings need both (alternative = the better structural design;
  recommended fix = the concrete implementation step); but Codex treats them as near-synonyms
- Missing `docs/architecture/README.md` as P1-B (breaks family consistency)
- Evidence discipline is in principles but not in the Phase 2 Codex exec prompt body
- No explicit synthesis document template
- No-findings case only in acceptance criteria, not in Phase 5 instructions

## Valid Critiques Accepted

1. **Schema reconciliation with family convention** (Codex critique of Claude): schema
   is now declared as "core audit columns + architecture extension columns." `Recommended Fix`
   is retained from the core. `Pattern/Principle`, `Alternative`, and `Migration Cost`
   are the extension. `Alternative` and `Recommended Fix` serve different purposes:
   Alternative = the better structural design to move toward; Recommended Fix = concrete
   implementation step. Both stay.

2. **Scope exclusions** (Codex critique of Claude): added explicit exclusions for
   generated output (`build/`, `dist/`, lockfiles), vendored/dependency code, and
   binary assets — mirroring `audit-design`/`audit-accessibility` pattern.

3. **Multi-path scope carried through** (Codex critique of Claude): added a compact
   convention — multiple resolved paths joined with `, ` in sprint title and ledger entry.
   Phase 2 prompt receives the full list of resolved paths. Synthesis merges across paths
   unless scope grouping is materially relevant to a finding.

4. **Phase 1 discovery contract strengthened** (Codex critique of Claude): added minimum
   discovery steps — identify owned entry points and boundaries; inspect import hotspots;
   sample representative modules before generalizing a pattern.

5. **Guiding Principles section** (from Codex draft): adopted as opening framing.

6. **Out of Scope section** (from Codex draft): adopted explicitly.

7. **P0 sub-task structure** (from Codex draft): A/B/C sub-tasks for better tracking.

8. **Verification Plan** (from Codex draft): adopted as a separate section.

9. **Concrete schema example row** (from Codex draft): added to the merged draft.

10. **`prompts/` and `scripts/` in agent-config coverage** (from Codex draft): added.

## Critiques Rejected (with reasoning)

1. **"`docs/architecture/README.md` is optional at best"** (Codex over-engineering claim):
   Rejected. SPRINT-004 shipped `docs/security/README.md`; SPRINT-005 shipped
   `docs/design/README.md` and `docs/accessibility/README.md`. Omitting
   `docs/architecture/README.md` breaks family consistency. The cost is one small file.

2. **"Requiring both a principle and an alternative may cause labeling busywork"**
   (Codex over-engineering claim): Partially accepted as nuance. The merged draft's
   instruction allows "trade-off language when principle labels are redundant" rather than
   requiring a formal principle taxonomy. But the requirement for a named principle or
   observable trade-off is retained — that's the key evidence discipline guard.

## Interview Refinements Applied

- Warn-and-continue (not stop) for unusual/flat repos: confirmed
- Opinion-only findings without named principle: skip entirely (not allowed at any severity)
- Migration Cost as a schema column (not buried in task body): confirmed

## Final Decisions

- Sprint number: 006
- Command file: `commands/audit-architecture.md`
- Artifact directory: `docs/architecture/`
- Finding schema: core audit-security columns + `Pattern/Principle` + `Alternative` +
  `Migration Cost` extension
- Schema column order:
  `| ID | Severity | Title | Location | Pattern/Principle | Why It Matters | Alternative | Migration Cost | Recommended Fix | Evidence/Notes |`
- P0 split into P0-A (command authoring), P0-B (synthesis + devil's advocate behavior),
  P0-C (sprint output contract)
- P1-A: README.md update; P1-B: `docs/architecture/README.md`
- Simplest viable filter: no new execution infrastructure, no ADR workflow, no scoring
  system; one file does the job
- Sprint sizing: single file creation + one P1 README update = well within one sprint
