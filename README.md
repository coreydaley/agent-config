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

Invoke with `/command-name` in Claude Code. Commands with `disable-model-invocation` must be called explicitly; others may also trigger automatically based on context.

| Command | Description |
|---|---|
| `/commit` | Analyze uncommitted changes and create grouped conventional commits |
| `/tag` | Analyze commits since last tag and propose the next semantic version |
| `/create-task` | Create a new task note in the Obsidian vault |
| `/create-knowledge` | Create a new knowledge note in the Obsidian vault |
| `/create-draft` | Create a new draft note in the Obsidian vault |
| `/create-read-later` | Add a URL to the Read Later list in the Obsidian vault |
| `/sandbox-script` | Create a new standalone script in the sandbox |
| `/sandbox-project` | Create a new project directory in the sandbox |
| `/sprint-plan` | Multi-agent collaborative sprint planning |
| `/sprint-work` | Execute the next sprint from local docs |
| `/audit-security` | Dual-agent security review → findings report |
| `/audit-design` | Dual-agent UI/UX review → findings report |
| `/audit-accessibility` | Dual-agent WCAG 2.1/2.2 review → findings report |
| `/audit-architecture` | Dual-agent architecture review → findings report |
| `/create-blog-post` | AI-powered blog post creation workflow |

## Skills

Skills are auto-discovered from `~/.claude/skills/`. Each skill has a `SKILL.md` with YAML frontmatter describing when it applies. Skill descriptions are always loaded into context; skill bodies load only when triggered.

| Skill | Description |
|---|---|
| `github` | `gh` CLI operations — issues, PRs, releases, branches |
| `obsidian` | Obsidian vault operations via the `obsidian` CLI |
| `orbstack` | OrbStack management — Linux machines, Docker, Kubernetes |
| `frontend-design` | Production-grade UI component creation |
| `ledger` | Sprint ledger tracking |
| `generate-post-image` | Hugo blog post image generation |
| `skill-creator` | Guide for creating new skills |

## Subagents

Subagents are specialized agents Claude delegates work to via the Agent tool. Their full workflow runs in an isolated context, keeping the main conversation clean. Defined in `subagents/` (symlinked to `~/.claude/agents/`).

| Subagent | Description |
|---|---|
| `audit-security` | Dual-agent security audit — 5-phase workflow (orient, independent reviews, synthesis, devil's advocate, report) |
| `audit-accessibility` | Dual-agent WCAG 2.1/2.2 audit — same 5-phase pattern with accessibility-specific finding schema |
| `audit-architecture` | Dual-agent architecture audit — findings anchored to named principles with migration cost estimates |
| `audit-design` | Dual-agent UI/UX audit — findings anchored to Nielsen heuristics and project design system |

### Audit output

Each audit run writes timestamped artifacts to `~/Reports/<repo-path>/`:

```
$REPORT_TS-audit-security-claude.md          ← Claude's independent review
$REPORT_TS-audit-security-codex.md           ← Codex's independent review
$REPORT_TS-audit-security-synthesis.md       ← unified findings
$REPORT_TS-audit-security-devils-advocate.md ← Codex challenge pass
$REPORT_TS-audit-security-report.md          ← final findings report
```

The report is a reference document. To act on findings, run `/sprint-plan` and use the report as the seed.

## Disclaimer

This repository contains AI-generated content. Review all configurations and instructions before use. The creators assume no liability for problems caused by using resources from this repository. See [SECURITY.md](SECURITY.md) for details.
