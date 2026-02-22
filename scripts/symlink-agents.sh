#!/bin/bash

################################################################################
# Script: symlink-agents.sh
#
# Purpose: Builds merged agent instruction files and creates symlinks for each
# AI agent config in the user's home directory.
#
# Description:
#   This script sets up symlinks for three AI agents (Claude, Codex, Copilot)
#   by creating directories in the home folder (~/.claude, ~/.codex, ~/.copilot)
#   and linking each agent's final markdown file to its expected destination.
#   For each agent, it creates/overwrites a merged file by concatenating:
#     1) agents/_GLOBAL.md
#     2) agents/<agent>/_<AGENT>.md
#   Output files are written to agents/<agent>/<AGENT>.md and then symlinked.
#
# Usage: ./scripts/symlink-agents.sh
#
# Behavior:
#   - Converts agent names to uppercase using tr for cross-shell compatibility
#   - Rebuilds merged markdown files for each agent on every run
#   - Writes merged content to agents/<agent>/<AGENT>.md
#   - Backs up existing files/folders at symlink destinations by renaming to .old
#   - Creates symlinks for Claude to ~/.claude/CLAUDE.md
#   - Creates symlinks for Codex to ~/.codex/CODEX.md
#   - Creates symlinks for Copilot to ~/.copilot/copilot-instructions.md
#
# Requirements:
#   - Bash 3.2+ (for [[ ]] support)
#   - Standard Unix utilities (ln, tr, cat, mv, echo)
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

    # Concatenate _GLOBAL.md and the _agent-specific markdown file into a new file
    echo "Combining global settings with agent-specific settings for: $AGENT"
    cat "${AGENTS_DIR}/_GLOBAL.md" "${AGENTS_DIR}/${AGENT}/_${AGENT_UPPER}.md" > "${AGENTS_DIR}/${AGENT}/${AGENT_UPPER}.md"

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
