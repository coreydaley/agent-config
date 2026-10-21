# PR Artifacts

Shared layout and schema for the `pr-*` skill family (`/pr-plan`,
`/pr-build`, `/pr-review`, `/pr-fix`, `/pr-polish`). One directory per
piece of work, keyed on the branch, that every phase reads and appends
to. This file is the single definition. Skills cite it rather than
restating it.

## Directory

```
<reports-root>/<org>/<repo>/prs/<key>/
  PLAN.md               # pr-plan writes; pr-build and pr-fix append (Log, Follow-ups)
  source.md             # the ticket / issue / PR text the plan was made from (untrusted data)
  orient.md             # pr-plan's code-reading notes: file:line facts, prior art, dependencies
  plan-attack.md        # adversarial-reviewer pass on the plan (M+ ceremony only)
  archive/PLAN.<TS>.md  # prior plan versions when pr-plan re-runs on the same key
  pr-body.md            # pr-build's drafted PR title + body (the version that was opened)
  build-verify.log      # pr-build's full test / lint run
  verify.md             # pr-build's plan-delivery check (fresh subagent)
  sweep.md              # pr-build's hygiene sweep record (fresh subagent)
  reviews/<TS>/         # one subdir per /pr-review run (review-independent.md, review-adversarial.md,
                        #   canon-*.md with --canon, synthesis.md, devils-advocate.md, adjudication.md, REVIEW.md)
  fixes/<TS>/           # one subdir per /pr-fix run (TRIAGE.md, ADDRESSED.md, ...)
  polish/<TS>/          # one subdir per /pr-polish run (PROPOSALS.md, proposals.json, review-proposals.json)
  .walk-state.<skill>.json   # walker state per skill (plan, build, fix, polish); most recent run
```

`<reports-root>/<org>/<repo>` is `~/Reports/<org>/<repo>`, the same tree
the audit and feature skills write to. Resolve it, don't write it by
hand, so the org/repo derivation stays in one place:

```bash
PRS_BASE="$(python3 "$HOME/.claude/lib/paths.py" reports-base)/prs" || exit 1
PLAN_DIR="$PRS_BASE/$KEY"
```

`reports-base` already includes `<org>/<repo>`, derived from the source
repo's remote (preferring `upstream`, falling back to `origin`), so only
`prs/<key>/` gets appended. The `|| exit 1` is required: skill bash runs
under `set +u`, so an unset variable would expand to empty and relocate
the whole directory to the filesystem root.

## Key

The key is the branch name with `/` replaced by `-`. The branch exists
before the PR does, so it's the stable identity across the whole
lifecycle. `/pr-review` in external mode (someone else's PR, no branch of
ours) uses `pr-<N>` instead.

Examples:

| Branch | Key |
|---|---|
| `fix/gh-2479-tmp-budget` | `fix-gh-2479-tmp-budget` |
| `feat/syncer-skip-tag-pushes` | `feat-syncer-skip-tag-pushes` |
| (external PR 57169) | `pr-57169` |

Branch naming when `/pr-plan` runs on the default branch and has to
propose one. `<type>` is the Conventional Commits type the work will
mostly land as (`feat`, `fix`, `refactor`, `docs`, `chore`, `test`,
`perf`, `ci`):

- GitHub issue source: `<type>/gh-<N>-<slug>`.
- PR source: the PR's `headRefName`.
- Free text or a markdown file: `<type>/<slug>`, flagged as proposed so
  the user can rename it during discussion.

Never put a feature (parent) issue number in a branch name. The
implementation issue's number, or nothing.

## PLAN.md schema

```markdown
# Plan: <title>

| | |
|---|---|
| Status | draft \| approved \| no-build \| building \| in-review \| merged |
| Source | <org>/<repo>#N (<url>) \| <pr url> \| <file path> \| free text |
| Repo | <org>/<repo> |
| Branch | <branch> (proposed) |
| Base | <default branch> @ <sha> |
| Size | XS \| S \| M \| L \| XL (<measured: issue `size/*` label \| assumed>) |
| Ceremony | none \| attack \| design-review |
| Planned | <YYYY-MM-DD> |

## Problem
One paragraph. What's wrong or missing and why it matters, in our
words, derived from the source. Not a paste of the ticket.

## Value
Expected steady-state impact, with a provenance label on every number
(measured / code-derived / assumed). If the honest answer is "about
zero", say so here. This section is the build/no-build evidence.

## Scope
### In
- Bullet per deliverable. Each traces to the source's acceptance
  criteria or to an explicit decision recorded in Log.
### Out
- Bullet per thing the source mentions or the code reading surfaced
  that this PR will not do, with a one-clause reason. Adjacent
  improvements go here by default.

## Approach
How, as checkable assertions. Every mechanism claim that depends on a
dependency's behavior (caching, retries, coherence, ordering) cites
the dependency's implementation at file:line, not the call site.

## Tasks
1. **<task name>**: what this step delivers. Files: `a.go`, `a_test.go`.
   Proves: TestFoo_Bar.
2. **<task name>**: ... Files: ... Proves: ...

Ordered so each task leaves the tree building and its tests green.
One task becomes one commit in /pr-build. Foundations (types, config,
shared helpers) before callers, tests in the same task as the code
they prove.

## Files
| File | Change |
|---|---|
| path/to/file.go | what changes, one clause |

## Tests
| Test | Level | Proves |
|---|---|---|
| TestFoo_Bar | unit \| integration \| e2e | the specific claim it verifies |

Include negative cases. A test that only certifies the happy path
doesn't prove the approach.

## Risks
- What could go wrong in prod or in review, and the mitigation or
  the reason we accept it.

## Open questions
- Things that need the user's answer. Resolved ones move to Log.

## Follow-ups
- Appended by /pr-fix: findings deferred as out of scope, one line
  each with the reason. This is the only place deferrals live. The
  family never creates or edits GitHub issues; filing a follow-up is
  the user's call (`/issue-create`).

## Log
- <YYYY-MM-DD> planned (size S, ceremony none)
- <YYYY-MM-DD> approved
- <YYYY-MM-DD> pr-build: opened #<N> as draft
- <YYYY-MM-DD> pr-fix: review round 1, 3 fixed, 2 deferred, 1 won't-fix
```

Rules for the file:

- **Reads clean.** When a plan changes, rewrite the affected sections
  as if written fresh. No "(revised)" markers, no strikethrough. The
  Log carries the narrative, the archive carries the old versions.
- **Status is set by the skill that owns the transition.** pr-plan
  sets draft / approved / no-build. pr-build sets building, then
  in-review when the PR opens. pr-polish sets merged after the fact
  if it sees the PR merged.
- **Follow-ups and Log are append-only.** Other sections are rewritten
  in place.
- **Untrusted content stays in source.md.** PLAN.md is our words. If
  the ticket text needs quoting, quote briefly in Problem and point at
  source.md.

## PR body template

Used by `/pr-build` when opening the PR and by `/pr-polish` when
rewriting the body to match the final state. Rules for the prose are in
`lib/code-hygiene.md` (PR bodies section).

Title: a Conventional Commits subject, `<type>(<scope>): <summary>`,
imperative, lowercase, at most 72 characters. The issue number goes in
the Linked section, not the title.

```markdown
## Summary

Two to four sentences: the problem and the approach, condensed from
PLAN.md Problem and Approach. Mechanism claims keep their file:line
pointers when they help a reviewer verify.

## Changes

- One bullet per commit or per Files row, whichever reads better.

## Testing

- What was run and passed: the full-suite command, plus the specific
  tests from the Tests table that prove the change. Negative cases
  named explicitly.

## Not in this PR

- Scope Out items a reviewer will predictably ask about, ship-with
  gaps, and Follow-ups deferred during review, one clause of reason
  each. Omit the section when there's nothing worth saying.

## Linked

Closes #N   (a GitHub issue source; omit otherwise)
```

Leave out anything true of every PR. No "per discussion," no names, no
internal IDs, no local report paths, no feature (parent) issue numbers.

## How each skill uses it

| Skill | Reads | Writes |
|---|---|---|
| pr-plan | source, code | PLAN.md, source.md, orient.md, plan-attack.md |
| pr-build | PLAN.md (Tasks, Files, Tests, Scope, Approach, Open questions) | pr-body.md, build-verify.log, Log lines, Status |
| pr-review (own mode) | PLAN.md as the intent anchor | reviews/<TS>/ |
| pr-fix | PLAN.md Scope for triage, reviews/<TS>/REVIEW.md | fixes/<TS>/, Follow-ups, Log |
| pr-polish | PLAN.md (Follow-ups, Scope Out) for the final PR body | polish/<TS>/, Log, Status (merged) |
