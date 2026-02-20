# Agents Configuration

This directory contains configuration files for three AI agents: Claude, Codex, and Copilot.

## Directory Contents

```
agents/
├── README.md           # This file
├── GLOBAL.md           # Shared configuration available to all agents
├── claude/
│   └── CLAUDE.md       # Claude-specific configuration and instructions
├── codex/
│   └── CODEX.md        # Codex-specific configuration and instructions
└── copilot/
    └── COPILOT.md      # Copilot-specific configuration and instructions
```

## Files

### GLOBAL.md

Contains shared configuration, instructions, and context that are available to all agents. During setup, this content is automatically merged into each agent's specific configuration file.

### Agent-Specific Configuration Files

- **CLAUDE.md** - Configuration, instructions, and context specific to Claude
- **CODEX.md** - Configuration, instructions, and context specific to Codex
- **COPILOT.md** - Configuration, instructions, and context specific to Copilot

Each agent file contains:

- Custom instructions and behavior guidelines
- Agent-specific capabilities and limitations
- Tools and resources available to that agent
- Contextual information and best practices

## Setup

To set up symlinks for the agent configuration files, run:

```bash
make symlink-agents
```

### What This Command Does

The `make symlink-agents` command:

1. Converts agent names to uppercase (claude → CLAUDE, etc.)
2. Checks if GLOBAL.md contents already exist in each agent's markdown file
3. Prepends GLOBAL.md contents to agent markdown files if not already present
4. Creates symlinks as follows:
   - `~/.claude/CLAUDE.md` → `agents/claude/CLAUDE.md`
   - `~/.codex/CODEX.md` → `agents/codex/CODEX.md`
   - `~/.copilot/copilot-instructions.md` → `agents/copilot/COPILOT.md`

## Other Make Commands

```bash
make symlink-skills       # Set up skills configuration symlinks
make symlink-subagents    # Set up subagents configuration symlinks
make all                  # Run all symlink setup commands at once
make help                 # Show all available commands
```

## After Setup

Once symlinks are configured, each agent will have access to:

- Global configuration: `~/.{agent}/GLOBAL.md`
- Agent-specific configuration: `~/.{agent}/{AGENT_NAME}.md` (or `copilot-instructions.md` for Copilot)
- Shared skills directory: `~/.{agent}/skills`
- Subagents directory: `~/.{agent}/agents`

## For More Information

See [scripts/symlink-agents.sh](../scripts/symlink-agents.sh) for implementation details.
