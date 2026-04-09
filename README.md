# agent-config

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/coreydaley/agent-config)](https://github.com/coreydaley/agent-config/issues)

A personal configuration repository for [Claude Code](https://claude.ai/code) — managing instructions, skills, commands, and subagents in one place, version-controlled and symlinked into `~/.claude/`.

> **Security notice:** The contents of this repository flow directly into Claude's system prompt. Review all files before use, and never commit secrets or credentials. A `gitleaks` pre-commit hook is included to help catch leaks before they happen.

## What's in here

| Directory | Purpose |
|---|---|
| `CLAUDE.md` | Global instructions loaded by Claude Code on every session |
| `commands/` | Custom slash commands (invoke with `/command-name`) |
| `skills/` | Reusable skill modules auto-discovered by Claude Code |
| `subagents/` | Specialized agents Claude can delegate work to |
| `prompts/` | Standalone prompts for specific tasks |
| `scripts/` | Setup scripts |

## Setup

```bash
git clone https://github.com/coreydaley/agent-config.git
cd agent-config
brew install gitleaks
make all
```

`make all` creates symlinks into `~/.claude/` and installs the gitleaks pre-commit hook. It is idempotent — safe to run multiple times.

### What gets symlinked

```
CLAUDE.md   → ~/.claude/CLAUDE.md
commands/   → ~/.claude/commands/
skills/     → ~/.claude/skills/
subagents/  → ~/.claude/agents/
```

Existing files at symlink destinations are backed up with a `.old` extension before replacement.

### Individual targets

```bash
make symlinks   # Create ~/.claude/ symlinks only
make hooks      # Install gitleaks pre-commit hook only
make help       # Show all available targets
```

## Commands

Invoke with `/command-name` in Claude Code.

| Command | Description |
|---|---|
| `/commit` | Analyze uncommitted changes and create grouped conventional commits |
| `/tag` | Analyze commits since last tag and propose the next semantic version |
| `/sprint-plan` | Multi-agent collaborative sprint planning |
| `/sprint-work` | Execute the next sprint from local docs |
| `/audit-security` | Dual-agent security review → executable sprint |
| `/audit-design` | Dual-agent UI/UX review → executable sprint |
| `/audit-accessibility` | Dual-agent WCAG 2.1/2.2 review → executable sprint |
| `/audit-architecture` | Dual-agent architecture review → executable sprint |
| `/create-blog-post` | AI-powered blog post creation workflow |

## Skills

Skills are auto-discovered from `~/.claude/skills/`. Each skill has a `SKILL.md` with YAML frontmatter describing when it applies.

| Skill | Description |
|---|---|
| `github` | `gh` CLI operations — issues, PRs, releases, branches |
| `frontend-design` | Production-grade UI component creation |
| `mcp-builder` | MCP server creation guidance |
| `ledger` | Sprint ledger tracking |
| `generate-post-image` | Hugo blog post image generation |
| `skill-creator` | Guide for creating new skills |

## Disclaimer

This repository contains AI-generated content. Review all configurations and instructions before use. The creators assume no liability for problems caused by using resources from this repository. See [SECURITY.md](SECURITY.md) for details.
