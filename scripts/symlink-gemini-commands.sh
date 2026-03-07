#!/bin/bash

################################################################################
# Script: symlink-gemini-commands.sh
#
# Purpose: Creates a symlink for Gemini CLI commands from build/gemini-commands/
#          to ~/.gemini/commands/.
#
# Description:
#   Gemini CLI reads commands from ~/.gemini/commands/ as .toml files.
#   This script symlinks the auto-generated build/gemini-commands/ directory
#   to that location. Run generate-gemini-commands.sh first to produce the
#   TOML files.
#
# Usage: ./scripts/symlink-gemini-commands.sh
#
# Requirements:
#   - Bash 3.2+
#   - build/gemini-commands/ must exist (run make generate-gemini-commands first)
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

BUILD_DIR="$ROOT_DIR/build/gemini-commands"

if [[ ! -d "$BUILD_DIR" ]]; then
    echo "ERROR: $BUILD_DIR does not exist. Run 'make generate-gemini-commands' first." >&2
    exit 1
fi

echo "Creating symlinks for gemini commands"
ensure_dir "$HOME/.gemini"
create_symlink "$BUILD_DIR" "$HOME/.gemini/commands"
