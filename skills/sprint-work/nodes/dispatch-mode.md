# Node: dispatch-mode

Pure decision: route on flags set during `init`. Three subgraphs branch from here.

## Inputs

- `flag_review`, `flag_retro` from walker state

```bash
STATE="<path>"
FLAG_REVIEW=$(scripts/walk.sh get --state "$STATE" --key flag_review)
FLAG_RETRO=$(scripts/walk.sh get --state "$STATE" --key flag_retro)
```

## Steps

Decide:

- `flag_review=true` → `review` (`--review` wins over `--retro` when both somehow set, per the SKILL.md).
- `flag_retro=true` → `retro`.
- Otherwise → `normal`.

## Outputs

- No state changes; pure routing.

## Outgoing edges

- **`review`** → `render-plan-and-exit`.
- **`retro`** → `verify-merged`.
- **`normal`** → `detect-repo`.

Record exactly one:

```bash
# --review:
scripts/walk.sh transition --state "$STATE" --from dispatch_mode --to render_plan_and_exit --condition review

# --retro:
scripts/walk.sh transition --state "$STATE" --from dispatch_mode --to verify_merged --condition retro

# Normal execution:
scripts/walk.sh transition --state "$STATE" --from dispatch_mode --to detect_repo --condition normal
```

## Notes

- **`--review` over `--retro`** is mandated by the SKILL.md precedence rules. Surface the override during `init` if both flags are set.
- **No user input here.** Pure routing; user gates live downstream in each subgraph.
