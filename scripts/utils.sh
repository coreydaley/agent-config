#!/bin/bash

################################################################################
# Shared Script Utilities
#
# Purpose: Provides common reusable functions for repository scripts
#
# Functions:
#   create_symlink() - Creates symlinks with automatic backup of existing files
#
################################################################################

# Creates a symlink while safely handling existing targets.
create_symlink() {
    local source="$1"
    local target="$2"

    # If target exists and is not a symlink, back it up
    if [[ -e "$target" ]] || [[ -L "$target" ]]; then
        if [[ ! -L "$target" ]]; then
            local backup="${target}.old"
            echo "Backing up existing file/folder: $target -> $backup"
            mv "$target" "$backup"
        else
            rm "$target"
        fi
    fi

    ln -sf "$source" "$target"
}
