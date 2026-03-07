# Claude-Specific Instructions

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
