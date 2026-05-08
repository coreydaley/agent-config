# Node: register

Phase 9 Step 6: register the sprint in the ledger so `/sprint-work` can find it. Compute participants list, write entry, repeat the Recommended Execution block in the final message.

## Inputs

- `session_dir`, `report_ts`, `recommended_model`, `recommended_tier`, plus all phase-completion flags from walker state

```bash
STATE="<path>"
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
REPORT_TS=$(scripts/walk.sh get --state "$STATE" --key report_ts)
RECOMMENDED_MODEL=$(scripts/walk.sh get --state "$STATE" --key recommended_model)
```

## Step 1: Extract title

Extract the sprint title from the first `# Title` heading in `$SESSION_DIR/SPRINT.md`. The session timestamp `$REPORT_TS` is the sprint's identifier; there's no separate sprint number.

## Step 2: Compute participants list

Who actually produced planning artifacts? Compute from which phases *ran*, not which were enabled. A phase that was enabled but produced no artifact (e.g., worker failed) does NOT count.

- Include `claude` if any Claude-side worker ran:
  - Phase 5a or 5b delegated to a Claude-side worker
  - Phase 6a or 6b delegated to a Claude-side worker
  - Any Phase 8 review routed to Claude (Security, Architecture, Observability, Breaking Change)
- Include `codex` if any Codex-side worker ran:
  - Phase 5a or 5b delegated to a Codex-side worker
  - Phase 6a or 6b delegated to a Codex-side worker
  - Any Phase 8 review routed to Codex (Devil's Advocate, Test Strategy, Performance & Scale)

The orchestrator itself does NOT count as a participant — only delegated workers that produced artifacts. Emit alphabetically.

Examples:

- Single-agent (only Claude-side workers ran): `claude`
- Both-sides: `claude,codex`

This list is what the `/commit` skill reads to build multi-agent `Co-authored-by:` trailers for the sprint-artifact commit.

## Step 3: Register in the ledger

```bash
/sprints --add "$REPORT_TS" "$TITLE" --recommended-model="$RECOMMENDED_MODEL" --participants="$PARTICIPANTS"
```

`$REPORT_TS` is the sprint identifier. `$RECOMMENDED_MODEL` is the model name (`opus` / `sonnet` / `haiku`) from Recommended Execution. `$PARTICIPANTS` is the comma-separated list from Step 2.

## Step 4: Final message

Print:

```
Sprint registered:
  Session:       $REPORT_TS
  Title:         $TITLE
  SPRINT.md:     $SESSION_DIR/SPRINT.md
  Participants:  $PARTICIPANTS
  Recommended:   $RECOMMENDED_MODEL ($RECOMMENDED_TIER tier)

To run the sprint:
    /model $RECOMMENDED_MODEL
    /sprint-work
```

Repeat the **Recommended Execution** block fully so the exact `/model` and `/sprint-work` commands are the last thing the user sees.

## Outputs

- Ledger entry for the sprint
- Printed final message

## Outgoing edges

- → `terminal` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from register --to terminal
```

## Notes

- **The orchestrator doesn't count** as a participant. Only delegated workers that produced artifacts. (The orchestrator's `Co-authored-by:` trailer comes from `/commit`'s default; it's not from the participants list.)
- **Don't run `git commit` / `git push`.** This skill doesn't touch git. The user does that explicitly later.
- **Don't push to Linear** — that's `/sprint-plan-to-linear`'s job, run separately if the user wants Linear coverage.
