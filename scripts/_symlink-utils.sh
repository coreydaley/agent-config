#!/bin/bash

################################################################################
# Shared Utilities for Symlink Scripts
#
# Purpose: Provides common functions and utilities for symlink management
#
# Functions:
#   create_symlink() - Creates symlinks with automatic backup of existing files
#
################################################################################

# Helper function to create symlink, backing up existing files/folders
create_symlink() {
    local source="$1"
    local target="$2"

    # If target exists and is not a symlink, back it up
    if [[ -e "$target" ]] || [[ -L "$target" ]]; then
        if [[ ! -L "$target" ]]; then
            # It's a regular file or directory, not a symlink
            local backup="${target}.old"
            echo "Backing up existing file/folder: $target -> $backup"
            mv "$target" "$backup"
        else
            # It's already a symlink, remove it
            rm "$target"
        fi
    fi

    # Create the symlink
    ln -sf "$source" "$target"
}
