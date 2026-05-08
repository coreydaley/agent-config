# Node: decide

Single point of state evaluation. Read the ledger, count what's open, compare against the iteration cap, and route. Decide doesn't ask anything of the user — that's `escalate`'s job. Decide just picks the right outgoing edge.

## Inputs

- `$FINDINGS` (the ledger, as updated by `address` or untouched on the `no_addressable` path)
- `cycles_in_run` and `max_cycles` from the walker's extra state (read via `scripts/walk.sh get --state "$STATE" --key cycles_in_run` etc.). The cap compares cycles within this *invocation* — if the user previously chose `user_continue` after `iter_cap`, escalate resets `cycles_in_run` so the next batch counts from zero.

## State to compute

From `$FINDINGS`, count:

- **`high_open`** — entries with status `*open*` or `*regression after iter-N*` and Severity in {Blocker, High, Medium}
- **`low_open`** — entries with status `*open*` or `*regression after iter-N*` and Severity in {Low, Nit}
- **`escalation_pending`** — entries with status `*escalated, awaiting user*`, `*escalated: fix failed verification*`, `*escalated: cannot verify fix*`, or `*pending-dedup-check*`
- **`fixed`** — entries with status `*fixed in iter-N*`
- **`triaged`** — entries with status `*won't-fix*`, `*deferred*`, or `*skipped*`

## Outgoing edges

Evaluate in order — first match wins.

### 1. `needs_user_input` → `escalate`

**Condition:** `escalation_pending > 0`

Any finding marked for escalation always wins, regardless of iteration count or other state. Don't keep iterating with unresolved ambiguity. Route to `escalate` so the user can resolve before we continue.

### 2. `iter_cap` → `escalate`

**Condition:** `cycles_in_run >= max_cycles` (we've completed `max_cycles` iterations in this invocation, the next one would exceed the cap)

The iteration cap protects against runaway loops. Even if there are still `high_open` findings, hand control to the user at the cap. They decide whether to continue.

### 3. `keep_iterating` → `compute-diff`

**Condition:** `high_open > 0` (and the prior conditions didn't match — implicit: `escalation_pending == 0`, `cycles_in_run < max_cycles`)

Findings remain that the agent can address, and we have iterations left. Loop back through `compute-diff` to start another iteration of the review pipeline (independent-reviews → synthesis → devils-advocate → write-iteration-review → address). `compute-diff` increments `cycles_in_run` on entry — decide doesn't need to.

### 4. `only_low_nit` → `escalate`

**Condition:** `high_open == 0`

No Blocker/High/Medium open. We're at terminal-ish state. Even if `low_open > 0`, we route to escalate so the user can decide whether to keep iterating on cosmetic issues or wrap up.

## Outputs

- One state transition (no files written)
- The chosen edge label is communicated to the next node so it knows which mode to operate in (especially for `escalate`, which composes its prompt based on the entry condition)

## Recording the transition

Pick exactly one based on the evaluation above:

```bash
# needs_user_input (escalation pending in ledger):
scripts/walk.sh transition --state "$PR_DIR/.walk-state.json" --from decide --to escalate --condition needs_user_input

# iter_cap (out of cycles):
scripts/walk.sh transition --state "$PR_DIR/.walk-state.json" --from decide --to escalate --condition iter_cap

# keep_iterating (Blocker/High/Medium open, cycles_in_run < max_cycles):
scripts/walk.sh transition --state "$PR_DIR/.walk-state.json" --from decide --to compute_diff --condition keep_iterating

# only_low_nit (no Blocker/High/Medium open):
scripts/walk.sh transition --state "$PR_DIR/.walk-state.json" --from decide --to escalate --condition only_low_nit
```

The escalate node reads the condition from `.walk-state.json` history to pick its prompt mode. The keep_iterating path goes through compute-diff (loop entry point) so the next iteration starts with a fresh diff against the working tree (post-address fixes).

## Notes

- The condition order is the precedence. Don't reorder without thinking through the cases — the priority matters when multiple conditions could match.
- `decide` is purely deterministic: same ledger + same iter count + same cap = same edge. No randomness, no LLM judgment beyond reading the ledger.
- The state counts are a useful audit trail. Consider logging them to working memory for `escalate` to draw on when composing its prompt.

## Failure modes

- Ledger is empty / missing: shouldn't happen by the time decide runs (init creates it, address writes to it). If it does, treat as `only_low_nit` (zero findings = terminal-ish) and route to escalate so the user can confirm.
