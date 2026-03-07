# Agents Configuration

This directory contains configuration files for four AI agents: Claude, Codex, Copilot, and Gemini.

The agent config that gets symlinked is generated from two source files:

1. `_GLOBAL.md` (shared instructions)
2. `_<AGENT_NAME>.md` (agent-specific instructions)

These are concatenated to produce `<AGENT_NAME>.md`, which is the file used by symlinks.

## Directory Contents

```text
agents/
├── README.md           # This file
├── _GLOBAL.md          # Shared source content for all agents
├── claude/
│   ├── _CLAUDE.md      # Claude-specific source content
│   └── CLAUDE.md       # Generated merged file (_GLOBAL + _CLAUDE)
├── codex/
│   ├── _CODEX.md       # Codex-specific source content
│   └── CODEX.md        # Generated merged file (_GLOBAL + _CODEX)
├── copilot/
│   ├── _COPILOT.md     # Copilot-specific source content
│   └── COPILOT.md      # Generated merged file (_GLOBAL + _COPILOT)
└── gemini/
    ├── _GEMINI.md      # Gemini-specific source content
    └── GEMINI.md       # Generated merged file (_GLOBAL + _GEMINI)
```

## Files

### _GLOBAL.md

Contains shared configuration, instructions, and context that are included in every generated agent file.

### Agent-Specific Configuration Files

- **_<AGENT_NAME>.md** (for example `_CLAUDE.md`) contains agent-specific source content.
- **<AGENT_NAME>.md** (for example `CLAUDE.md`) is the generated output used by symlinks.

Generation pattern:

- `_GLOBAL.md` + `claude/_CLAUDE.md` → `claude/CLAUDE.md`
- `_GLOBAL.md` + `codex/_CODEX.md` → `codex/CODEX.md`
- `_GLOBAL.md` + `copilot/_COPILOT.md` → `copilot/COPILOT.md`
- `_GLOBAL.md` + `gemini/_GEMINI.md` → `gemini/GEMINI.md`

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
2. Rebuilds each generated agent file by concatenating `_GLOBAL.md` with the corresponding `_<AGENT_NAME>.md`
3. Creates symlinks as follows:
   - `~/.claude/CLAUDE.md` → `agents/claude/CLAUDE.md`
   - `~/.codex/AGENTS.md` → `agents/codex/CODEX.md`
   - `~/.copilot/copilot-instructions.md` → `agents/copilot/COPILOT.md`
   - `~/.gemini/GEMINI.md` → `agents/gemini/GEMINI.md`

## Other Make Commands

```bash
make symlink-skills       # Set up skills configuration symlinks
make symlink-subagents    # Set up subagents configuration symlinks
make all                  # Run all symlink setup commands at once
make help                 # Show all available commands
```

## After Setup

Once symlinks are configured, each agent has:

| | Claude | Codex | Copilot | Gemini |
|---|---|---|---|---|
| **Config** | `~/.claude/CLAUDE.md` | `~/.codex/AGENTS.md` | `~/.copilot/copilot-instructions.md` | `~/.gemini/GEMINI.md` |
| **Skills** | `~/.claude/skills/` | ❌ skipped | `~/.copilot/skills/` | ❌ skipped |
| **Commands** | `~/.claude/commands/` | `~/.codex/prompts/` | ❌ skipped | `~/.gemini/commands/` (.toml) |
| **Subagents** | `~/.claude/agents/` | ❌ skipped | ⚠️ P1 | `~/.gemini/agents/` |

## For More Information

See [scripts/symlink-agents.sh](../scripts/symlink-agents.sh) for implementation details.
