#!/bin/bash

################################################################################
# Script: setup-hooks.sh
#
# Purpose: Installs git pre-commit hooks for this repository.
#
# Requires: gitleaks (brew install gitleaks)
#
# Usage: ./scripts/setup-hooks.sh
#
################################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
HOOK="$ROOT_DIR/.git/hooks/pre-commit"

if ! command -v gitleaks &>/dev/null; then
    echo "Error: gitleaks is not installed. Run: brew install gitleaks" >&2
    exit 1
fi

cat > "$HOOK" <<'EOF'
#!/bin/bash
gitleaks protect --staged --config .gitleaks.toml
EOF

chmod +x "$HOOK"
echo "Pre-commit hook installed."
