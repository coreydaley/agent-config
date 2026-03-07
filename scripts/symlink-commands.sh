#!/bin/bash

################################################################################
# Script: symlink-commands.sh
#
# Purpose: Creates symlinks for AI commands configuration from the
# artificial-intelligence repository to the user's home directory.
#
# Description:
#   This script sets up symlinks for commands data for supported AI agents.
#   Each agent uses a different directory name for user-defined prompts/commands:
#     - Claude: ~/.claude/commands  (Markdown .md files)
#     - Codex:  ~/.codex/prompts   (Markdown .md files, loaded as /prompts: slash commands)
#   Note: GitHub Copilot CLI does not support custom commands.
#   Note: Gemini CLI uses TOML format and is not compatible with this commands directory.
#
# Usage: ./scripts/symlink-commands.sh
#
# Behavior:
#   - Backs up existing files/folders at symlink destinations by renaming to .old
#   - Creates symlinks for commands directory to each agent's home folder
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

# Claude: commands/ directory contains Markdown slash commands
echo "Creating symlinks for agent commands: claude"
ensure_dir "$HOME/.claude"
create_symlink "$ROOT_DIR/commands" "$HOME/.claude/commands"

# Codex: same Markdown files but loaded from the prompts/ directory
echo "Creating symlinks for agent commands: codex"
ensure_dir "$HOME/.codex"
create_symlink "$ROOT_DIR/commands" "$HOME/.codex/prompts"

# Gemini: TOML format — symlink is handled by symlink-gemini-commands.sh
# (called separately as part of the symlinks target after generate-gemini-commands)
echo "Skipping gemini commands here: handled by symlink-gemini-commands.sh after TOML conversion"

# Copilot: custom commands not supported
echo "Skipping commands for copilot: custom commands not supported by Copilot CLI"
