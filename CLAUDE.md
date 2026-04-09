# Claude Code Instructions

## Commit Style

Use Conventional Commits for all git commits:

```
<type>(<scope>): <short summary>
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `style`, `ci`

- Summary: imperative mood, lowercase, no trailing period, max 72 chars
- Always include a `Co-authored-by:` trailer identifying the AI agent

## Code Conventions

- Prefer editing existing files over creating new ones
- Avoid over-engineering; implement only what is needed
- Do not add comments unless the logic is non-obvious
- Never commit secrets, credentials, or `.env` files

## Tools

Claude Code has access to file system tools (Read, Write, Edit, Glob, Grep), Bash, and browser tools. Use dedicated tools (Read, Edit, Glob) in preference to Bash equivalents.

## Memory

CLAUDE.md files are loaded hierarchically: `~/.claude/CLAUDE.md` (global) → project root → subdirectories. More specific files take precedence.

## Skills

Skills in `~/.claude/skills/` are auto-discovered. Each skill has a `SKILL.md` with YAML frontmatter describing when it applies.

## Commands

Custom slash commands live in `~/.claude/commands/`. Invoke with `/command-name`.

## Subagents

Subagent definitions in `~/.claude/agents/` can be delegated work via the Agent tool.

## Obsidian Vault

The vault lives at `~/Vault/` (symlinked from iCloud for backup). It is an Obsidian vault. Refer to it as "the vault."

### Structure

| Path | Purpose |
|---|---|
| `~/Vault/Tasks/` | Task notes — one note per task, organized by project subfolder |
| `~/Vault/Tasks.base` | Obsidian Base with table and board views for tasks |
| `~/Vault/Knowledge/` | Knowledge base notes, organized by topic subfolder |
| `~/Vault/Knowledge.base` | Obsidian Base with table and board views for knowledge |
| `~/Vault/Templates/Task.md` | Template for new task notes |
| `~/Vault/Templates/Knowledge.md` | Template for new knowledge notes |
| `~/Vault/Drafts/` | Draft notes — ideas, LinkedIn posts, blog posts, etc. |
| `~/Vault/Drafts.base` | Obsidian Base with table and board views for drafts |
| `~/Vault/Templates/Draft.md` | Template for new draft notes |

### Task properties

| Property | Type | Values |
|---|---|---|
| `status` | text | `todo`, `in-progress`, `done`, `blocked` |
| `priority` | text | `low`, `medium`, `high`, `urgent` |
| `due` | date | ISO date |
| `project` | text | free text |
| `tags` | list | free text |
| `created` | date | ISO date |

Task title = note filename. When creating tasks, use the template at `~/Vault/Templates/Task.md`.

### Knowledge properties

| Property | Type | Values |
|---|---|---|
| `type` | text | `concept`, `reference`, `how-to`, `decision`, `tool`, `person` |
| `status` | text | `draft`, `review`, `stable`, `archived` |
| `source` | text | URL, book, person, etc. |
| `tags` | list | free text |
| `created` | date | ISO date |
| `summary` | text | one-liner description |

Knowledge title = note filename. When creating knowledge notes, use the template at `~/Vault/Templates/Knowledge.md`.

### Draft properties

| Property | Type | Values |
|---|---|---|
| `type` | text | `idea`, `linkedin-post`, `blog-post`, `email`, `note` |
| `status` | text | `raw`, `in-progress`, `ready`, `published`, `abandoned` |
| `tags` | list | free text |
| `created` | date | ISO date |
| `summary` | text | one-liner description |

Draft title = note filename. When creating drafts, use the template at `~/Vault/Templates/Draft.md`.

## Sandbox

The sandbox lives at `~/Code/sandbox/` (private GitHub repo: `coreydaley/sandbox`). It is for quick experiments, scripts, and prototypes.

| Path | Purpose |
|---|---|
| `~/Code/sandbox/scripts/` | Quick standalone scripts |
| `~/Code/sandbox/projects/` | Larger experiments, POCs, and prototypes |

When asked to build a proof of concept, prototype, or experiment, create an appropriately named subfolder in `projects/` and work there.

## Git

**NEVER commit or push git changes unless explicitly instructed to do so.** This is an absolute rule with no exceptions — do not commit "just to save progress", do not push after committing, do not assume that completing a task implies permission to commit. Always wait for an explicit instruction like "commit this" or "go ahead and push".

## Disclaimer

This repository contains AI-generated content. Review all configurations, scripts, and instructions before use in production or sensitive environments. See SECURITY.md for details.
