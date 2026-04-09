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

## Disclaimer

This repository contains AI-generated content. Review all configurations, scripts, and instructions before use in production or sensitive environments. See SECURITY.md for details.
