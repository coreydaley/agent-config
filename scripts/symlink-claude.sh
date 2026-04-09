#!/bin/bash

################################################################################
# Script: symlink-claude.sh
#
# Purpose: Creates symlinks from this repository into ~/.claude/
#
# Targets:
#   - CLAUDE.md   → ~/.claude/CLAUDE.md
#   - commands/   → ~/.claude/commands/
#   - skills/     → ~/.claude/skills/
#   - subagents/  → ~/.claude/agents/
#
# Usage: ./scripts/symlink-claude.sh
#
################################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

ensure_dir() {
    local dir="$1"
    [[ ! -d "$dir" ]] && mkdir -p "$dir"
}

create_symlink() {
    local source="$1"
    local target="$2"
    if [[ -e "$target" ]] || [[ -L "$target" ]]; then
        if [[ ! -L "$target" ]]; then
            mv "$target" "${target}.old"
        else
            rm "$target"
        fi
    fi
    ln -sf "$source" "$target"
}

ensure_dir "$HOME/.claude"

create_symlink "$ROOT_DIR/CLAUDE.md"   "$HOME/.claude/CLAUDE.md"
create_symlink "$ROOT_DIR/commands"    "$HOME/.claude/commands"
create_symlink "$ROOT_DIR/skills"      "$HOME/.claude/skills"
create_symlink "$ROOT_DIR/subagents"   "$HOME/.claude/agents"
