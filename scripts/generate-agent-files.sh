#!/bin/bash

################################################################################
# Script: generate-agent-files.sh
#
# Purpose: Builds merged agent instruction files for each AI agent.
#
# Description:
#   This script generates merged markdown files for four AI agents
#   (Claude, Codex, Copilot, Gemini). For each agent, it creates/overwrites a merged
#   file by concatenating:
#     1) agents/_GLOBAL.md
#     2) agents/<agent>/_<AGENT>.md
#   Output files are written to agents/<agent>/<AGENT>.md.
#
# Usage: ./scripts/generate-agent-files.sh
#
# Behavior:
#   - Converts agent names to uppercase using tr for cross-shell compatibility
#   - Rebuilds merged markdown files for each agent on every run
#   - Writes merged content to agents/<agent>/<AGENT>.md
#
# Requirements:
#   - Bash 3.2+ (for [[ ]] support)
#   - Standard Unix utilities (tr, cat, echo)
#   - Write access to agents configuration files
#
################################################################################

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source shared utilities
# shellcheck source=./utils.sh
source "${SCRIPT_DIR}/utils.sh"

# Get the root directory of the project
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Get the agents directory
AGENTS_DIR="$ROOT_DIR/agents"

# Loop through all available agents in the list
for AGENT in claude codex copilot gemini; do
    # Convert agent name to uppercase using tr for compatibility
    AGENT_UPPER=$(echo "$AGENT" | tr '[:lower:]' '[:upper:]')

    # Fail explicitly if source files are missing
    if [[ ! -f "${AGENTS_DIR}/_GLOBAL.md" ]]; then
        echo "ERROR: Missing required source file: ${AGENTS_DIR}/_GLOBAL.md" >&2
        exit 1
    fi
    if [[ ! -f "${AGENTS_DIR}/${AGENT}/_${AGENT_UPPER}.md" ]]; then
        echo "ERROR: Missing required source file: ${AGENTS_DIR}/${AGENT}/_${AGENT_UPPER}.md" >&2
        exit 1
    fi

    # Concatenate _GLOBAL.md and the _agent-specific markdown file into a new file
    echo "Combining global settings with agent-specific settings for: $AGENT"
    cat "${AGENTS_DIR}/_GLOBAL.md" "${AGENTS_DIR}/${AGENT}/_${AGENT_UPPER}.md" > "${AGENTS_DIR}/${AGENT}/${AGENT_UPPER}.md"
done
