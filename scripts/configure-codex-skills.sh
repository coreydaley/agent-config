#!/bin/bash

################################################################################
# Script: configure-codex-skills.sh
#
# Purpose: Registers skills from this repo with Codex by appending
#          [[skills.config]] entries to ~/.codex/config.toml.
#
# Description:
#   Codex does not support a global skills directory symlink. Instead, skills
#   must be registered via entries in ~/.codex/config.toml. This script reads
#   each skill directory under skills/ and appends a [[skills.config]] entry
#   for any that are not already registered.
#
#   This script modifies ~/.codex/config.toml. It backs up the file to
#   ~/.codex/config.toml.old before making any changes.
#
# Usage: ./scripts/configure-codex-skills.sh
#        make configure-codex-skills
#
# Behavior:
#   - Creates ~/.codex/config.toml if it does not exist
#   - Backs up existing config to ~/.codex/config.toml.old before any changes
#   - Appends [[skills.config]] entries for skills not already registered
#   - Idempotent: re-running does not add duplicate entries
#
# Requirements:
#   - Bash 3.2+
#   - Standard Unix utilities (grep, cp, printf)
#   - Write access to ~/.codex/
#
# Note: Run this separately from make all. It is NOT part of the default
#       build because it modifies a user config file.
#
################################################################################

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source shared symlink utilities
# shellcheck source=./utils.sh
source "${SCRIPT_DIR}/utils.sh"

# Get the root directory of the project
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

SKILLS_DIR="$ROOT_DIR/skills"
CONFIG_FILE="$HOME/.codex/config.toml"

if [[ ! -d "$SKILLS_DIR" ]]; then
    echo "ERROR: skills/ directory not found at $SKILLS_DIR" >&2
    exit 1
fi

# Ensure ~/.codex/ exists
ensure_dir "$HOME/.codex"

# Create config.toml if it doesn't exist
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Creating $CONFIG_FILE"
    touch "$CONFIG_FILE"
fi

# Back up config before any changes
cp "$CONFIG_FILE" "${CONFIG_FILE}.old"
echo "Backed up $CONFIG_FILE to ${CONFIG_FILE}.old"

ADDED=0
SKIPPED=0

for SKILL_DIR in "$SKILLS_DIR"/*/; do
    [[ -d "$SKILL_DIR" ]] || continue

    SKILL_NAME=$(basename "$SKILL_DIR")
    SKILL_PATH="$SKILL_DIR"

    # Check if this skill path is already registered
    if grep -qF "$SKILL_PATH" "$CONFIG_FILE" 2>/dev/null; then
        echo "Skipping (already registered): $SKILL_NAME"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    echo "Registering skill: $SKILL_NAME"
    {
        printf '\n[[skills.config]]\n'
        printf 'name = "%s"\n' "$SKILL_NAME"
        printf 'path = "%s"\n' "$SKILL_PATH"
        printf 'enabled = true\n'
    } >> "$CONFIG_FILE"
    ADDED=$((ADDED + 1))
done

echo "Done: $ADDED registered, $SKIPPED already registered"
