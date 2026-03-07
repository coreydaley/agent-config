# Codex-Specific Instructions

## Sandbox Awareness

Codex runs in a sandboxed environment. File system access is scoped to the working directory. Network access may be restricted depending on the approval mode.

## AGENTS.md Format

This file (`~/.codex/AGENTS.md`) is loaded as global instructions before every session. Structure it with clear sections. Codex also reads `AGENTS.md` files in the project root and current directory, with closer files taking precedence.

## Custom Prompts

Custom prompts live in `~/.codex/prompts/` as Markdown files. Invoke with `/prompts:command-name` in the Codex CLI.

## Skills

Skills must be registered via `~/.codex/config.toml` with `[[skills.config]]` entries pointing to each `SKILL.md` path.
