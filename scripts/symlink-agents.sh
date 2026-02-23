#!/bin/bash

################################################################################
# Script: symlink-agents.sh
#
# Purpose: Creates symlinks for each AI agent config in the user's home
# directory.
#
# Description:
#   This script sets up symlinks for three AI agents (Claude, Codex, Copilot)
#   by linking each agent's final markdown file to its expected destination:
#     - Claude:  ~/.claude/CLAUDE.md
#     - Codex:   ~/.codex/CODEX.md
#     - Copilot: ~/.copilot/copilot-instructions.md
#   It does not generate merged files; use generate-agent-files.sh first.
#
# Usage: ./scripts/symlink-agents.sh
#
# Behavior:
#   - Converts agent names to uppercase using tr for cross-shell compatibility
#   - Backs up existing files/folders at symlink destinations by renaming to .old
#   - Creates symlinks for Claude to ~/.claude/CLAUDE.md
#   - Creates symlinks for Codex to ~/.codex/CODEX.md
#   - Creates symlinks for Copilot to ~/.copilot/copilot-instructions.md
#
# Requirements:
#   - Bash 3.2+ (for [[ ]] support)
#   - Standard Unix utilities (ln, tr, mv, rm, echo)
#   - Write access to home directory
#   - Generated agent files in agents/<agent>/<AGENT>.md
#
################################################################################

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source shared symlink utilities
# shellcheck source=./utils.sh
source "${SCRIPT_DIR}/utils.sh"

# Get the root directory of the project
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Get the agents directory
AGENTS_DIR="$ROOT_DIR/agents"

# Loop through all available agents in the list
for AGENT in claude codex copilot; do
    # Convert agent name to uppercase using tr for compatibility
    AGENT_UPPER=$(echo "$AGENT" | tr '[:lower:]' '[:upper:]')
    # Create a symlink for the agent's markdown file
    echo "Creating symlinks for agent: $AGENT"
    if [[ "$AGENT" == "claude" ]]; then
        create_symlink "$AGENTS_DIR/${AGENT}/${AGENT_UPPER}.md" "$HOME/.${AGENT}/CLAUDE.md"
    elif [[ "$AGENT" == "codex" ]]; then
        create_symlink "$AGENTS_DIR/${AGENT}/${AGENT_UPPER}.md" "$HOME/.${AGENT}/CODEX.md"
    elif [[ "$AGENT" == "copilot" ]]; then
        create_symlink "$AGENTS_DIR/${AGENT}/${AGENT_UPPER}.md" "$HOME/.${AGENT}/copilot-instructions.md"
    fi
done
