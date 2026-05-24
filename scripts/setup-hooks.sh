#!/usr/bin/env bash

################################################################################
# Script: setup-hooks.sh
#
# Purpose: Installs git hooks for this repository.
#
#   pre-commit  — blocked file extensions, risky large files, secret
#                 scanning, mermaid syntax validation
#   pre-push    — full branch history secret scan (gitleaks detect)
#
# Requires: gitleaks (brew install gitleaks)
#           mermaid-cli (brew install mermaid-cli) — provides mmdc
#
# Usage: ./scripts/setup-hooks.sh
#
################################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
HOOKS_DIR="$(git -C "$REPO_ROOT" rev-parse --git-path hooks)"

if ! command -v gitleaks &>/dev/null; then
    echo "Error: gitleaks is not installed. Run: brew install gitleaks" >&2
    exit 1
fi

if ! command -v mmdc &>/dev/null; then
    echo "Error: mmdc is not installed. Run: brew install mermaid-cli" >&2
    exit 1
fi

cat > "$HOOKS_DIR/pre-commit" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

ERRORS=0

# --- Blocked file extensions ---
# Hard block on credential/key file types regardless of content or size.
BLOCKED_PATTERN='\.(pem|key|p12|pfx|jks|keystore|p8|der|crt|cer|csr)$|^(id_rsa|id_ed25519|id_ecdsa|id_dsa)(\.pub)?$|\.env$|\.secrets$'

while IFS= read -r file; do
    if echo "$file" | grep -qiE "$BLOCKED_PATTERN"; then
        echo "BLOCKED: $file — matches blocked credential/key file pattern" >&2
        ERRORS=$((ERRORS + 1))
    fi
done < <(git diff --cached --name-only --diff-filter=ACM)

# --- Risky large file check ---
# Block archive and database file types over 1MB.
RISKY_PATTERN='\.(db|sqlite|sqlite3|sql|zip|tar|tgz|tar\.gz|tar\.bz2|tar\.xz|gz|bz2|7z|rar|dump|bak)$'
MAX_BYTES=$((1 * 1024 * 1024))  # 1MB

while IFS= read -r file; do
    if echo "$file" | grep -qiE "$RISKY_PATTERN"; then
        size=$(git cat-file -s "$(git rev-parse ":$file")" 2>/dev/null || echo 0)
        if [ "$size" -gt "$MAX_BYTES" ]; then
            echo "BLOCKED: $file — risky file type is $(( size / 1024 ))KB (limit 1MB)" >&2
            ERRORS=$((ERRORS + 1))
        fi
    fi
done < <(git diff --cached --name-only --diff-filter=ACM)

# --- Secret scanning ---
gitleaks protect --staged

# --- Mermaid syntax validation ---
# Validate any mermaid blocks in staged markdown files.
REPO_ROOT="$(git rev-parse --show-toplevel)"
MD_FILES=()
while IFS= read -r f; do
    [ -n "$f" ] && MD_FILES+=("$f")
done < <(git diff --cached --name-only --diff-filter=ACM | grep -iE '\.md$' || true)
if [ ${#MD_FILES[@]} -gt 0 ]; then
    if ! "$REPO_ROOT/scripts/lint-mermaid.py" "${MD_FILES[@]}"; then
        ERRORS=$((ERRORS + 1))
    fi
fi

if [ "$ERRORS" -gt 0 ]; then
    exit 1
fi
EOF
chmod +x "$HOOKS_DIR/pre-commit"
echo "Installed: pre-commit"

cat > "$HOOKS_DIR/pre-push" <<'EOF'
#!/usr/bin/env bash
gitleaks detect
EOF
chmod +x "$HOOKS_DIR/pre-push"
echo "Installed: pre-push"
