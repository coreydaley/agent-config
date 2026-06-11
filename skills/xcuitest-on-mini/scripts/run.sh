#!/usr/bin/env bash
#
# xcuitest-on-mini — rsync the local Apple project to the Mac mini and
# run xcodebuild test there, so XCUITest's "Automation Running" indicator
# takes over the mini's screen instead of the MBP's.
#
# Why no git: rsync maintains a file tree at the destination; xcodebuild
# doesn't need .git. No first-time clone, no drift between local and
# remote git state, less data transferred.
#
# Path mapping is identity: $(pwd) on the MBP becomes $(pwd) on the mini.
# Works because both Macs are user `corey` with `/Users/corey` home dirs.
# If you ever use a Mac with a different home layout, this breaks — flag
# at that point and add explicit local→remote mapping.

set -euo pipefail

# -----------------------------------------------------------------------
# Configuration (overridable via flags; see help)
# -----------------------------------------------------------------------

REMOTE_HOST="${XCUITEST_ON_MINI_HOST:-mac-mini.example}"
REMOTE_USER="${XCUITEST_ON_MINI_USER:-corey}"
SCHEME=""
PROJECT_PATH=""
TEST_FILTER=""
RUN_ALL=false
CI_MODE=false
PULL_XCRESULT=false

usage() {
  cat <<'EOF'
xcuitest-on-mini — run xcodebuild test on the Mac mini, stream results back

USAGE
  xcuitest-on-mini [<test-filter>] [--all] [--scheme NAME]
                   [--project PATH] [--pull-xcresult] [--help]

ARGUMENTS
  <test-filter>     Positional, optional. Passes verbatim to
                    `-only-testing:<filter>`. Examples:
                      PurrchiverUITests
                      PurrchiverUITests/PurrchiverUITests/testFoo
                      PurrchiverTests/MyTestClass
                    If omitted, defaults to `<scheme>UITests` (the
                    common convention).

FLAGS
  --all             Run every test in the scheme (no -only-testing).
  --ci              CI-parity mode: run the repo's scripts/ci-test.sh (the
                    same matrix CI runs — swift test --parallel per SPM
                    package, then app + UI). Use this as the pre-commit gate
                    when you need a mini run to actually predict CI; the
                    default xcodebuild-over-.xctestplan run is serial and
                    does not reproduce CI's per-package parallelism.
  --scheme NAME     Xcode scheme name. Default: derived from the
                    .xcodeproj basename.
  --project PATH    Path to the .xcodeproj. Default: first .xcodeproj
                    found in cwd (BFS, up to depth 3).
  --pull-xcresult   On failure, rsync the .xcresult bundle back to the
                    local repo's build/remote-ui-tests.xcresult for
                    inspection in Xcode.
  --help, -h        Print this help and exit.

ENVIRONMENT
  XCUITEST_ON_MINI_HOST   Remote hostname. Default: mac-mini.example
  XCUITEST_ON_MINI_USER   Remote SSH user. Default: corey

EXAMPLES
  # Run all UI tests (default behavior)
  xcuitest-on-mini

  # Run one specific test
  xcuitest-on-mini PurrchiverUITests/PurrchiverUITests/testSettingsCompressionTabSurfacesPresetsSection

  # Run everything in the scheme
  xcuitest-on-mini --all

  # Run a unit-test target (override the default UI test guess)
  xcuitest-on-mini PurrchiverTests

EOF
}

# -----------------------------------------------------------------------
# Arg parsing
# -----------------------------------------------------------------------

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    --all) RUN_ALL=true; shift ;;
    --ci) CI_MODE=true; shift ;;
    --scheme) SCHEME="$2"; shift 2 ;;
    --project) PROJECT_PATH="$2"; shift 2 ;;
    --pull-xcresult) PULL_XCRESULT=true; shift ;;
    --) shift; TEST_FILTER="${1:-}"; break ;;
    -*) echo "error: unknown flag: $1" >&2; usage >&2; exit 2 ;;
    *)
      if [[ -z "$TEST_FILTER" ]]; then
        TEST_FILTER="$1"
      else
        echo "error: unexpected extra positional arg: $1" >&2
        exit 2
      fi
      shift
      ;;
  esac
done

# -----------------------------------------------------------------------
# Detect project root + scheme
# -----------------------------------------------------------------------

if [[ -z "$PROJECT_PATH" ]]; then
  # Find the first .xcodeproj at depth ≤ 3 from cwd. Use -prune to skip
  # build/derived-data dirs that may contain stale .xcodeproj copies.
  PROJECT_PATH="$(find . -maxdepth 3 \
    \( -name 'build' -o -name 'DerivedData' -o -name '.build' \) -prune -o \
    -name '*.xcodeproj' -print 2>/dev/null | head -1 | sed 's|^\./||')"
  if [[ -z "$PROJECT_PATH" ]]; then
    echo "error: no .xcodeproj found under cwd. Use --project PATH." >&2
    exit 1
  fi
fi

PROJECT_PATH="$(cd "$(dirname "$PROJECT_PATH")" && pwd)/$(basename "$PROJECT_PATH")"

if [[ -z "$SCHEME" ]]; then
  SCHEME="$(basename "$PROJECT_PATH" .xcodeproj)"
fi

# Prefer a sibling .xcworkspace over the bare .xcodeproj. Local SPM
# package test targets only RESOLVE through the workspace — against the
# bare project they silently don't run, so a "--all" against -project
# quietly skips every package suite. With the workspace, a mini run is
# the real everything: SPM package tests + app unit tests + UI tests.
CONTAINER_FLAG="-project"
CONTAINER_PATH="$PROJECT_PATH"
WORKSPACE_PATH="${PROJECT_PATH%.xcodeproj}.xcworkspace"
if [[ -d "$WORKSPACE_PATH" ]]; then
  CONTAINER_FLAG="-workspace"
  CONTAINER_PATH="$WORKSPACE_PATH"
fi

if [[ "$RUN_ALL" == false && -z "$TEST_FILTER" ]]; then
  # Default: assume the UI test bundle is named "<scheme>UITests".
  # Override via positional arg if your project doesn't follow this.
  TEST_FILTER="${SCHEME}UITests"
fi

# -----------------------------------------------------------------------
# Find local repo root (the rsync source). Walk up FROM THE DETECTED
# PROJECT (not from cwd!) until we find .git, falling back to the
# project's parent dir.
#
# Why from the project: in a bare-clone + worktrees layout
# (projects/<repo>/{main,feat-x,...}), running from the worktree PARENT
# made the cwd walk-up find no .git, so LOCAL_ROOT became the parent —
# rsyncing EVERY worktree and (worse) silently testing whichever
# worktree's .xcodeproj the BFS found first alphabetically (a stale
# feature branch, not the one you're working in). Deriving the root
# from the project pins the rsync + remote run to the worktree that
# actually owns the detected project.
# -----------------------------------------------------------------------

LOCAL_ROOT="$(dirname "$PROJECT_PATH")"
SEARCH_DIR="$LOCAL_ROOT"
while [[ "$SEARCH_DIR" != "/" ]]; do
  if [[ -d "$SEARCH_DIR/.git" ]] || [[ -f "$SEARCH_DIR/.git" ]]; then
    LOCAL_ROOT="$SEARCH_DIR"
    break
  fi
  SEARCH_DIR="$(dirname "$SEARCH_DIR")"
done

REMOTE_ROOT="$LOCAL_ROOT"  # identity mapping; both Macs use /Users/corey

echo "==> Worktree root: ${LOCAL_ROOT}"
echo "==> Container:     ${CONTAINER_PATH#$LOCAL_ROOT/} (${CONTAINER_FLAG})"

# Relative container (workspace or project) path inside the repo root,
# for the remote xcodebuild invocation:
REL_CONTAINER="${CONTAINER_PATH#$LOCAL_ROOT/}"

# -----------------------------------------------------------------------
# Find rsync. Apple ships an ancient 2.6.9 that doesn't support
# --mkpath; brew's rsync is 3.x. Pre-create the dir via ssh so the
# choice doesn't matter.
# -----------------------------------------------------------------------

RSYNC="$(command -v /opt/homebrew/bin/rsync || command -v rsync)"
if [[ -z "$RSYNC" ]]; then
  echo "error: rsync not found on PATH" >&2
  exit 1
fi

# -----------------------------------------------------------------------
# Optional: refuse if an xcodebuild is already running on the mini.
# XCUITest grabs the screen — concurrent runs fight each other.
# -----------------------------------------------------------------------

if ssh "${REMOTE_USER}@${REMOTE_HOST}" "pgrep -x xcodebuild >/dev/null"; then
  echo "error: xcodebuild already running on ${REMOTE_HOST} — wait or kill it" >&2
  exit 1
fi

# -----------------------------------------------------------------------
# Rsync local working tree to the mini.
# -----------------------------------------------------------------------

echo "==> Mirroring ${LOCAL_ROOT} → ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_ROOT}"

ssh "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p '${REMOTE_ROOT}'"

# Excludes: anything regenerable by the build, anything large/local-only,
# anything git-related (we don't need history on the mini).
"$RSYNC" -az --delete \
  --exclude='.git/' \
  --exclude='.gitignore' \
  --exclude='build/' \
  --exclude='DerivedData/' \
  --exclude='.build/' \
  --exclude='node_modules/' \
  --exclude='*.xcuserstate' \
  --exclude='*.xcresult' \
  --exclude='xcuserdata/' \
  --exclude='.DS_Store' \
  --exclude='.swiftpm/' \
  "${LOCAL_ROOT}/" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_ROOT}/"

# -----------------------------------------------------------------------
# Build the remote command.
# -----------------------------------------------------------------------

if [[ "$CI_MODE" == true ]]; then
  # CI-parity mode: run the project's scripts/ci-test.sh, the single source of
  # truth the CI workflow also calls. It runs the SPM packages via
  # `swift test --parallel` (tests parallel WITHIN each package — which a serial
  # xcodebuild over the .xctestplan does NOT reproduce), then the app + UI
  # xcodebuild slices. This is what makes a mini run actually predict CI.
  # The script does its own xcbeautify formatting, so no outer pipe.
  REMOTE_CMD_STR="cd '${REMOTE_ROOT}' && bash scripts/ci-test.sh all"
else
  REMOTE_CMD=(
    cd "${REMOTE_ROOT}" \&\& xcodebuild test
    "${CONTAINER_FLAG}" "'${REL_CONTAINER}'"
    -scheme "'${SCHEME}'"
    -destination "'platform=macOS'"
    -resultBundlePath "'build/remote-tests.xcresult'"
  )

  if [[ "$RUN_ALL" == false && -n "$TEST_FILTER" ]]; then
    REMOTE_CMD+=( "-only-testing:${TEST_FILTER}" )
  fi

  # Pipe through xcbeautify if it's on the remote.
  REMOTE_CMD_STR="${REMOTE_CMD[@]}"
  REMOTE_CMD_STR="${REMOTE_CMD_STR} | { command -v xcbeautify >/dev/null && xcbeautify || cat; }"
fi

# -----------------------------------------------------------------------
# Execute.
#
# Wrap in `launchctl asuser $UID` so the xcodebuild process inherits
# the GUI user's launchd context. Without this, codesign can't access
# the signing identity in the login keychain (errSecInternalComponent)
# even though the keychain is unlocked for the GUI session — SSH
# sessions and GUI sessions live in different launchd domains.
#
# This is the standard workaround for "codesign works for the logged-in
# user but fails over SSH" on macOS. Requires that someone is actually
# logged in at the console (auto-login satisfies this).
# -----------------------------------------------------------------------

echo "==> Running on ${REMOTE_HOST}: xcodebuild test -scheme ${SCHEME}${TEST_FILTER:+ -only-testing:${TEST_FILTER}}"
echo

# xcodebuild refuses to overwrite an existing -resultBundlePath, so
# clear any stale bundle from a previous run before invoking. Use
# sudo because an earlier failed run that landed as root may have
# left root-owned files in the bundle that a plain rm can't touch.
ssh "${REMOTE_USER}@${REMOTE_HOST}" \
  "sudo -n rm -rf '${REMOTE_ROOT}/build/remote-tests.xcresult'"

set +e
# Three layers:
#   1. sudo: elevate to root so launchctl asuser can switch audit sessions
#   2. launchctl asuser <UID>: enter the GUI user's launchd domain (where
#      the unlocked login keychain is accessible)
#   3. sudo -u <user>: drop back from root to the actual user so the
#      build artifacts land in /Users/<user>/Library/... not /var/root/
#
# `$(id -u ${REMOTE_USER})` is evaluated AFTER ssh interpolation but
# BEFORE the outer sudo runs — gives the GUI user's UID, not root's.
#
# Requires NOPASSWD sudoers entry for the user:
#   ${REMOTE_USER} ALL=(ALL) NOPASSWD: /bin/launchctl, /usr/bin/sudo
ssh -t "${REMOTE_USER}@${REMOTE_HOST}" \
  "sudo -n launchctl asuser \$(id -u ${REMOTE_USER}) sudo -n -u ${REMOTE_USER} /bin/bash -lc 'set -o pipefail; ${REMOTE_CMD_STR}'"
EXIT_CODE=$?
set -e

# -----------------------------------------------------------------------
# Pull xcresult on failure if requested.
# -----------------------------------------------------------------------

if [[ "$EXIT_CODE" -ne 0 && "$PULL_XCRESULT" == true ]]; then
  echo
  echo "==> Test failed; pulling xcresult bundle..."
  mkdir -p "${LOCAL_ROOT}/build"
  "$RSYNC" -az --delete \
    "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_ROOT}/build/remote-tests.xcresult/" \
    "${LOCAL_ROOT}/build/remote-ui-tests.xcresult/"
  echo "==> Open with: open '${LOCAL_ROOT}/build/remote-ui-tests.xcresult'"
fi

exit "$EXIT_CODE"
