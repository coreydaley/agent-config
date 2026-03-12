# Critique of `SPRINT-005-CLAUDE-DRAFT.md` (Codex)

## What Claude Got Right

Claude's draft is strong on command-level specificity. It does not just
say "add two new audit commands"; it spells out the actual five-phase
workflow, the artifact paths, the expected prompts, and the output
contract for both commands. That makes the sprint much closer to
execution-ready than a higher-level planning document would be.

It also makes several good product decisions:

- It keeps `audit-design` and `audit-accessibility` aligned with the
  proven `audit-security` workflow instead of inventing a second audit
  architecture.
- It separates artifact directories by domain (`docs/design/` and
  `docs/accessibility/`), which matches the sprint intent and avoids
  mixing unlike findings.
- It gives accessibility findings explicit standards context via WCAG
  criterion and level columns, which improves remediation quality.
- It handles edge cases intentionally, especially no-frontend scopes,
  no-findings output, and single-agent fallback during synthesis.
- It includes useful operational safeguards such as validating scope
  before using it in `codex exec` prompts and keeping prompts
  self-contained.

In short, Claude's draft is thoughtful, concrete, and clearly informed
by the lessons from `audit-security`.

## What Claude Missed

### 1. It conflicts with the stated success criterion about schema reuse

The sprint intent says both new commands should share the same finding
schema as `audit-security`. Claude instead introduces two new variants:

- `audit-design` adds a `Heuristic` column
- `audit-accessibility` adds `WCAG` and `Level` columns

Those additions are sensible in isolation, but they are still a change
to the schema. That means the draft is quietly redefining a success
criterion rather than following it. If that change is desired, the
sprint should say so explicitly as a design decision, not smuggle it in
as an implementation detail.

### 2. It overstates what static review can reliably verify

The accessibility command is careful in a few places to note the limits
of static review, but the proposed review categories still include items
like screen reader support, focus restoration, live-region
announcements, and responsive/mobile behavior as if they can be audited
consistently from source alone. In practice, some of these can be
suspected from code patterns, but not validated confidently without
runtime testing.

The issue is not that these categories are wrong; it is that the draft
does not separate:

- code-inspectable findings
- runtime-likely findings
- verification steps that require a browser or assistive technology

Without that distinction, the audit risks producing authoritative-sounding
findings from incomplete evidence.

### 3. The design audit standards are too loosely bounded

For accessibility, Claude uses WCAG as a clear normative reference. For
design, it mixes Nielsen heuristics, Material Design, Apple HIG, and
project-specific design system rules. That gives flexibility, but it
also makes findings harder to calibrate consistently. The same UI issue
could be framed as a heuristic violation, a platform mismatch, or a
local design-system inconsistency depending on reviewer preference.

This is manageable, but the draft does not define an order of
precedence. Without one, the design audit could drift toward opinionated
critique instead of stable review criteria.

### 4. README and supporting docs are underspecified relative to the new surface area

Claude includes README updates and optional per-directory READMEs, which
is directionally right, but the draft does not say what existing README
section should be updated or how command discoverability should stay
consistent with the rest of the repo. That is a smaller issue than the
command content, but once two new top-level commands land, the
documentation burden is real.

## What I Would Do Differently

### 1. Keep one core schema and add domain metadata in a controlled way

I would preserve the core `audit-security` columns unchanged and add
domain-specific references in one consistent extension field, or in a
clearly declared optional metadata column strategy shared by all
`audit-*` commands. That keeps the family coherent and avoids each new
audit inventing a custom table shape.

If the repo wants richer schemas per audit type, I would make that a
deliberate family-level decision and update the success criteria
accordingly.

### 2. Separate "can be found in code" from "must be tested in runtime"

For `audit-accessibility`, I would explicitly label findings or task
output with a verification mode:

- static code review
- browser/manual verification
- assistive technology verification

That would make the sprint output more honest and more useful. It keeps
the command from over-claiming certainty while still surfacing likely
issues.

### 3. Narrow the design audit to a more stable rubric

I would anchor `audit-design` primarily to:

- project design-system adherence, if present
- information hierarchy and interaction clarity
- consistency across repeated UI patterns
- responsive/layout integrity

Then I would treat Nielsen or platform guidelines as secondary support,
not co-equal authorities. That makes design findings less subjective and
more actionable for a sprint.

### 4. Reduce duplication between the two command specs

Claude repeats a lot of the same workflow and acceptance language twice.
I would keep the commands self-contained, but tighten the sprint by
stating one shared audit-family contract and then documenting only the
domain-specific differences for design vs. accessibility. That would
make the sprint easier to maintain and easier for an implementation
agent to scan.

## Over-Engineering and Gaps

### Potential over-engineering

1. The design and accessibility schemas may be too customized too soon.
   For the second and third commands in a new family, simpler alignment
   with `audit-security` is probably safer unless there is a strong need
   for schema divergence.

2. The P1 proposal to add both `docs/design/README.md` and
   `docs/accessibility/README.md` may be heavier than necessary. The
   naming rules and artifact conventions could likely live in the
   command files unless these directories are expected to become
   long-lived surfaces with multiple producers.

3. The draft is very detailed about review categories, which is mostly a
   strength, but parts of it start to read like embedded standards
   documentation. That increases maintenance cost if the command text is
   supposed to remain concise and durable.

### Important gaps

1. The draft should explicitly reconcile its schema changes with the
   sprint intent's "same finding schema as `audit-security`" requirement.

2. The accessibility workflow should more clearly distinguish suspected
   issues from runtime-verified failures.

3. The design workflow should define how to prioritize project-local
   design conventions versus external heuristics when they disagree.

4. The draft should be clearer about multi-path scope handling. The
   intent lists it as an edge case, but Claude's command text mainly
   discusses a single resolved scope path rather than multiple validated
   paths carried through the workflow.

## Overall Assessment

Claude's draft is strong and substantially execution-ready. Its biggest
strength is that it specifies real command behavior instead of leaving
future agents to infer the workflow. The main weaknesses are not lack of
detail, but a few places where the draft quietly broadens scope or
redefines the contract: custom schemas, ambitious static accessibility
coverage, and a somewhat loose design-review standard.

With a tighter schema strategy, clearer runtime-vs-static boundaries,
and a more constrained design rubric, this would be a very solid basis
for the final Sprint 005 merge.
