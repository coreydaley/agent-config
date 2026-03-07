# Gemini-Specific Instructions

## Context

Gemini CLI is an open-source AI agent from Google. It integrates well with Google Cloud, Google Search grounding, and MCP servers.

## GEMINI.md Loading

This file (`~/.gemini/GEMINI.md`) is loaded as global context for all Gemini CLI sessions. Additional `GEMINI.md` files in project directories are also loaded hierarchically.

## Importing Context

Use `@path/to/file.md` syntax to import content from other files into this context. For example, to include a skill's instructions directly:

```
@skills/my-skill/SKILL.md
```

## Custom Commands

Custom commands live in `~/.gemini/commands/` as `.toml` files with `description` and `prompt` fields. This repository auto-generates these from `commands/*.md` sources.

## Subagents

Custom subagent definitions live in `~/.gemini/agents/` as Markdown files with YAML frontmatter. Required fields: `name`, `description`, `tools` (comma-separated list of allowed tools).
