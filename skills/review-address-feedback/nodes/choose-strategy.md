# Node: choose-strategy

Ask the user how they want to work through the findings. The choice is the route — no separate confirmation gate.

## Inputs

- `mode`, `findings_count` from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
MODE=$(scripts/walk.sh get --state "$STATE" --key mode)
```

## Steps

Use `AskUserQuestion`. Offer:

1. **Fix all** — work through every finding in severity order (Mode B: Blocker → High → Medium → Low → Nit; Mode A: original GitHub order, no severity).
2. **Walk one-by-one** — show each finding, ask per-finding action.
3. **Group logically** — propose groupings (by file, category, related concern), confirm the grouping inline, then fix per group.
4. **Severity filter** *(Mode B only)* — free-form. Examples: "fix Medium and above, defer the rest as Linear issues" or "ignore Nits." Translate into a per-finding plan and **confirm the plan inline** before doing any work.
5. **Pick specific findings** — user names IDs or `file:line` entries; the rest are skipped.
6. **Switch to live PR comments** *(Mode B only)* — restart in Mode A. Routes via `switch_mode` back to `init`.
7. **Cancel** — stop without addressing anything. Routes via `user_cancel` to terminal.

Hide options 4 and 6 in Mode A. (4 has no severity to filter on; 6 is already where you are.)

### Plan-confirm inline (no separate node)

For options 3, 4, and 5, draft the per-finding plan (which finding gets which action) and show it to the user before transitioning to `address`. If the user adjusts ("actually defer R003 too"), update the plan in place. Once confirmed, persist:

```bash
scripts/walk.sh set --state "$STATE" --key strategy --value "<fix_all|walk|group|severity|pick>"
scripts/walk.sh set --state "$STATE" --key plan_path --value "$SESSION_DIR/plan.json"
```

The plan file is a list of `{finding_id, action, group?, defer_target?}` records. `address` reads it.

For options 1 and 2 (fix-all, walk), no upfront plan is needed — `address` handles those modes directly.

## Outputs

- `strategy` in walker state
- `plan_path` in walker state (when applicable)
- `$SESSION_DIR/plan.json` (when applicable)

## Outgoing edges

- **`strategy_chosen`** → `address`. Strategy selected (and plan confirmed where needed).
- **`switch_mode`** → `init`. Mode B only — user wants to switch to live PR comments.
- **`user_cancel`** → `terminal`. User backed out before any work.

Record exactly one:

```bash
# Strategy chosen:
scripts/walk.sh transition --state "$STATE" --from choose_strategy --to address --condition strategy_chosen

# Switch to Mode A:
scripts/walk.sh transition --state "$STATE" --from choose_strategy --to init --condition switch_mode

# Cancel:
scripts/walk.sh transition --state "$STATE" --from choose_strategy --to terminal --condition user_cancel
```

## Notes

- **Default to walk.** When the user is ambiguous, the safer route is to ask per finding — that's `walk`, not `fix all`.
- **The plan is the confirmation.** For severity / group / pick, showing the plan and getting "looks good" *is* the gate. Don't add a redundant "are you sure?" after.
- **Don't auto-translate vague phrasing.** "Just fix the obvious stuff" isn't actionable. Ask the user to pick from the menu.

## Failure modes

- User asks for a 7th option that isn't on the list (e.g. "review more carefully") → clarify and re-prompt.
- User picks `switch_mode` but `pr_number` isn't set (Mode B without parseable header) → bail with "can't switch — REVIEW.md doesn't reference a PR number." Stay in this node, re-prompt.
