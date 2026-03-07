#!/bin/bash

################################################################################
# Script: symlink-skills.sh
#
# Purpose: Creates symlinks for AI skills configuration from the
# artificial-intelligence repository to the user's home directory.
#
# Description:
#   This script sets up symlinks for skills data for supported AI agents.
#   Only agents with a standard global skills directory convention are supported:
#     - Claude:  ~/.claude/skills/
#     - Copilot: ~/.copilot/skills/
#   Codex and Gemini are explicitly skipped (no supported global skills directory).
#
# Usage: ./scripts/symlink-skills.sh
#
# Behavior:
#   - Backs up existing files/folders at symlink destinations by renaming to .old
#   - Creates symlinks for shared skills to each agent's home folder
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

# Claude and Copilot: both support a standard ~/.agent/skills/ directory
for AGENT in claude copilot; do
    echo "Creating symlinks for agent skills: $AGENT"
    ensure_dir "$HOME/.${AGENT}"
    create_symlink "$ROOT_DIR/skills" "$HOME/.${AGENT}/skills"
done

# Codex: no standard global skills directory — registered via ~/.codex/config.toml by configure-codex-skills.sh
echo "Skipping skills for codex: no standard global skills directory (handled by configure-codex-skills)"

# Gemini: no skills/ directory convention — reference skills via @imports in GEMINI.md
echo "Skipping skills for gemini: no skills/ directory convention (use @file.md imports in GEMINI.md)"
