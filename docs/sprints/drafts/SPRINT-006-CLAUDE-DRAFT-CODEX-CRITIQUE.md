# Critique of `SPRINT-006-CLAUDE-DRAFT.md` (Codex)

## What Claude Got Right

Claude's draft is strong where this sprint most needs strength: it
keeps `audit-architecture` inside the established `audit-*` family
instead of inventing a one-off workflow. The five phases are clear, the
artifact paths are concrete, and the Phase 2 / Phase 3 / Phase 4
handoffs are specified tightly enough that an implementation agent could
reasonably build the command without guessing.

It also handles the core architecture-review problem well: subjectivity.
The requirement that each finding cite a named
`Pattern/Principle` or explicit trade-off, plus a concrete
`Alternative`, is the right mitigation against architecture critique
turning into taste-based commentary. The draft also makes a good call on
warn-and-continue behavior for flat or unusual repos. That matches the
intent: every repo has architecture, even if the architecture is weak or
informal.

A few additional strengths are worth calling out:

- It clearly supports both general software repositories and this
  agent-config repo shape.
- It preserves the dual-agent independence and devil's advocate pass
  that made `audit-security` useful.
- It treats migration cost as first-class, which is especially important
  for architecture work where the best technical answer is often not the
  best sprint answer.
- It anticipates edge cases such as single-reviewer fallback,
  no-findings output, and grouped findings for repeated patterns.

Overall, this is a thoughtful and mostly execution-ready draft.

## What Claude Missed

### 1. The schema drifts more than the draft acknowledges

The intent and recent sprint context establish a family pattern of
extending the base schema from `audit-security`. Claude's proposal adds
the right architecture-specific metadata, but it also effectively
replaces `Recommended Fix` with `Alternative` rather than clearly
preserving the base columns and extending them.

That may be the right design choice, but the draft does not explicitly
reconcile it with the stated family convention. This matters because the
rest of the audit family is converging on "core columns plus extension
columns," while this draft reads more like "architecture gets a new
table." If that is intentional, it should be defended as a family-level
design decision rather than introduced implicitly.

### 2. Generated, vendored, and dependency code are not bounded clearly enough

The design and accessibility drafts explicitly describe excluding
generated output and third-party UI code during orientation. This draft
does not offer equivalent boundaries for architecture review.

That omission matters more here than it first appears. An architecture
audit that freely scans vendored packages, generated output, lockfiles,
or framework build artifacts will produce noisy coupling and structure
findings that do not reflect the team's actual design decisions. The
command needs a clearer statement of what counts as in-scope repository
architecture versus incidental repository contents.

### 3. Multi-path scope handling is mentioned but not carried through operationally

Claude says the command supports multiple paths and should validate
them, which is good. But the rest of the draft mostly collapses back to
a singular `[scope]` concept in prompts, titles, ledger entries, and
final sprint wording.

That leaves real ambiguity in implementation:

- How should multiple resolved paths be represented in the review
  prompts?
- How should they appear in the sprint title?
- What string should be passed to `/ledger add`?
- Should synthesis merge findings across disjoint paths or preserve path
  grouping?

This is not a fatal flaw, but it is an underspecified edge case the
draft claims to support.

### 4. The evidence discipline is stronger for findings than for repository discovery

The draft rightly insists that findings be anchored to principles and
alternatives, but it is lighter on how the command should build its
architectural picture in Phase 1. It mentions `git log`, module
boundaries, entry points, and dependency graph review, but it does not
say how much evidence is enough before agents start making claims about
coupling, layering, or extensibility.

In practice, architecture reviews are sensitive to shallow reads. If the
command does not emphasize repository-specific evidence gathering before
judgment, reviewers may anchor too hard on top-level directory shape or
file names rather than actual change boundaries and flow.

## What I Would Do Differently

### 1. Preserve the family core schema more explicitly

I would keep the `audit-security` core columns visibly intact and add
architecture metadata around them. If `Alternative` truly replaces
`Recommended Fix`, I would say so directly and explain why architecture
needs that wording shift. Otherwise, I would keep both the familiar core
contract and the new metadata:

```markdown
| ID | Severity | Title | Location | Pattern/Principle | Why It Matters | Alternative | Migration Cost | Recommended Fix | Evidence/Notes |
```

That is a cleaner continuation of the schema-extension rule introduced
in the recent audit-family work.

### 2. Add explicit scope exclusions for architecture review

I would mirror the discipline used in the design/accessibility drafts:
exclude generated output, vendored code, package manager artifacts, and
other non-owned structure by default unless the user scopes into them
deliberately. That would keep the review focused on architectural
choices the team can actually change.

### 3. Tighten the Phase 1 discovery contract

I would make Phase 1 more explicit about the minimum discovery work
before findings are allowed. For example:

- identify owned entry points and major boundaries
- identify dependency direction or import hotspots where possible
- inspect the relevant config and orchestration files
- sample representative modules before generalizing a pattern

That would make the later findings more trustworthy without changing the
overall workflow.

### 4. Define multi-path output behavior once

I would add one small rule for multi-path scopes and reuse it
everywhere: how the resolved scope list is serialized for prompts,
displayed in sprint titles, and summarized in the ledger. A compact
convention such as a comma-separated normalized scope string or a shared
"multiple paths" label with details in the body would remove avoidable
implementation ambiguity.

## Over-Engineering and Gaps

### Potential over-engineering

1. `docs/architecture/README.md` looks optional at best. At this stage,
   the command file itself is probably enough to define naming and
   schema conventions. Adding a directory README before there is a
   broader architecture-artifact ecosystem feels heavier than necessary.

2. The review prompt categories are detailed and generally useful, but
   they are drifting toward embedded architecture guidance rather than a
   durable command spec. Some of that detail is valuable; too much of it
   increases maintenance burden every time the audit family evolves.

3. Requiring every finding to name both a principle and an alternative
   is directionally right, but architecture principles can overlap
   heavily. Without care, reviewers may spend effort "labeling" findings
   with principle names that add little real clarity. The command should
   prefer concrete trade-off language when principle labels are forced or
   redundant.

### Important gaps

1. The draft should reconcile its schema with the audit-family "base
   schema plus extensions" rule more explicitly.

2. It should define default exclusions so architecture review does not
   get polluted by generated or third-party code.

3. It should carry multi-path scope support through titles, prompts,
   synthesis behavior, and ledger registration rather than only
   mentioning it in Phase 1.

4. It should strengthen the repository-discovery expectations in Phase 1
   so the evidence discipline applies to the audit process, not just the
   final table rows.

## Overall Assessment

Claude's draft is good and close to shippable. Its biggest strengths are
family consistency, seriousness about subjectivity control, and a strong
focus on actionable alternatives rather than abstract critique. The main
issues are not conceptual mistakes so much as contract-level
underspecification: schema continuity, scope boundaries, and the exact
behavior of multi-path audits.

With a tighter statement of schema inheritance, clearer in-scope /
out-of-scope rules, and more explicit multi-path and discovery
behavior, this would be a solid basis for the final Sprint 006 merge.
