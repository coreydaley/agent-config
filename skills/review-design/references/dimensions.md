# Design review dimensions

The rubric both attackers apply and the synthesis grades against. Every
dimension asks a question about the design, not about the document that
describes it. A finding is a reason the design will not work, will cost
more than claimed, or is the wrong shape for the problem. Nothing else.

## Altitude guard: what is not a finding here

These belong to a document review (the presentation) or to code review
(the implementation), and the synthesis drops them:

- wording, structure, missing sections, missing diagrams, tone
- "the doc does not spell out implementation detail X"
- metric and label names, exact config values, env-var permutations
- exhaustive test enumerations, line-by-line acceptance criteria
- style, naming, formatting of anything

A doc gap becomes a design finding only when the gap hides a decision
the design depends on (see Sequencing and scope).

## Severity

| Severity | Meaning |
|---|---|
| Blocker | The design cannot work as stated, or a load-bearing mechanism claim is refuted by the code. Building it as designed produces a rewrite or an incident. |
| High | A failure mode, gap, or wrong number that would cause an incident, a rollback, or a materially different cost if unaddressed. Fixable inside the current shape. |
| Medium | A real gap with a contained fix. Does not change the build decision on its own. |
| Low | Worth recording, does not change the decision. |

No Nit. If it is a nit, it is presentation, and it is out of altitude.

## 1. Problem and value

- Is the problem real, and is there evidence (a measurement, an incident,
  an issue with numbers) rather than an assertion?
- Does the design solve the stated problem, or a neighboring easier one?
  Name the gap between the two if it exists.
- Is the value stated with provenance (measured, code-derived, assumed)?
  Does the pessimistic bound still justify the work? A business case sized
  on the optimistic bound is a finding.
- Is "do nothing" priced? What happens if the problem is left alone for a
  quarter?

## 2. Mechanism claims

The load-bearing dimension. For every claim that depends on a dependency's
behavior, open the dependency's implementation, not the call site, and
confirm or refute it with a `file:line`. Designs die here more than
anywhere else, and the fatal fact lives in the library more often than in
the caller.

Checklist of behaviors that are routinely assumed and rarely true:

- **Caching**: per-instance or shared? Keyed on what? TTL and invalidation?
  Does the layer below already cache (ETag, digest, index) so the new cache
  is redundant?
- **Retries**: what predicate decides a retry, which errors get absorbed
  before the caller sees them, and is the operation idempotent under retry?
- **Ordering and idempotency**: does the design assume delivery order,
  exactly-once, or a single writer that the substrate does not guarantee?
- **Coherence**: when two instances or two regions see different state,
  which one wins and does the design know?
- **Distribution**: which instance handles which work, and what happens
  when the assignment changes mid-operation?
- **Error classification**: does the code distinguish the errors the design
  treats differently (not-found vs unauthorized vs transient)?
- **Concurrency**: locks, races, double invocation, a cron overlapping its
  previous run.
- **Quotas, rate limits, and timeouts** at every external boundary.
- **Auth boundaries**: which identity performs each step, and does it hold
  the permission the design assumes?

Each claim ends in one of: `confirmed file:line`, `refuted file:line`, or
`unverifiable` (no code available, or the behavior is runtime-only). An
unverifiable claim is never counted as confirmed. When no codebase is
provided, every mechanism claim is unverifiable and the review says so.

## 3. Alternatives and prior art

- Is the obvious alternative named and rejected with a reason that holds?
  If the doc names no alternative, propose the obvious one and ask why not.
- Is there an existing primitive in the repo (a helper, flag, job, table,
  pattern) that already does this or most of it? Rebuilding one that does
  most of it is a High with the suggestion "reuse". One that already solves
  the whole problem is a Don't build.
- Buy vs build: does a dependency already in use provide this?
- Is there a smaller first step that captures most of the value and
  de-risks the rest? A design that goes straight to the full build when a
  meter or a flag would settle the key uncertainty first is a finding.

## 4. Failure modes and blast radius

Walk each component and each external dependency: down, slow, partitioned,
returning garbage, invoked twice, running on stale config. For each, what
does the design do, and is that acceptable?

- **Rollback**: can it be turned off without a deploy? Is there a flag, and
  who flips it?
- **Migration and compatibility**: dual-write windows, backfills, old
  readers against new writers, schema and wire-format changes, cross-team
  contracts. What breaks for a consumer that has not upgraded?
- **Partial rollout**: staging and prod usually mirror each other. Does the
  design land in both, and what happens in the window where they differ?
- **Data loss and corruption paths**: any step that deletes, overwrites, or
  reconciles needs a named safeguard.
- **Cost of the failure vs cost of the mitigation**. A mitigation more
  expensive than the failure it prevents is itself a finding.

## 5. Numbers

- Every number carries a provenance label: measured (with a date and a
  query), code-derived (with the multipliers shown), or assumed (as a range
  with the assumption named). An unlabeled number in a headline or a dollar
  claim is a finding.
- Divisor discipline: for any ratio, is the denominator stated, and does
  the plausible alternative denominator change the answer?
- Capacity and load projections show their multipliers. Check the
  arithmetic.
- The headline number matches the body. A summary that rounds up is a
  finding.
- Estimates run optimistic. When the design picks between two sizes or two
  rates, it should pick the worse one. Check whether it did.

## 6. Operability and verification

- How will anyone know it worked? Name the success signal and where it is
  read.
- How will anyone know it broke? An alert on a failure is weaker than an
  alert on the absence of success. Which does the design have?
- Dashboards, runbook, and ownership named? Steady-state cost stated?
- Is there a meter before the estimate is leaned on? Shipping the meter
  first is often the right first phase.

## 7. Sequencing and scope

- Are the load-bearing decisions made, or deferred with a hidden default?
  "We will decide X later" is fine when X is not on the critical path and a
  finding when it is.
- Does each phase leave the system working? Can the sequence pause between
  phases for a cycle without harm?
- Does scope-in cover the problem? Does scope-out hide a piece the design
  actually requires to function?
- Are cross-team contracts and owners named for anything that crosses a
  boundary?

## 8. Security and trust boundaries

Apply when the design touches auth, secrets, untrusted input, or
multi-tenant data. Otherwise record "not exercised".

- Where does untrusted data enter, and what validates it?
- Who can trigger each operation, and with which identity?
- Are secrets read at the right layer and never logged or persisted?
- Does a tenant boundary survive every code path, including the failure
  paths from dimension 4?

## Strengths

Also record what the design gets right, when it is load-bearing: a
mechanism claim confirmed against the code, an alternative correctly
rejected, a failure mode already handled, a number with honest provenance.
Two to five items. Praise for prose is out of altitude.
