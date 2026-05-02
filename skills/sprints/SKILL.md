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

The script resolves the ledger to `~/Reports/<org>/<repo>/ledger.tsv`, with `<org>/<repo>` derived from `git remote get-url origin` in the current directory. Run from a project worktree; `~/Reports/<org>/<repo>/` is created if it doesn't exist. Outside a git repo, falls back to `~/Reports/_no-repo/`.

Sprint planning sessions live at `~/Reports/<org>/<repo>/sprints/<TS>/` where `<TS>` is `YYYY-MM-DDTHH-MM-SS`. **The session timestamp IS the sprint identifier** — there's no separate sprint number. Most commands accept a `<query>` that resolves via session-prefix or title-substring match (ambiguous queries error out with the matching list).

> **Model invocation note**: Model invocation of this skill is intentional and expected. The `/sprint-plan` and `/sprint-work` skills call this skill via the Skill tool to update sprint state as part of their workflow. The `allowed-tools: Bash(python3 *)` constraint remains as the execution guardrail.

## Flags

Exactly one action flag per invocation. `<query>` accepts a session timestamp (full or prefix) or a title substring.

| Action flag | Description |
|---|---|
| `--stats` | Overview of all sprints (includes velocity summary when data exists) |
| `--current` | Show the in-progress sprint |
| `--next` | Show the next planned sprint |
| `--list` | List all sprints (combine with `--status` to filter) |
| `--velocity` | Velocity statistics across completed sprints (mean, median, rolling, by model) |
| `--add <TS> "Title"` | Register an existing sprint session in the ledger (optionally with `--recommended-model=<name>`, `--participants=<list>`) |
| `--start <query> [--model=<name>]` | Mark sprint as in_progress; record model if given |
| `--complete <query> [--model=<name>]` | Mark sprint as completed; record model if not already set |
| `--skip <query>` | Mark sprint as skipped |
| `--set-status <query> <status>` | Set arbitrary status |
| `--set-fit <query> <verdict>` | Record post-sprint fit from the retro. Values: `over_powered`, `right_sized`, `under_powered`. |
| `--sync` | Sync sprints from `~/Reports/<org>/<repo>/sprints/<TS>/SPRINT.md` files. Title comes from the first `# Title` heading; session is the parent folder name. |
| `--path <query>` | Print absolute session folder path for the resolved sprint. Used by `/sprint-work` to find the plan and write the retro. |
| `--help`, `-h` | Show usage summary and exit |

| Modifier flag | Description |
|---|---|
| `--status=<status>` | Filter for `--list` (e.g. `--list --status=planned`) |
| `--model=<name>` | Record the Claude model family (`opus` / `sonnet` / `haiku`) on a sprint. Pair with `--start` (primary) or `--complete`. |
| `--recommended-model=<name>` | What sprint-plan suggested at planning time. Pair with `--add`. |
| `--participants=<list>` | Who participated in planning (comma-separated subset of `claude`, `codex`). Pair with `--add`. |

Valid statuses: `planned`, `in_progress`, `completed`, `skipped`
