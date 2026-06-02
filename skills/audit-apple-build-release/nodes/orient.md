# Node: orient

Phase 1 of the framework — collect the build/release artifact snapshot the reviewers need. **Build & release has Phase 1 tooling (xcodebuild + plutil + lockfile dumps) but no emergency-exit conditions** — the `orient → emergency_exit` edge is structurally present but never taken.

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only)
- Optional env vars: `SKIP_XCODEBUILD=1` skips `xcodebuild`-driven steps (useful in CI where Xcode isn't installed or when project doesn't have a working scheme yet)

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
TO=$(bash ~/.claude/lib/audit-runner.sh timeout-bin)
[ -z "$TO" ] && echo "⚠️ no timeout command available; install via 'brew install coreutils' for tool timeouts" \
  >> "$AUDIT_DIR/tooling-raw/STATUS.md"
```

## Steps

### 1. Detect project shape

```bash
WORKSPACE=$(ls "$PROJECT_CWD"/*.xcworkspace 2>/dev/null | head -1)
PROJECT=$(ls "$PROJECT_CWD"/*.xcodeproj 2>/dev/null | head -1)
PACKAGE_SWIFT="$PROJECT_CWD/Package.swift"

HAS_XCWORKSPACE=$([ -n "$WORKSPACE" ] && echo 1 || echo 0)
HAS_XCODEPROJ=$([ -n "$PROJECT" ] && echo 1 || echo 0)
HAS_PACKAGE_SWIFT=$([ -f "$PACKAGE_SWIFT" ] && echo 1 || echo 0)

scripts/walk.sh set --state "$STATE" --key has_xcworkspace --value "$HAS_XCWORKSPACE"
scripts/walk.sh set --state "$STATE" --key has_xcodeproj   --value "$HAS_XCODEPROJ"
scripts/walk.sh set --state "$STATE" --key has_package     --value "$HAS_PACKAGE_SWIFT"
```

If none of the three are present, bail — there's nothing for this audit to review.

### 1b. Detect target platforms

```bash
# Detect target platforms
PLATFORMS=""
# Build-settings signals (iOS / macOS / watchOS / tvOS / visionOS)
for kind in IPHONEOS MACOSX WATCHOS TVOS XROS; do
  if grep -rqE "^[[:space:]]*${kind}_DEPLOYMENT_TARGET" "$PROJECT_CWD" --include='*.pbxproj' --include='*.xcconfig' 2>/dev/null; then
    case "$kind" in
      IPHONEOS) PLATFORMS="$PLATFORMS iOS";;
      MACOSX)   PLATFORMS="$PLATFORMS macOS";;
      WATCHOS)  PLATFORMS="$PLATFORMS watchOS";;
      TVOS)     PLATFORMS="$PLATFORMS tvOS";;
      XROS)     PLATFORMS="$PLATFORMS visionOS";;
    esac
  fi
done
# Package.swift platforms array signal
if [ -f "$PROJECT_CWD/Package.swift" ]; then
  for p in iOS macOS watchOS tvOS visionOS macCatalyst; do
    grep -qE "\.${p}\(" "$PROJECT_CWD/Package.swift" && PLATFORMS="$PLATFORMS $p"
  done
fi
PLATFORMS=$(echo "$PLATFORMS" | tr ' ' '\n' | sort -u | tr '\n' ',' | sed 's/^,//;s/,$//')
scripts/walk.sh set --state "$STATE" --key target_platforms --value "${PLATFORMS:-unknown}"
echo "Detected target platforms: ${PLATFORMS:-unknown}" >> "$AUDIT_DIR/tooling-raw/STATUS.md"
```

### 2. Snapshot build settings

`xcodebuild -showBuildSettings` is the single most useful Phase 1 artifact for this audit. It resolves the full inherited setting chain across xcconfigs, the .pbxproj, and the active scheme — letting reviewers find configuration drift between Debug and Release without manually walking the file.

```bash
if [ -z "${SKIP_XCODEBUILD:-}" ] && command -v xcodebuild >/dev/null; then
  # Pick a scheme: prefer the project's first scheme over a workspace
  # scheme (workspaces often have schemes from package dependencies that
  # are not the app target).
  if [ -n "$WORKSPACE" ]; then
    xcodebuild -list -workspace "$WORKSPACE" > "$AUDIT_DIR/tooling-raw/schemes.txt" 2>&1 || true
  elif [ -n "$PROJECT" ]; then
    xcodebuild -list -project "$PROJECT" > "$AUDIT_DIR/tooling-raw/schemes.txt" 2>&1 || true
  fi
  SCHEME=$(awk '/Schemes:/{flag=1;next}/^$/{flag=0}flag{print $1; exit}' "$AUDIT_DIR/tooling-raw/schemes.txt" 2>/dev/null)

  if [ -n "$SCHEME" ]; then
    XC_ARGS=()
    if [ -n "$WORKSPACE" ]; then
      XC_ARGS+=(-workspace "$WORKSPACE")
    else
      XC_ARGS+=(-project "$PROJECT")
    fi
    ${TO:+$TO 120} xcodebuild -showBuildSettings "${XC_ARGS[@]}" -scheme "$SCHEME" -configuration Debug \
      > "$AUDIT_DIR/tooling-raw/build-settings-debug.txt" 2>&1 || true
    ${TO:+$TO 120} xcodebuild -showBuildSettings "${XC_ARGS[@]}" -scheme "$SCHEME" -configuration Release \
      > "$AUDIT_DIR/tooling-raw/build-settings-release.txt" 2>&1 || true
  else
    echo "⚠️ no scheme detected; build settings snapshot skipped" >> "$AUDIT_DIR/tooling-raw/STATUS.md"
  fi
else
  echo "⚠️ xcodebuild skipped (SKIP_XCODEBUILD set or xcodebuild missing)" >> "$AUDIT_DIR/tooling-raw/STATUS.md"
fi
```

### 3. Snapshot configuration files

```bash
# .xcconfig files — the canonical place for build settings outside the .pbxproj
find "$PROJECT_CWD" -name "*.xcconfig" -not -path '*/.build/*' -not -path '*/DerivedData/*' \
  -exec sh -c 'echo "=== $1 ==="; cat "$1"; echo' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/xcconfig-files.txt" 2>&1 || true

# Entitlements per target
find "$PROJECT_CWD" -name "*.entitlements" -not -path '*/.build/*' \
  -exec sh -c 'echo "=== $1 ==="; cat "$1"; echo' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/entitlements-per-target.txt" 2>&1 || true

# Info.plist files (most projects have generated Info.plist now; capture explicit ones)
find "$PROJECT_CWD" -name "Info.plist" -not -path '*/.build/*' -not -path '*/Pods/*' \
  -exec sh -c 'echo "=== $1 ==="; plutil -p "$1" 2>/dev/null || cat "$1"; echo' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/info-plists.txt" 2>&1 || true

# ExportOptions.plist — distribution config
find "$PROJECT_CWD" -name "ExportOptions*.plist" -not -path '*/.build/*' \
  -exec sh -c 'echo "=== $1 ==="; plutil -p "$1" 2>/dev/null || cat "$1"; echo' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/export-options-plists.txt" 2>&1 || true
```

### 4. Snapshot dependency lockfiles

```bash
# SPM
RESOLVED_PATHS=(
  "$PROJECT_CWD/Package.resolved"
  "$PROJECT_CWD"/*.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved
  "$PROJECT_CWD"/*.xcworkspace/xcshareddata/swiftpm/Package.resolved
)
{
  for p in "${RESOLVED_PATHS[@]}"; do
    [ -f "$p" ] && { echo "=== $p ==="; cat "$p"; echo; }
  done
} > "$AUDIT_DIR/tooling-raw/package-resolved.txt" 2>&1

# CocoaPods
[ -f "$PROJECT_CWD/Podfile.lock" ] && cp "$PROJECT_CWD/Podfile.lock" "$AUDIT_DIR/tooling-raw/podfile-lock.txt"

# Carthage
[ -f "$PROJECT_CWD/Cartfile.resolved" ] && cp "$PROJECT_CWD/Cartfile.resolved" "$AUDIT_DIR/tooling-raw/cartfile-resolved.txt"
```

### 5. Phase 1 emergency-exit check

**Build & release has no emergency-exit triggers.** Always proceed.

```bash
EMERGENCY=0
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "$EMERGENCY"
```

### 6. Survey

In conversational text (not a persisted file), note:

- Project shape: `.xcworkspace` vs `.xcodeproj` vs `Package.swift`-only, presence of `Tuist/`, `XcodeGen/` (project.yml), or `Bazel` (BUILD files)
- Scheme(s) detected and which one drove the `build-settings-*` snapshot
- Configurations beyond Debug/Release (e.g. Staging, Beta) — visible in `schemes.txt` and `build-settings-*.txt`
- xcconfig files present and whether they're referenced from the .pbxproj (vs orphaned)
- Dependency managers in use: SPM (Package.swift + Package.resolved), CocoaPods (Podfile + Podfile.lock), Carthage (Cartfile + Cartfile.resolved), Tuist, vendored XCFrameworks
- Deployment targets per platform (from `build-settings-*.txt` `IPHONEOS_DEPLOYMENT_TARGET`, `MACOSX_DEPLOYMENT_TARGET`, `WATCHOS_DEPLOYMENT_TARGET`, `XROS_DEPLOYMENT_TARGET`)
- Signing strategy: `CODE_SIGN_STYLE=Automatic` vs `Manual`, `DEVELOPMENT_TEAM` populated, provisioning profile references
- Distribution config: any `ExportOptions.plist`, CI signing (fastlane, manual, GitHub Actions with `apple-actions/import-codesigning-certs`)

**If no Swift/Obj-C/project files found**: notify and stop.

This is for the user's situational awareness, not a persisted artifact.

## Outputs

- `$AUDIT_DIR/tooling-raw/` populated with whatever was available
- `$AUDIT_DIR/tooling-raw/STATUS.md` documents skipped tools
- Walker state has `has_xcworkspace`, `has_xcodeproj`, `has_package`, `emergency_exit` set

## Outgoing edges

- **`proceed`** → `independent_reviews`. Normal path.
- **`emergency`** → `emergency_exit`. Never taken (no triggers).

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- No `.xcodeproj`, `.xcworkspace`, or `Package.swift` in scope → bail with a pointer to a non-Apple project audit.
- `xcodebuild -showBuildSettings` times out (unusual; should be sub-minute) → captured in the log file; orient still proceeds and reviewers use source-only reading.
- `xcodebuild -list` returns no schemes (project never built / scheme not shared) → flagged as a finding category (`Schemes`) in Phase 2.
