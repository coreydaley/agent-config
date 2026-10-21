# Report format and artifacts

## Session directory

```
<reports-base>/designs/<slug>/<TS>/
  subject.md              the design as reviewed, rendered to markdown (untrusted data)
  context.md              source pointer, repo paths, scope, settled decisions, focus
  claims.md               claim ledger (verifier)
  review-independent.md   independent-reviewer findings, IDs IR
  review-adversarial.md   adversarial-reviewer findings, IDs AR
  synthesis.md            merged and calibrated findings, IDs DR (synthesizer), edited in place by the adjudicator
  defense.md              the defender's case for the design
  REVIEW.md               the deliverable
  .walk-state.review-design.json   walker state, the crash marker for --resume
```

`<reports-base>` is what `lib/paths.py` returns for the primary repo,
which is the first codebase path the user listed. With no codebase it
resolves against the current checkout; if that isn't a git checkout,
ask which repo the design belongs to:

```bash
BASE=$(python3 "$HOME/.claude/lib/paths.py" reports-base -C "$REPO") || exit 1
# or, with no codebase, from the current checkout:
BASE=$(python3 "$HOME/.claude/lib/paths.py" reports-base) || exit 1
TS=$(date +%Y%m%d-%H%M%S)
SESSION_DIR="$BASE/designs/$SLUG/$TS"
mkdir -p "$SESSION_DIR"
```

`<slug>` is a short kebab-case name for the design, stable across
re-runs so the runs stack under one directory and the newest prior
`REVIEW.md` is the comparison baseline. For a `PLAN.md` from `/pr-plan`,
the slug is the plan's key. For a GitHub issue, `issue-<N>`.

## context.md

```markdown
# Context

- Source: <absolute path | GitHub issue <org>/<repo>#N | pasted text>
- Grounded against: <absolute repo paths, one per line> | none
- Extra grounding: <orient.md path, prior design, data files> | none
- Scope: <one sentence: in, and explicitly out>
- Settled: <accepted risks and follow-ups carried from prior triage, one per line> | none
- Focus: <question> | none
- Prior run: <absolute path to the previous REVIEW.md> | none
```

## Verdict scale

| Verdict | Meaning |
|---|---|
| Build | No Blocker or High open. Load-bearing mechanism claims confirmed against the code. The design is the right shape for the problem. |
| Build with changes | No Blocker. High or Medium findings with a clear fix inside the current shape. Name the changes. |
| Rework | A Blocker that needs a different approach, or a load-bearing mechanism claim refuted. The problem is still worth solving. |
| Don't build | The problem is not real, the value on the pessimistic bound is about zero, an existing primitive already solves it, or the design cannot work and no rework is apparent. |

An ungrounded run (no codebase) cannot return Build. Every mechanism
claim is unverifiable, and the verdict line carries "(ungrounded)".

## REVIEW.md

Sections in this order. Omit a section rather than padding it. Plain,
direct prose. The orchestrator formats this from `synthesis.md` and
changes none of its judgments.

```markdown
# Design Review: <title>

| | |
|---|---|
| Source | <as in context.md> |
| Grounded against | <repo paths> | none (ungrounded) |
| Scope | <sentence> |
| Settled | <count> items carried from prior triage | none |
| Reviewers | independent-reviewer and adversarial-reviewer (Fable) |
| Defense | <ledger line> | not run (no findings) | failed (<why>) |
| Reviewed | <YYYY-MM-DD> |
| Prior run | <relative path> | none |

## Verdict

**<Build | Build with changes | Rework | Don't build><, ungrounded>**

<2-4 sentences from the synthesis: the load-bearing finding, the single
change that most improves the design, the answer to the focus question if
one was given.>

## Claim ledger

| # | Claim | Kind | Status | Evidence | Checked by |
|---|---|---|---|---|---|

<Status: confirmed, refuted, unverifiable, untested. Checked by: both,
independent, adversarial, synthesis, or nobody. A load-bearing claim
marked untested or unverifiable is a finding below, not a footnote here.>

## Findings

| ID | Severity | Dimension | Claim # | Finding | Evidence | Suggestion | Sources |
|---|---|---|---|---|---|---|---|

<Most material first. Sources lists the IR and AR IDs, or "claim ledger"
for a finding the synthesis raised from an untested load-bearing claim.
Suggestion is the smallest design change that resolves it, or "rework".>

## What the design gets right

<Two to five load-bearing strengths with evidence. A confirmed mechanism
claim counts. Prose quality does not.>

## Since last run

<Only when a prior run exists. Three short lists: resolved, still open
(with the prior ID), new.>

## Reviewer disagreements

<Only when material: a severity two steps apart, or a claim one reviewer
confirmed and the other refuted. What each said and the call made.>

## Removed in defense

<Findings the defense pass killed, each with the verified evidence. This
is the audit trail. Omit when the defense removed nothing and say so in
the Defense line of the header instead.>

## Out of altitude

<One line per presentation-level item the reviewers raised and the
synthesis set aside, so nothing is lost. These are for whoever edits the
document.>
```

## Lifecycle: re-running and convergence

The report is a snapshot. After a run, triage each finding in the design
itself:

- **Address**: change the design. The finding is resolved next run.
- **Accept**: record it in the design as an accepted risk with a one-line
  why. Carry it into `Settled` on the next run.
- **Defer**: record it in the design as a follow-up. Carry it into
  `Settled` on the next run. Filing it as an issue is the user's call
  via `/issue-create`.

Acceptance is explicit and recorded in the design, never inferred from a
finding merely staying in the list. Convergence is Blockers at zero, Highs
resolved or accepted with a reason, the claim ledger free of `refuted` and
load-bearing `untested` rows, and the verdict at Build or Build with
changes.

## Hand-offs after the report

- **Build** or **Build with changes**: the design is ready for `/pr-plan`,
  which will read it as a source and size the work.
- Any verdict: presentation items sit in Out of altitude for whoever
  edits the document. This skill never writes into the design or the
  issue it came from.
