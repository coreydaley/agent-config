---
name: ledger
description: Sprint ledger manager for tracking sprint progress. Use when checking sprint status, syncing the ledger, adding sprints, or updating sprint state.
argument-hint: <subcommand> [args]
allowed-tools: Bash(python3 *)
---

# Sprint Ledger

Manage the sprint ledger by running:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/ledger.py $ARGUMENTS
```

The script resolves `ledger.tsv` to `~/Reports/<repo-path>/ledger.tsv` (derived from `pwd` stripping everything up to and including `.../Code/`). Run from the project root.

> **Model invocation note**: Model invocation of this skill is intentional and expected. The `/sprint` command calls this skill via the Skill tool to update ledger state as part of its workflow. The `allowed-tools: Bash(python3 *)` constraint remains as the execution guardrail.

## Subcommands

| Subcommand | Description |
|---|---|
| `stats` | Overview of all sprints |
| `current` | Show in-progress sprint |
| `next` | Show next planned sprint |
| `list [--status <status>]` | List sprints, optionally filtered by status |
| `add NNN "Title"` | Add a new sprint entry |
| `start NNN` | Mark sprint as in_progress |
| `complete NNN` | Mark sprint as completed |
| `skip NNN` | Mark sprint as skipped |
| `status NNN <status>` | Set arbitrary status |
| `sync` | Sync ledger from `*-sprint-plan-SPRINT-*.md` files in `~/Reports/<repo-path>/` |

Valid statuses: `planned`, `in_progress`, `completed`, `skipped`
