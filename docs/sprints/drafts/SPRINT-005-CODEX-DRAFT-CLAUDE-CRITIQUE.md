# Claude's Critique of SPRINT-005-CODEX-DRAFT.md

## What Codex Got Right

1. **P0-C: Cross-Command Audit Behavior** — Codex added an explicit
   consistency task (P0-C) covering family-wide behavior: shared finding
   schema shape, domain-specific severity guidance, edge-case handling,
   sprint-output contract, and Codex exec prompt constraints. My draft
   embedded these in each command's task list implicitly. Codex's
   explicit P0-C is cleaner — it names the family-level concerns once,
   preventing them from being treated as per-command variation.

2. **Domain-specific severity anchors** — Codex's P0-C severity guidance
   is more precise than mine:
   - Design: "user impact, breadth, task interruption, consistency cost"
   - Accessibility: "exclusion severity, task blockage, assistive-tech
     impact, breadth of affected users"
   These are better grounding criteria than my "user impact and frequency
   of encounter." The accessibility anchor in particular is stronger:
   "exclusion severity" is the right frame for a11y severity.

3. **README as P1 explicitly in-scope** — Codex includes README updates
   as P1 in-scope (with a full task block, not just a mention). My draft
   did the same, but Codex also specifies invocation examples across
   Claude, Codex, and Gemini — a detail I missed that matters for this
   multi-agent repo.

4. **Structural discipline** — Codex kept the draft at planning-level
   abstraction (what the commands must do, not the full text of what they
   will say). This is appropriate for a sprint plan; my draft is a
   detailed spec that partially invades the implementation space.

## What Codex Got Wrong or Missed

1. **No finding schema definition** — Codex says "reuse the same core
   findings table shape" but never defines what that shape is for design
   and accessibility. The `audit-security` schema is:
   `| ID | Severity | Title | Location | Why It Matters | Recommended Fix | Evidence/Notes |`
   For `audit-design`, I proposed adding a `Heuristic` column.
   For `audit-accessibility`, I proposed adding `WCAG` and `Level` columns.
   These additions are the critical difference from the security schema —
   without them, the commands can't anchor their findings to standards.
   Codex completely omits this, saying only "same core table columns."
   This is a gap the merge must close.

2. **No-UI behavior is underspecified** — Codex mentions "explicit
   behavior for no-UI or minimal-UI scopes" in P0-A tasks but never
   specifies what that behavior is. Based on the interview, the answer
   is: warn and stop. Codex leaves this ambiguous.

3. **No inherent-limitations disclaimer** — `audit-security` includes
   an explicit inherent-limitations note: "static review cannot assess
   runtime exploitability." The equivalent for accessibility is critical:
   static code review cannot fully substitute for browser/screen reader
   testing. Codex omits this entirely. My draft includes it; the merge
   should keep it.

4. **Severity mapping to WCAG conformance levels is missing** —
   Codex says "require each accessibility finding to cite the relevant
   WCAG criterion" but doesn't document the severity → WCAG level
   mapping (Level A → Critical, AA → High, AAA → Medium, BP → Low).
   Without this, executing agents will make inconsistent severity calls.

5. **No docs/design/README.md or docs/accessibility/README.md** — Codex
   omits the directory README files that `audit-security` created via
   P1-B (`docs/security/README.md`). These serve as reference for future
   maintainers and include the naming convention and finding schema. The
   merge should include these as P1-B.

6. **No rollback / observability section** — My draft has both; Codex's
   does not. For a text-only sprint, rollback is trivial (git restore),
   but the section is part of the standard sprint template.

7. **Draft is a planning document, not an implementation spec** — This
   is both strength and weakness. Codex's draft is appropriately
   abstracted for a sprint plan. But because this sprint's "code" is
   Markdown command files, the sprint doc itself needs to specify enough
   detail that `/sprint-work` can write the commands correctly. Codex's
   level of abstraction will require the executing agent to make many
   unstated choices. My draft over-specifies but errs in the right direction
   for this type of deliverable.

## Choices I Would Defend Against Codex's Approach

1. **Explicit finding schema for each command** — The schema additions
   (`Heuristic`, `WCAG`, `Level`) are not over-engineering; they are the
   mechanism by which findings are anchored to standards rather than
   agent opinion. These must be in the sprint document.

2. **Warn-and-stop for no-UI projects** — Codex leaves this open.
   The interview confirmed: warn and stop. This should be explicit in
   the final sprint doc.

3. **Phase 5 task format specifying WCAG criterion** — For
   `audit-accessibility`, each P0 task must include the WCAG criterion
   ID and conformance level. Codex's draft doesn't specify this; my
   draft does.

## Merge Recommendations

- **Keep Codex's P0-C** as an explicit consistency task, but augment it
  with the finding schema specifications from my draft.
- **Use Codex's severity anchors** for both commands (they're better).
- **Keep my inherent-limitations note** and no-UI warn-and-stop behavior.
- **Keep my WCAG severity mapping** table in the accessibility command spec.
- **Keep Codex's README invocation examples** detail (multi-agent: Claude,
  Codex, Gemini).
- **Keep my P1-B directory READMEs** (they match the `audit-security`
  pattern).
- **Merge rollback/observability** from my draft.
