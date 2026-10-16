#!/usr/bin/env bash

################################################################################
# Script: setup-hooks.sh
#
# Purpose: Installs git hooks for this repository.
#
#   pre-commit  — blocked file extensions, risky large files, secret scanning,
#                 personal-info check on the staged lines
#   pre-push    — full-history secret scan (gitleaks detect) + personal-info
#                 check across every tracked file
#
# Also creates an empty private denylist for the personal-info check at
# ${XDG_CONFIG_HOME:-~/.config}/agent-config/denylist (outside the repo).
#
# Requires: gitleaks (brew install gitleaks)
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

# --- Personal / embarrassing info (generic patterns + private denylist) ---
python3 -I scripts/check-personal-info.py --staged || ERRORS=$((ERRORS + 1))


if [ "$ERRORS" -gt 0 ]; then
    exit 1
fi
EOF
chmod +x "$HOOKS_DIR/pre-commit"
echo "Installed: pre-commit"

cat > "$HOOKS_DIR/pre-push" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
gitleaks detect
python3 -I scripts/check-personal-info.py --all
EOF
chmod +x "$HOOKS_DIR/pre-push"
echo "Installed: pre-push"

DENYLIST="${AGENT_CONFIG_DENYLIST:-${XDG_CONFIG_HOME:-$HOME/.config}/agent-config/denylist}"
if [[ ! -f "$DENYLIST" ]]; then
    mkdir -p "$(dirname "$DENYLIST")"
    cat > "$DENYLIST" <<'EOF'
# Private denylist for agent-config's personal-info check. NEVER commit this.
# One case-insensitive regex per line; a match blocks the commit/push.
# Examples: family names, employer, home address, salary figures, codenames.
EOF
    chmod 600 "$DENYLIST"
    echo "Created private denylist: $DENYLIST (add your own patterns)"
fi
