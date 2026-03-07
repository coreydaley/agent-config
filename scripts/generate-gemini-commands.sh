#!/bin/bash

################################################################################
# Script: generate-gemini-commands.sh
#
# Purpose: Converts commands/*.md files to Gemini CLI-compatible TOML format.
#
# Description:
#   Gemini CLI requires commands in ~/.gemini/commands/ as .toml files with
#   'description' and 'prompt' fields. This script reads each Markdown command
#   file, strips YAML frontmatter, extracts the 'description' field, and
#   writes a corresponding .toml file to build/gemini-commands/.
#
# Conversion spec:
#   Input:  commands/<name>.md (YAML frontmatter + Markdown body)
#   Output: build/gemini-commands/<name>.toml
#
#   Frontmatter 'description:' field → TOML 'description = "..."'
#   Markdown body (after closing ---) → TOML 'prompt = """..."""'
#
# Constraints:
#   - Only single-line YAML values are supported
#   - 'description:' must exist; script fails loudly if absent
#   - Only 'description:' is extracted; all other frontmatter fields are stripped
#   - Claude-specific fields (disable-model-invocation, allowed-tools) are stripped
#   - Known limitation: embedded triple-quotes (""") in body may break TOML output
#
# Usage: ./scripts/generate-gemini-commands.sh
#
# Requirements:
#   - Bash 3.2+
#   - Standard Unix utilities (awk, mkdir, echo)
#
################################################################################

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get the root directory of the project
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

COMMANDS_DIR="$ROOT_DIR/commands"
OUTPUT_DIR="$ROOT_DIR/build/gemini-commands"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Track conversion results
CONVERTED=0
FAILED=0

for MD_FILE in "$COMMANDS_DIR"/*.md; do
    [[ -f "$MD_FILE" ]] || continue

    BASENAME=$(basename "$MD_FILE" .md)
    TOML_FILE="$OUTPUT_DIR/${BASENAME}.toml"

    echo "Converting: $BASENAME.md -> $BASENAME.toml"

    # Extract description from YAML frontmatter using awk
    DESCRIPTION=$(awk '
        /^---$/ { if (in_front == 0) { in_front = 1; next } else { exit } }
        in_front && /^description:/ {
            sub(/^description:[[:space:]]*/, "")
            print
            exit
        }
    ' "$MD_FILE")

    if [[ -z "$DESCRIPTION" ]]; then
        echo "ERROR: No 'description:' field found in frontmatter of $BASENAME.md" >&2
        FAILED=$((FAILED + 1))
        continue
    fi

    # Extract the Markdown body (everything after the second ---)
    BODY=$(awk '
        /^---$/ { count++; if (count == 2) { found = 1; next } }
        found { print }
    ' "$MD_FILE")

    # Write the TOML file
    {
        printf 'description = "%s"\n' "$DESCRIPTION"
        printf 'prompt = """\n'
        printf '%s\n' "$BODY"
        printf '"""\n'
    } > "$TOML_FILE"

    CONVERTED=$((CONVERTED + 1))
done

echo "Done: $CONVERTED converted, $FAILED failed"

if [[ $FAILED -gt 0 ]]; then
    exit 1
fi
