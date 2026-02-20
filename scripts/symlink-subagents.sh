#!/bin/bash

################################################################################
# Script: symlink-subagents.sh
#
# Purpose: Creates symlinks for AI subagents configuration from the
# artificial-intelligence repository to the user's home directory.
#
# Description:
#   This script sets up symlinks for subagents data for three AI agents
#   (Claude, Codex, Copilot) by linking the agents directory to each
#   agent's home folder (~/.claude/agents, ~/.codex/agents, ~/.copilot/agents).
#   This allows the agents to access subagents and related data from a centralized location.
#
# Usage: ./scripts/symlink-subagents.sh
#
# Behavior:
#   - Backs up existing files/folders at symlink destinations by renaming to .old
#   - Creates symlinks for subagents directory to each agent's home folder
#
# Requirements:
#   - Bash 3.2+
#   - Standard Unix utilities (ln, mv, rm)
#   - Write access to home directory
#
################################################################################

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source shared symlink utilities
# shellcheck source=./_symlink-utils.sh
source "${SCRIPT_DIR}/_symlink-utils.sh"

# Get the root directory of the project
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Loop through all available agents in the list
for AGENT in claude codex copilot; do
    echo "Creating symlinks for agent subagents: $AGENT"
    create_symlink "$ROOT_DIR/agents" "$HOME/.${AGENT}/agents"
done
