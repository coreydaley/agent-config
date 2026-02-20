# Artificial Intelligence

A comprehensive repository for managing AI agent configurations, capabilities, and extensions across multiple AI platforms (Claude, Codex, and Copilot).

## Overview

This project provides a centralized location for storing and managing:

- **Agent Configurations** - Settings and instructions for different AI agents
- **Reusable Skills** - Specialized capabilities that agents can leverage
- **Custom Commands** - Tools and operations available to agents
- **Subagents** - Specialized AI agents that primary agents can delegate work to
- **Custom Prompts** - Task-specific prompts that enhance agent performance

## Directory Structure

```
artificial-intelligence/
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

Contains configuration files for the three primary AI agents: Claude, Codex, and Copilot.

Each agent has:

- A markdown file with agent-specific instructions and configuration
- A `GLOBAL.md` file with shared settings available to all agents

**Contents should include:**

- Custom instructions and behavioral guidelines
- Agent capabilities and limitations
- Tool integrations and API configurations
- Context and best practices for that agent

See [agents/README.md](agents/README.md) for details.

### skills/

Reusable skills and specialized capabilities that agents can access and leverage.

**Contents should include:**

- Well-defined capabilities agents can perform
- Domain expertise and knowledge bases
- Procedural workflows and processes
- Specialized knowledge resources

### commands/

Custom commands and tools that are available to agents for execution.

**Contents should include:**

- CLI commands and scripts
- Utility functions agents can call
- Operational tools and workflows
- Integration points with external systems

### subagents/

Configurations for custom AI agents that primary agents can delegate work to.

**Contents should include:**

- Specialized agent configurations
- Agents designed for specific domains or tasks
- Agent instructions for delegated work
- Subagent capabilities and limitations

### prompts/

Custom prompts for specific tasks that don't fit into skills or commands categories.

**Contents should include:**

- Task-specific guidance and instructions
- Domain expertise prompts
- Workflow optimization guides
- Ad-hoc solutions and patterns

See [prompts/README.md](prompts/README.md) for details.

### scripts/

Setup and configuration scripts for initializing the AI environment.

**Available scripts:**

- `symlink-agents.sh` - Creates symlinks for agent configurations (also prepends global settings)
- `symlink-skills.sh` - Creates symlinks for shared skills
- `symlink-commands.sh` - Creates symlinks for custom commands
- `symlink-subagents.sh` - Creates symlinks for custom subagents

All scripts use a shared utility module (`_symlink-utils.sh`) that provides intelligent symlink creation. The scripts automatically back up any existing files or directories at symlink destinations by renaming them with a `.old` extension before creating the new symlinks.

## Setup

To configure your AI environment and create symlinks for all resources:

```bash
make symlinks
```

This runs all setup scripts and makes all agent configurations, skills, commands, and subagents available to your AI agents.

### Backup Behavior

When running setup commands, if a file or directory already exists at a symlink destination:

- **Existing regular files or directories** are backed up with a `.old` extension (e.g., `~/.claude/CLAUDE.md` → `~/.claude/CLAUDE.md.old`)
- **Existing symlinks** are removed and replaced with the new symlink

This ensures you never lose data while maintaining clean symlink management.

### Individual Setup Commands

```bash
make symlink-agents       # Setup agent configurations
make symlink-skills       # Setup skills
make symlink-commands     # Setup commands
make symlink-subagents    # Setup subagents
make help                 # Show all available commands
```

## Usage

After running `make symlinks`, each agent will have access to:

- Global configuration
- Agent-specific configuration
- Shared skills
- Available commands
- Subagents for delegation
- Custom prompts

Reference the individual README files in each directory for specific usage instructions:

- [agents/README.md](agents/README.md) - Agent configuration details
- [prompts/README.md](prompts/README.md) - Custom prompt guidelines

## Getting Started

1. Clone this repository
2. Review the folder contents and README files
3. Run `make symlinks` to set up all configurations
4. Begin using agents with access to skills, commands, and subagents
5. Add new skills, commands, prompts, or subagents as needed

## Contributing

When adding new resources:

- Place them in the appropriate folder (skills, commands, subagents, or prompts)
- Follow the naming conventions established in each directory
- Update the relevant README files with documentation
- Test that symlinks and configurations work correctly

## Disclaimer

**Please note:** Content in this project is likely generated using AI language models. While efforts have been made to ensure quality and accuracy, AI-generated content can contain errors, outdated information, or unintended biases.

**Use at your own risk.** Always:

- Review AI-generated content before using it in production
- Test configurations and commands thoroughly
- Verify information against authoritative sources
- Consider the limitations and potential issues of AI-generated code and instructions
- Take responsibility for any issues that may arise from using this project

The creators and maintainers assume no liability for problems caused by following instructions or using resources from this repository.
