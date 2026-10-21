# PR Discipline

The working rules the `pr-*` family and `/review-design` apply on top of
the global `CLAUDE.md`. Skills cite the section by name rather than
restating it.

## Read the Dependency First

Before proposing a design whose safety or value depends on a
dependency's caching, retry, distribution, ordering, or coherence
semantics, read that dependency's implementation, not just the call
site. The fatal fact lives in the library more often than in the caller.

Corollary: substantial designs get an adversarial pass (`/review-design`,
or an `adversarial-reviewer` with read access to the dependencies)
*before* building, with explicit instructions to attack the mechanism
claims. A design killed on paper costs one review; killed in PR review
it costs a build; killed in prod it costs an incident. State mechanism
claims as checkable assertions with file:line pointers so the attacker
has something concrete to refute.

## Estimates: Provenance, Divisors, Pessimistic Bounds

Estimates run optimistic. Three rules:

1. **Every number carries a provenance label**: *measured* (a query or
   benchmark, dated), *code-derived* (a formula with the multipliers
   shown), or *assumed*. Only measured numbers go in headlines; assumed
   numbers appear as ranges with the assumption named.
2. **Divisor discipline**: a ratio states its denominator and computes
   the plausible alternative before publishing.
3. **Size the case on the pessimistic bound.** Upside is a pleasant
   surprise; a walked-back headline costs credibility.

Ship the meter that would correct an estimate *before* leaning on the
estimate.

## Sizing

| Size | Effort (build + test + review + docs) |
|---|---|
| XS | < 4 hours |
| S | 1 day |
| M | 2–3 days |
| L | 1 week |
| XL | 2 weeks or more |

A `size/*` label on the source issue is *measured*; anything else is
*assumed*. When torn between two sizes, pick the larger.

## Scope Discipline

Reviews find things. That's their job. They don't know what's in scope.
The orchestrator is the scope cop, not the reviewers and not the skills.

- **Default to defer, not fix.** The first question about a finding is
  "is this in scope for THIS PR?", not "what severity is it?"
- **Severity is not scope.** Blocker / High / Medium / Low / Nit is
  importance. Whether to fix it here is a separate axis. Surface both.
- **Read the scope out loud before triage.** State what's in and out,
  and reference it when classifying findings.
- **Three heuristics:**
  1. A regression this PR introduced → fix.
  2. Pre-existing debt the PR doesn't touch directly → defer.
  3. An improvement adjacent to the diff but not required for the
     stated goal → defer.

  A PR that brings a new thing to parity with an existing one inherits
  the existing one's gaps. Fixing those gaps in the same PR is scope
  creep, even when the fixes are correct.
- **Watch diff growth across rounds.** A PR that doubles between review
  rounds gets a scope check. The healthy pattern is feat → maybe one
  chore → merge.
- **Watch for self-reinforcing loops.** If round N+1's findings are
  mostly in code round N added, the problem is the additions.
- **Neutral framing.** "Fix or defer?", not "fix everything / fix
  priority / nothing". Never bundle actions into one option and treat
  approval of the bundle as approval of each part, especially external
  writes.
- **Draft first for anything outbound.** "Draft", "write up", "put
  together" mean show me. The only authorization to post a GitHub
  comment, review, or reply is an explicit "post it" after the draft
  has been seen, or a standing instruction in the task itself. A PR body
  is outbound prose too: settle it in chat, then post once.
- **Posted is immutable.** Correct a posted comment or reply forward, in
  the next one, not in place. PR descriptions are the exception; they
  are living documents.
- **Facts about the system, not the author.** No "the instance I built";
  name systems and issues, not people, in either direction.
- **When told to do less, do less immediately.** Stop, ask, narrow.
- **A purpose or compatibility claim is a technical assertion.** "The
  follow-up consumes this API" needs the consumer sketched first. When a
  design pivots, re-derive what survives instead of rewording artifacts
  to keep shipped code sounding relevant.
- **Reviewer output is biased long.** Independent reviews, synthesis,
  and devil's advocate each add items. Treat the result as a candidate
  list, not a fix list.

## Show the Artifact Before Any Question Dialog

Only a turn's final text message is reliably shown. Never put
deliverable content (findings, drafts, reports, review output) between
tool calls or in front of AskUserQuestion. When a workflow shows an
artifact and then asks what's next, end the turn with the artifact plus
a plain-text question and let the user answer in their own words. If the
user says they never saw the content, re-emit it in full as a final
message.

## PR Pre-Review Procedure

Never ask for human review right after opening a PR. The order is
fixed:

1. Sweep the diff for comment noise (`lib/code-hygiene.md` Comments).
2. Sweep the tests for assertions that prove nothing
   (`lib/code-hygiene.md` Tests).
3. Run `/pr-review` and address its findings with `/pr-fix`.

Only then does the user mark the PR ready and request reviewers. Fixups
before human review squash into their original commits; after the first
human comment, history is append-only.

## Verification Ceremony Scales With Stakes

The multi-role review machinery (independent ∥ adversarial reviewers,
synthesis, devil's advocate, adjudication) is for decisions where being
wrong is expensive: designs, changes with wide blast radius, claims of
large impact. An XS fix with a bounded blast radius gets one review
pass, at the end (`/pr-review`), not a pre-build pass plus a post-build
pass.

The build/no-build value gate applies to everything, including quick
fixes: if the expected steady-state impact is about zero, say so before
code is written and let the user decide whether to spend the time.

Findings carry their impact label when they're surfaced. A bug raised
mid-investigation without "expected frequency about zero, unrelated to
the current problem" borrows relevance it doesn't have.

## Fresh Eyes for Review Judgments

An agent that wrote the code doesn't grade it. Every judgment step runs
in a fresh role subagent per `lib/agent-roles.md`. The same rule applies
outside the skills: when the next step is to judge something just
written in this context, spawn a fresh reviewer.
