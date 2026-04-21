---
name: sprints
description: Sprint manager for tracking sprint progress. Use when checking sprint status, syncing sprints, adding sprints, or updating sprint state.
argument-hint: <action-flag> [args]
allowed-tools: Bash(python3 *)
---

# Sprints

Manage the sprint ledger by running:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/sprints.py $ARGUMENTS
```

The script resolves the data file to `./docs/sprints/sprints.tsv` relative to the current working directory. Run from the project root; `docs/sprints/` is created if it doesn't exist.

> **Model invocation note**: Model invocation of this skill is intentional and expected. The `/sprint-plan` and `/sprint-work` skills call this skill via the Skill tool to update sprint state as part of their workflow. The `allowed-tools: Bash(python3 *)` constraint remains as the execution guardrail.

## Flags

Exactly one action flag per invocation.

| Action flag | Description |
|---|---|
| `--stats` | Overview of all sprints (includes velocity summary when data exists) |
| `--current` | Show the in-progress sprint |
| `--next` | Show the next planned sprint |
| `--list` | List all sprints (combine with `--status` to filter) |
| `--velocity` | Velocity statistics across completed sprints (mean, median, rolling, by model) |
| `--add NNN "Title"` | Add a new sprint entry (optionally with `--recommended-model=<name>`) |
| `--start NNN [--model=<name>]` | Mark sprint NNN as in_progress; record model if given |
| `--complete NNN [--model=<name>]` | Mark sprint NNN as completed; record model if not already set |
| `--skip NNN` | Mark sprint NNN as skipped |
| `--set-status NNN <status>` | Set arbitrary status for sprint NNN |
| `--set-fit NNN <verdict>` | Record post-sprint fit from the retro. Values: `over_powered`, `right_sized`, `under_powered`. |
| `--sync` | Sync sprints from `*-sprint-plan-SPRINT-*.md` files in `./docs/sprints/` |
| `--help`, `-h` | Show usage summary and exit |

| Modifier flag | Description |
|---|---|
| `--status=<status>` | Filter for `--list` (e.g. `--list --status=planned`) |
| `--model=<name>` | Record the Claude model family (`opus` / `sonnet` / `haiku`) on a sprint. Pair with `--start` (primary) or `--complete`. |
| `--recommended-model=<name>` | What sprint-plan suggested at planning time. Pair with `--add`. |

Valid statuses: `planned`, `in_progress`, `completed`, `skipped`
