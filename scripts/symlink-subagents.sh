#!/bin/bash

################################################################################
# Script: symlink-subagents.sh
#
# Purpose: Creates symlinks for AI subagents configuration from the
# artificial-intelligence repository to the user's home directory.
#
# Description:
#   This script sets up symlinks for subagents data for supported AI agents.
#   Source: subagents/ directory (superset frontmatter format)
#   Supported agents and targets:
#     - Claude:  ~/.claude/agents/  (.md format, directly compatible)
#     - Gemini:  ~/.gemini/agents/  (.md with YAML frontmatter; requires tools: field)
#   Skipped agents:
#     - Codex:   no native subagents support
#     - Copilot: requires .agent.md extension (P1: generate-copilot-subagents.sh)
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
# shellcheck source=./utils.sh
source "${SCRIPT_DIR}/utils.sh"

# Get the root directory of the project
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Loop through all available agents in the list
# Claude: fully compatible with subagents/ format
echo "Creating symlinks for agent subagents: claude"
ensure_dir "$HOME/.claude"
create_symlink "$ROOT_DIR/subagents" "$HOME/.claude/agents"

# Gemini: compatible with subagents/ format; subagent files must include a 'tools:' frontmatter field
echo "Creating symlinks for agent subagents: gemini"
ensure_dir "$HOME/.gemini"
create_symlink "$ROOT_DIR/subagents" "$HOME/.gemini/agents"

# Codex: no native subagents support
echo "Skipping subagents for codex: no native subagents support"

# Copilot: requires .agent.md extension — use make generate-copilot-subagents (P1)
echo "Skipping subagents for copilot: requires .agent.md extension (P1: generate-copilot-subagents.sh)"
