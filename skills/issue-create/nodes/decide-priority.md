# Node: decide-priority

A short guided aid that lands on a **priority** — `priority/p0`, `priority/p1`, or
`priority/defer`. Runs **at the end**, after the body is drafted, because severity is
only honestly knowable once the item is fleshed out.

This is the "help me decide priority" step: ask a few quick questions, recommend a
level with a one-line rationale, and let the user confirm or override. Priority is
**required** — every issue this skill files gets exactly one `priority/*`.

## Inputs

- `issue_type`, the rendered body from `draft`

```bash
STATE="$SESSION_DIR/.walk-state.json"
ISSUE_TYPE=$(scripts/walk.sh get --state "$STATE" --key issue_type)
```

## Steps

### 1. Ask the few questions that actually separate the tiers

Keep it to a short batch, framed for the type:

- **Impact** — if this stays unfixed, what breaks and for whom? (core function /
  data / security exposure → high; annoyance / cosmetic → low)
- **Workaround** — is there a reasonable way around it today? (none → higher)
- **Frequency / reach** — every user / every run, or a narrow edge case?
- **Time pressure** — does something external make it urgent (a release, a user
  waiting, an exposure window)?

For **security**: bias up. A live, exploitable exposure is `p0`; an unexploited
hardening gap is at least `p1` unless clearly theoretical.

For **docs / refactor / test / chore**: these are usually `p1` or `defer` — reserve
`p0` for cases that actively block shipping or hide a real defect.

### 2. Recommend, with one line of why

Map the answers to a tier and say it plainly:

- **priority/p0 — critical.** Core function broken / data loss / live security
  exposure, no workaround. Drop-everything.
- **priority/p1 — important.** Meaningfully hurts users or is a valuable change you
  want soon; no clean workaround, but not catastrophic.
- **priority/defer — low.** Nice-to-have, cosmetic, edge-case, or fine to wait
  indefinitely.

State your recommendation and the single deciding factor ("no workaround + every
run → p1"). Then let the user confirm or pick a different tier — the call is theirs.

### 3. Persist

```bash
scripts/walk.sh set --state "$STATE" --key priority --value "<p0|p1|defer>"
```

## Distinctions to keep straight (don't conflate)

- **`priority/defer` is a severity, not a sweep gate.** It means "low priority, do it
  eventually." It is NOT `deferred/<reason>` (the "parked, don't auto-pick"
  triage label) — this skill never sets `deferred/*`.
- **Priority is not size.** Don't let "this is a lot of work" pull the priority down;
  effort is `size/*`, set at work-time, never here.

## Outputs

- `priority` (`p0` | `p1` | `defer`) in walker state

## Outgoing edges

- → `ask-create` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from decide_priority --to ask_create
```

## Notes

- **Required, but quick.** Two or three questions, a recommendation, a confirm. Don't
  turn it into an interrogation.
- **Recommend; don't decide for them.** Surface the rationale; the user sets the tier.
