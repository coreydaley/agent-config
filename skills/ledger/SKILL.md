---
name: ledger
description: Sprint ledger manager for tracking sprint progress. Use when checking sprint status, syncing the ledger, adding sprints, or updating sprint state.
argument-hint: <subcommand> [args]
disable-model-invocation: true
allowed-tools: Bash(python3 *)
---

# Sprint Ledger

Manage the sprint ledger by running:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/ledger.py $ARGUMENTS
```

The script resolves `ledger.tsv` relative to the current working directory at `docs/sprints/ledger.tsv`, so it must be run from the project root.

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
| `sync` | Sync ledger from SPRINT-*.md files in docs/sprints/ |

Valid statuses: `planned`, `in_progress`, `completed`, `skipped`
