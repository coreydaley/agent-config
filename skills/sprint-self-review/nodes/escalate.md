# Node: escalate

The single user-gate. Compose an in-memory prompt from the current state and ask the user. Route based on their answer. No persistent file is written — `findings.md` is already the source of truth, and the prompt is ephemeral by design.

## Inputs

- `$FINDINGS` (current ledger state)
- The entry condition from `decide` (`only_low_nit`, `iter_cap`, or `needs_user_input`) — this drives which prompt to compose
- The state counts computed by `decide` (`high_open`, `low_open`, `escalation_pending`, `fixed`, `triaged`)

## Three modes

The prompt body depends on which entry condition got us here. The two outgoing edges (`user_continue` / `user_done`) are the same regardless.

### Mode A: `only_low_nit` (terminal-ish, came from decide)

Compose:

```
Self-review reached terminal: no Blocker/High/Medium findings open.

State recap:
- Iterations completed: {ITER_N}
- Findings: {total} total
  - Resolved: {fixed}
  - Triaged (won't-fix / deferred / skipped): {triaged}
  - Open at LOW/NIT: {low_open}
  - Pending user input: {escalation_pending}

Full ledger: {FINDINGS}

What next?
1. Done — proceed to terminal (you'll push, run CI, mark ready when satisfied)
2. Continue — run another batch of up to {MAX_CYCLES} iterations on the LOW/NIT findings
```

Ask via AskUserQuestion. Map the answer:
- "Done" / "1" → `user_done` → terminal
- "Continue" / "2" → `user_continue` → review (and reset the iteration cap window for the next batch)

### Mode B: `iter_cap` (out of cycles, came from decide)

Compose:

```
Iteration cap hit ({MAX_CYCLES} cycles). Still open:
- Blocker/High/Medium: {high_open}
- Low/Nit: {low_open}

Resolved this run: {fixed}
Full ledger: {FINDINGS}

What next?
1. Continue — next batch of {MAX_CYCLES} iterations
2. Done — accept current state and proceed to terminal
```

Map:
- "Continue" / "1" → `user_continue` → review (reset cap window)
- "Done" / "2" → `user_done` → terminal

### Mode C: `needs_user_input` (mid-iteration, came from decide)

There may be one or more findings in the ledger marked for escalation. Process each one in turn (or batch related ones in a single prompt if it makes sense).

For an **ambiguous dedup match** (`*pending-dedup-check*`):

```
Ambiguous match — is this the same as a prior finding?

This iteration found:
  CR-NNN  {File:Line}  {Severity}  {Issue}

Prior ledger entry that could be the same:
  LR-MMM  {File:Line}  {Severity}  {Issue}  ({status})

Match score: {score} (above threshold but below confident match)

What is this?
1. Same as LR-MMM — append CR-NNN to LR-MMM's "Seen in:" and continue
2. New finding — create a new ledger entry, continue addressing
3. Done — I'll handle from here
```

Map:
- "Same" / "1" → update ledger (merge), → `user_continue` → review
- "New" / "2" → create new ledger entry with status `*open*`, → `user_continue` → review
- "Done" / "3" → `user_done` → terminal

For a **fix-verification failure** (`*escalated: fix failed verification*`):

```
Fix attempt failed verification.

Finding: LR-NNN  {File:Line}  {Severity}  {Issue}
Attempted fix: {summary}
Failure: {test/lint output}

What next?
1. Continue — leave as open, retry next iteration (the agent will try a different approach)
2. Skip this finding — mark as won't-fix with the reason, continue with others
3. Done — I'll handle from here
```

Map options similarly. For "Skip", update the ledger entry to `*won't-fix: {reason}*` before transitioning.

For a **fix-cannot-verify** (`*escalated: cannot verify fix*`) or other escalation states: compose an analogous prompt with the relevant context.

If multiple findings are pending, present them sequentially. The user resolves each before the next is shown.

## Outputs

- Possibly updated `$FINDINGS` (resolution of an ambiguous match, user-decided skip, etc.)
- One state transition

## Outgoing edges

- **`user_continue`** → `review` — user wants to keep iterating. If we came from `iter_cap` or a Mode A "continue", reset the iteration counter window so the next `MAX_CYCLES` cycles count from now (don't immediately re-trip the cap).
- **`user_done`** → `terminal` — user is satisfied or wants to take over manually.

If the user chose to continue and we came from `iter_cap` (or any end-state cause), reset `cycles_in_run` so the next batch of `max_cycles` cycles counts from now:

```bash
scripts/walk.sh set --state "$PR_DIR/.walk-state.json" --key cycles_in_run --value 0
```

Record the transition (pick exactly one):

```bash
# user chose to continue (loops through compute-diff for a fresh iteration):
scripts/walk.sh transition --state "$PR_DIR/.walk-state.json" --from escalate --to compute_diff --condition user_continue

# user chose to end:
scripts/walk.sh transition --state "$PR_DIR/.walk-state.json" --from escalate --to terminal --condition user_done
```

## Notes

- **Always show the ledger path**. The user might want to open `findings.md` directly to see full context before answering.
- **One question at a time.** If multiple things need user input, ask sequentially. Stacking them in one prompt is harder to follow.
- **Don't be cute.** This is a control surface, not a chat. Plain options, plain numbering.
- **Default to safe.** If the user gives an ambiguous response, ask again rather than guessing.

## Failure modes

- User aborts (Ctrl-C) → treat as `user_done` and proceed to terminal. The ledger and per-iteration artifacts are on disk; nothing is lost.
- Cannot determine entry condition → treat as Mode A (only_low_nit) and ask the user for the catch-all "continue or done?" prompt. Surfaces the issue without breaking the cycle.
