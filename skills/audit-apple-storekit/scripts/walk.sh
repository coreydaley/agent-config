#!/usr/bin/env bash
# Thin wrapper around lib/graph_walker.py that hardcodes this skill's
# graph.dot, so node prose can be terse:
#
#   scripts/walk.sh transition --from compute_diff --to review --state $STATE
#
# Pass --state explicitly. State path is per-run, owned by the skill, not
# the walker.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LIB_DIR="$(cd "$SKILL_DIR/../../lib" && pwd)"
WALKER="$LIB_DIR/graph_walker.py"
GRAPH="$SKILL_DIR/graph.dot"

if [ "$#" -eq 0 ]; then
  python3 "$WALKER" --help
  exit 0
fi

CMD="$1"
shift

case "$CMD" in
  init)
    # Inject --graph if the caller didn't pass one.
    HAS_GRAPH=0
    for arg in "$@"; do
      if [ "$arg" = "--graph" ]; then HAS_GRAPH=1; break; fi
    done
    if [ "$HAS_GRAPH" -eq 0 ]; then
      exec python3 "$WALKER" init --graph "$GRAPH" "$@"
    else
      exec python3 "$WALKER" init "$@"
    fi
    ;;
  *)
    exec python3 "$WALKER" "$CMD" "$@"
    ;;
esac
