#!/bin/bash

################################################################################
# Script: symlink-agents.sh
#
# Purpose: Creates symlinks for AI agent configuration files and ensures
# global settings are available in agent-specific files.
#
# Description:
#   This script sets up symlinks for three AI agents (Claude, Codex, Copilot)
#   by creating directories in the home folder (~/.claude, ~/.codex, ~/.copilot)
#   and linking the agent's markdown files, configuration data, and global
#   settings to them. It also ensures that GLOBAL.md contents are available
#   in each agent's markdown file by prepending the global settings if needed.
#   This allows the agents to access both their respective configuration and
#   global settings from a centralized location.
#
# Usage: ./scripts/symlink-agents.sh
#
# Behavior:
#   - Converts agent names to uppercase using tr for cross-shell compatibility
#   - Checks if GLOBAL.md contents exist in each agent's markdown file
#   - Prepends GLOBAL.md contents to agent markdown files if not already present
#   - Backs up existing files/folders at symlink destinations by renaming to .old
#   - Creates symlinks for Claude to ~/.claude/CLAUDE.md
#   - Creates symlinks for Codex to ~/.codex/CODEX.md
#   - Creates symlinks for Copilot to ~/.copilot/copilot-instructions.md
#
# Requirements:
#   - Bash 3.2+ (for [[ ]] support)
#   - Standard Unix utilities (ln, tr, grep, cat, head, mv, echo)
#   - Write access to home directory and agents configuration files
#
################################################################################

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source shared symlink utilities
# shellcheck source=./_symlink-utils.sh
source "${SCRIPT_DIR}/_symlink-utils.sh"

# Get the root directory of the project
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Get the agents directory
AGENTS_DIR="$ROOT_DIR/agents"

# Loop through all available agents in the list
for AGENT in claude codex copilot; do
    # Convert agent name to uppercase using tr for compatibility
    AGENT_UPPER=$(echo "$AGENT" | tr '[:lower:]' '[:upper:]')
    # Check if GLOBAL.md contents are already in the agent's markdown file
    # if not, insert them at the beginning of the file
    AGENT_MD_FILE="$AGENTS_DIR/${AGENT}/${AGENT_UPPER}.md"
    if ! grep -q "$(head -1 "$AGENTS_DIR/GLOBAL.md")" "$AGENT_MD_FILE"; then
        # GLOBAL.md contents not found, insert at the beginning
        echo "Inserting GLOBAL.md contents into $AGENT_MD_FILE"
        cat "$AGENTS_DIR/GLOBAL.md" "$AGENT_MD_FILE" > "$AGENT_MD_FILE.tmp"
        mv "$AGENT_MD_FILE.tmp" "$AGENT_MD_FILE"
    fi
    echo "Creating symlinks for agent: $AGENT"
    # Create a symlink for the agent's markdown file

    if [[ "$AGENT" == "claude" ]]; then
        create_symlink "$AGENTS_DIR/${AGENT}/${AGENT_UPPER}.md" "$HOME/.${AGENT}/CLAUDE.md"
    elif [[ "$AGENT" == "codex" ]]; then
        create_symlink "$AGENTS_DIR/${AGENT}/${AGENT_UPPER}.md" "$HOME/.${AGENT}/CODEX.md"
    elif [[ "$AGENT" == "copilot" ]]; then
        create_symlink "$AGENTS_DIR/${AGENT}/${AGENT_UPPER}.md" "$HOME/.${AGENT}/copilot-instructions.md"
    fi
done
