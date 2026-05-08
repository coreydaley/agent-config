# Node: ask-spike

Phase 9 Step 2: feasibility-spike escape hatch. Findings reveal high uncertainty; user picks how to proceed.

## Inputs

- `uncertainty_reasons`, `sprint_md_path` from walker state

```bash
STATE="<path>"
REASONS=$(scripts/walk.sh get --state "$STATE" --key uncertainty_reasons)
SPRINT_MD=$(scripts/walk.sh get --state "$STATE" --key sprint_md_path)
```

## Steps

1. **Surface the specific unresolved uncertainty.** Print the reasons inline — what `incorporate-findings` flagged (architecture not validated, prototyping needed, etc.).

2. **Use `AskUserQuestion`:**

   > Reviews surfaced structural uncertainty: <one-line summary>.
   > How would you like to proceed?
   >
   > 1. **Ship a spike plan instead** — replace SPRINT.md with a 1-3 day feasibility spike with clear exit criteria
   > 2. **Proceed with the full sprint plan, accepting the risk** — keep SPRINT.md as-is; flag the risk in Recommended Execution
   > 3. **Narrow scope** — keep what *can* be committed now, defer the uncertain parts
   > 4. **Cancel** — stop without finalizing

3. **Persist the user's choice:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key spike_choice --value "<spike|accept|narrow|cancel>"
   ```

4. **Apply the choice to SPRINT.md:**

   - **spike**: rewrite `$SESSION_DIR/SPRINT.md` as a feasibility spike (small, time-boxed, clear exit criteria pointing back to the original sprint goal). The seed and intent stay; the implementation plan changes substantially.
   - **accept**: leave SPRINT.md as-is. `recommend-execution` will note the accepted risk.
   - **narrow**: edit SPRINT.md to drop the uncertain parts to Deferred. Add a "Future work" section pointing at the dropped items.
   - **cancel**: don't modify anything; route to terminal.

## Outputs

- `spike_choice` in walker state
- Possibly modified `$SESSION_DIR/SPRINT.md`

## Outgoing edges

- **`user_chose`** → `recommend-execution`. User picked spike / accept / narrow.
- **`user_cancel`** → `terminal`. User backed out.

Record exactly one:

```bash
# Proceed:
scripts/walk.sh transition --state "$STATE" --from ask_spike --to recommend_execution --condition user_chose

# Cancel:
scripts/walk.sh transition --state "$STATE" --from ask_spike --to terminal --condition user_cancel
```

## Notes

- **Default to "narrow scope" when ambiguous.** It's the most conservative non-cancel option — keeps what's committable, defers what isn't.
- **Don't auto-spike.** The spike is a meaningful pivot; the user owns the call.
- **The choice is the gate.** No follow-up "are you sure?".
