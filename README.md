# agent-config

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/coreydaley/agent-config)](https://github.com/coreydaley/agent-config/issues)
[![GitHub stars](https://img.shields.io/github/stars/coreydaley/agent-config)](https://github.com/coreydaley/agent-config/stargazers)
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)

A centralized repository for managing AI agent configurations, skills, commands, and subagents across multiple AI CLI platforms: Claude, Codex, Copilot, and Gemini.

> **Security notice:** The contents of this repository flow directly into each agent's system prompt. Review all files — especially `agents/_GLOBAL.md` and agent-specific stubs — before use. Anyone with write access to this repo can influence the behavior of all configured agents.

## Overview

This project provides a centralized location for storing and managing:

- **Agent Configurations** - Per-agent instruction files (merged from shared + agent-specific source)
- **Reusable Skills** - Specialized capabilities that agents can leverage
- **Custom Commands** - Slash commands available to agents (Markdown source; auto-converted to TOML for Gemini)
- **Subagents** - Specialized AI agents that primary agents can delegate work to

## Agent Capability Matrix

Not all features are supported by every agent. The table below shows what each agent supports and where each resource is installed on disk.

| Feature | Claude | Codex | Copilot | Gemini |
|---|---|---|---|---|
| **Config file** | `~/.claude/CLAUDE.md` | `~/.codex/AGENTS.md` | `~/.copilot/copilot-instructions.md` | `~/.gemini/GEMINI.md` |
| **Skills directory** | `~/.claude/skills/` | ❌ no standard path | `~/.copilot/skills/` | ❌ no convention |
| **Commands directory** | `~/.claude/commands/` (.md) | `~/.codex/prompts/` (.md) | ❌ not supported | `~/.gemini/commands/` (.toml) |
| **Subagents directory** | `~/.claude/agents/` (.md) | ❌ not supported | ⚠️ P1: `.agent.md` ext required | `~/.gemini/agents/` (.md) |
| **Command format** | Markdown | Markdown | — | TOML (auto-converted at build time) |

Scripts emit an explicit skip message for any unsupported feature rather than silently skipping.

## Directory Structure

```text
agent-config/
├── README.md                    # This file
├── LICENSE                      # Project license
├── Makefile                     # Build and setup targets
├── agents/                      # Agent configurations
├── skills/                      # Reusable skills for agents
├── commands/                    # Custom commands available to agents
├── subagents/                   # Custom agents for delegation
├── prompts/                     # Custom prompts for specific tasks
└── scripts/                     # Setup and installation scripts
```

## Folders

### agents/

Contains configuration files for four AI agents: Claude, Codex, Copilot, and Gemini.

Each agent has:

- A shared source file: `agents/_GLOBAL.md`
- An agent-specific source file: `agents/<agent>/_<AGENT_NAME>.md`
- A generated merged file: `agents/<agent>/<AGENT_NAME>.md` (generated, gitignored, and symlinked into the agent's home dir)

Generation: `make generate-agent-files` (runs as part of `make all`)

See [agents/README.md](agents/README.md) for symlink targets and details.

### skills/

Reusable skills and specialized capabilities that agents can access and leverage.

**Contents should include:**

- Well-defined capabilities agents can perform
- Domain expertise and knowledge bases
- Procedural workflows and processes
- Specialized knowledge resources

### commands/

Slash commands available to agents. Source files are Markdown (`.md`) with YAML frontmatter.

- Claude reads them directly from `~/.claude/commands/`
- Codex reads them from `~/.codex/prompts/`
- Gemini requires TOML format — files are auto-converted via `make generate-gemini-commands` to `build/gemini-commands/` and symlinked to `~/.gemini/commands/`
- Copilot does not support custom commands

The source of truth is still `commands/*.md`, but the way you invoke a command depends on the agent:

| Agent | `commit` | `tag` | `sprint-plan` | `sprint-work` |
|---|---|---|---|---|
| Claude | `/commit` | `/tag` | `/sprint-plan improve release rollback safety` | `/sprint-work` |
| Codex | `/prompts:commit` | `/prompts:tag` | `/prompts:sprint-plan improve release rollback safety` | `/prompts:sprint-work` |
| Gemini | `/commit` | `/tag` | `/sprint-plan improve release rollback safety` | `/sprint-work` |
| Copilot | Not supported | Not supported | Not supported | Not supported |

Current command workflows include:

- `commit` for analyzing uncommitted changes and creating grouped conventional commits
- `tag` for analyzing commits since the last tag and proposing the next semantic version tag
- `sprint-plan` for creating a sprint plan in local docs and ledger
- `sprint-work` for executing the next local sprint from the repo's sprint docs

The sprint commands also support an optional external planning tool name as the first argument, for example `linear` or `jira`, when the agent has a matching integration available.

Examples:

- `/commit`
- `/commit commands`
- `/tag`
- `/tag patch`
- `/sprint-plan improve release rollback safety`
- `/sprint-plan linear improve release rollback safety`
- `/sprint-work`
- `/sprint-work linear`

Agent-specific examples:

```bash
# Claude
/commit
/commit commands
/tag
/tag patch
/sprint-plan improve release rollback safety
/sprint-plan linear improve release rollback safety
/sprint-work
/sprint-work linear

# Codex
/prompts:commit
/prompts:commit commands
/prompts:tag
/prompts:tag patch
/prompts:sprint-plan improve release rollback safety
/prompts:sprint-plan linear improve release rollback safety
/prompts:sprint-work
/prompts:sprint-work linear

# Gemini
/commit
/commit commands
/tag
/tag patch
/sprint-plan improve release rollback safety
/sprint-plan linear improve release rollback safety
/sprint-work
/sprint-work linear
```

Tool-backed behavior:

- `sprint-plan TOOL_NAME ...` uses `TOOL_NAME` as the external sprint system and the remaining arguments as the planning seed
- After planning approval, `sprint-plan TOOL_NAME ...` should create or update the sprint in that external tool, including stories and tasks/subtasks when needed
- `sprint-work TOOL_NAME` should pull the active or next planned sprint from that tool and execute against the stories and tasks defined there
- If the named tool is not actually available to the agent in the current environment, the command should stop and report the missing integration rather than pretending the sync worked

See [commands/commit.md](commands/commit.md), [commands/tag.md](commands/tag.md), [commands/sprint-plan.md](commands/sprint-plan.md), and [commands/sprint-work.md](commands/sprint-work.md) for the detailed command behavior.

### subagents/

Configurations for custom AI agents that primary agents can delegate work to.

This repository supports subagents, but `subagents/` is currently empty.

**Contents should include:**

- Specialized agent configurations
- Agents designed for specific domains or tasks
- Agent instructions for delegated work
- Subagent capabilities and limitations

### scripts/

Setup and configuration scripts for initializing the AI environment.

All scripts use `utils.sh` for shared helpers. Existing files at symlink destinations are automatically backed up with a `.old` extension before replacement.

**Available scripts:**

| Script | Purpose |
|---|---|
| `generate-agent-files.sh` | Merges `_GLOBAL.md` + `_<AGENT>.md` → `<AGENT>.md` for each agent |
| `generate-gemini-commands.sh` | Converts `commands/*.md` → `build/gemini-commands/*.toml` (TOML format for Gemini) |
| `symlink-agents.sh` | Symlinks per-agent config to the correct filename in each agent's home dir |
| `symlink-skills.sh` | Symlinks `skills/` to Claude and Copilot (skipped for Codex and Gemini) |
| `symlink-commands.sh` | Symlinks `commands/` to Claude and Codex; defers Gemini to `symlink-gemini-commands.sh` |
| `symlink-gemini-commands.sh` | Symlinks `build/gemini-commands/` → `~/.gemini/commands/` |
| `symlink-subagents.sh` | Symlinks `subagents/` to Claude and Gemini (skipped for Codex; P1 for Copilot) |

## Setup

```bash
git clone https://github.com/coreydaley/agent-config.git
cd agent-config
make all
```

`make all` generates merged agent files, converts commands to TOML for Gemini, creates all symlinks, and registers Codex skills in `~/.codex/config.toml`. It is idempotent — safe to run multiple times.

### Individual targets

```bash
make generate             # Generate all artifacts (agent files + Gemini TOML)
make symlinks             # Create all symlinks
make symlink-agents       # Agent config symlinks only
make symlink-skills       # Skills symlinks only (Claude + Copilot)
make symlink-commands     # Command symlinks only (Claude + Codex)
make symlink-gemini-commands # Gemini command symlinks only
make symlink-subagents    # Subagent symlinks only (Claude + Gemini)
make configure-codex-skills # Register Codex skills in ~/.codex/config.toml
make help                 # Show all available targets
```

### Optional: Codex skills registration

Codex does not support a global skills directory. This repo registers skills from `skills/` in `~/.codex/config.toml` as part of `make all`. If you want to run that step by itself:

```bash
make configure-codex-skills
```

### Optional: YOLO mode aliases

Each agent has a flag to skip permission prompts and run fully autonomously. If you want this behavior by default, add these aliases to your shell config (`~/.zshrc`, `~/.bashrc`, etc.):

```bash
alias claude='claude --dangerously-skip-permissions'
alias codex='codex --dangerously-bypass-approvals-and-sandbox'
alias copilot='copilot --allow-all'
alias gemini='gemini --yolo'
```

> **Warning:** These aliases disable all permission prompts. The agent will execute file writes, shell commands, and other actions without asking first. Only use this if you trust the agent configuration in this repo and understand the risks.

### Backup behavior

Existing regular files or directories at symlink destinations are renamed to `.old` before the symlink is created. Existing symlinks are replaced directly.

## Usage

After running `make all`, each agent will load its merged config file automatically. Codex will also have skills from this repo registered in `~/.codex/config.toml`. The capability matrix above shows what each agent can access.

Reference the individual README files for details:

- [agents/README.md](agents/README.md) - Agent configuration and symlink targets

## Contributing

When adding new resources:

- Place them in the appropriate folder (skills, commands, subagents, or prompts)
- Follow the naming conventions established in each directory
- Update the relevant README files with documentation
- Test that symlinks and configurations work correctly

If you encounter a problem, please [open an issue](https://github.com/coreydaley/agent-config/issues). If you'd like to fix an issue or add new functionality, feel free to fork this repository and [submit a pull request](https://github.com/coreydaley/agent-config/pulls).

## Disclaimer

**Please note:** Content in this project is likely generated using AI language models. While efforts have been made to ensure quality and accuracy, AI-generated content can contain errors, outdated information, or unintended biases.

**Use at your own risk.** Always:

- Review AI-generated content before using it in production
- Test configurations and commands thoroughly
- Verify information against authoritative sources
- Consider the limitations and potential issues of AI-generated code and instructions
- Take responsibility for any issues that may arise from using this project

The creators and maintainers assume no liability for problems caused by following instructions or using resources from this repository.
