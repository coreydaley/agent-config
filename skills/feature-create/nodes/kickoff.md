# Node: kickoff

Open the session, get the feature on the table, and **detect/confirm its size**
(small vs large) — that sets how deep the discussion and the issue body go, and
whether the independent readiness check runs.

## Inputs

- `org_repo`, `seed_idea`, `orient_summary` from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
SEED_IDEA=$(scripts/walk.sh get --state "$STATE" --key seed_idea)
ORIENT_SUMMARY=$(scripts/walk.sh get --state "$STATE" --key orient_summary)
```

## Steps

Compose a tight opening — no preamble, no "Great, let's get started."

If a `seed_idea` was passed, **restate it** as your read and start there; if not,
ask for the feature:

> "Let's capture a feature for **<org/repo>** as a tracked issue.
> [If seed_idea: 'You're thinking: <restate seed_idea in your own words>. Let me
> make sure I've got it —' / else: 'What's the feature? A sentence or two on what
> it does and why it's worth building.']"

After the user describes it (or confirms your restatement), **gauge the size**
and confirm:

- **Small** — a self-contained change, low uncertainty. The issue body is just
  **intent + acceptance criteria**, and it files without a readiness check.
- **Large / epic** — meaningful scope, multiple subsystems, real unknowns. The
  body covers the engineering-surface dimensions (requirements + AC, edge cases &
  error states, constraints, dependencies & assumptions, feasibility,
  scope-creep, open questions), and it gets an independent readiness check before
  filing.

Detect a likely tier from the description, then confirm in one line:

> "This reads like a **<small | large>** one — [why]. So I'll keep it to
> [intent + acceptance criteria | the full engineering surface]. Sound right, or
> is it bigger/smaller than that?"

Persist the agreed size:

```bash
scripts/walk.sh set --state "$STATE" --key feature_size --value "<small|large>"
```

## What we DO and DON'T cover

This skill captures the **engineering surface** of a feature — what it must do
and how we'll know it's done. It does **not** plan the work (tasks, breakdown,
DoD); that's `/feature-plan`. Ground the feature in what the project is (the
README, via `orient_summary`); don't make the issue restate the product premise.

## Tone

Senior engineering peer. Not sycophantic. One question at a time.

## Outputs

- A single opening message; `feature_size` (`small` | `large`) in walker state.

## Outgoing edges

- → `discuss` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from kickoff --to discuss
```

## Notes

- **One message, then wait.** The user replies and we move into `discuss`.
- **Don't draft the issue here.** Kickoff opens the conversation; `draft`
  assembles the body.
