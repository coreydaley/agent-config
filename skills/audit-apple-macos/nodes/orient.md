# Node: orient

Phase 1 of the framework — collect the macOS-specific artifact snapshot the reviewers need. **Apple-macos has Phase 1 tooling (xcodebuild + plutil + codesign + Sparkle scan) but no emergency-exit conditions** — the `orient → emergency_exit` edge is structurally present but never taken.

**This audit only fires on projects that target macOS.** If no macOS deployment target is found across the project / SPM platforms, orient bails with a pointer to a more appropriate audit.

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only)
- Optional env vars: `SKIP_XCODEBUILD=1` skips `xcodebuild`-driven steps

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
TO=$(bash ~/.claude/lib/audit-runner.sh timeout-bin)
[ -z "$TO" ] && echo "no timeout command available; install via 'brew install coreutils' for tool timeouts" \
  >> "$AUDIT_DIR/tooling-raw/STATUS.md"
```

## Steps

### 1. Detect project shape

```bash
WORKSPACE=$(ls "$PROJECT_CWD"/*.xcworkspace 2>/dev/null | head -1)
PROJECT=$(ls "$PROJECT_CWD"/*.xcodeproj 2>/dev/null | head -1)
PACKAGE_SWIFT="$PROJECT_CWD/Package.swift"

if [ -z "$WORKSPACE" ] && [ -z "$PROJECT" ] && [ ! -f "$PACKAGE_SWIFT" ]; then
  bail "no .xcodeproj / .xcworkspace / Package.swift in scope; nothing for audit-apple-macos to review"
fi
```

### 2. Snapshot build settings

```bash
if [ -z "${SKIP_XCODEBUILD:-}" ] && command -v xcodebuild >/dev/null; then
  if [ -n "$WORKSPACE" ]; then
    xcodebuild -list -workspace "$WORKSPACE" > "$AUDIT_DIR/tooling-raw/schemes.txt" 2>&1 || true
  elif [ -n "$PROJECT" ]; then
    xcodebuild -list -project "$PROJECT" > "$AUDIT_DIR/tooling-raw/schemes.txt" 2>&1 || true
  fi
  SCHEME=$(awk '/Schemes:/{flag=1;next}/^$/{flag=0}flag{print $1; exit}' "$AUDIT_DIR/tooling-raw/schemes.txt" 2>/dev/null)

  if [ -n "$SCHEME" ]; then
    XC_ARGS=()
    if [ -n "$WORKSPACE" ]; then XC_ARGS+=(-workspace "$WORKSPACE")
    else XC_ARGS+=(-project "$PROJECT"); fi
    ${TO:+$TO 120} xcodebuild -showBuildSettings "${XC_ARGS[@]}" -scheme "$SCHEME" -configuration Debug \
      > "$AUDIT_DIR/tooling-raw/build-settings-debug.txt" 2>&1 || true
    ${TO:+$TO 120} xcodebuild -showBuildSettings "${XC_ARGS[@]}" -scheme "$SCHEME" -configuration Release \
      > "$AUDIT_DIR/tooling-raw/build-settings-release.txt" 2>&1 || true
  else
    echo "no scheme detected; build settings snapshot skipped" >> "$AUDIT_DIR/tooling-raw/STATUS.md"
  fi
else
  echo "xcodebuild skipped (SKIP_XCODEBUILD set or xcodebuild missing)" >> "$AUDIT_DIR/tooling-raw/STATUS.md"
fi
```

### 3. Confirm macOS is targeted (audit guard)

```bash
HAS_MACOS=0
if grep -qE '^\s*(MACOSX_DEPLOYMENT_TARGET|SUPPORTS_MACCATALYST|SUPPORTED_PLATFORMS.*macosx)' \
     "$AUDIT_DIR/tooling-raw/build-settings-release.txt" 2>/dev/null; then
  HAS_MACOS=1
fi
if [ -f "$PACKAGE_SWIFT" ] && grep -qE '\.macOS\(' "$PACKAGE_SWIFT"; then
  HAS_MACOS=1
fi
if [ -n "$PROJECT" ] && grep -qE 'SUPPORTED_PLATFORMS.*macosx' "$PROJECT/project.pbxproj" 2>/dev/null; then
  HAS_MACOS=1
fi

scripts/walk.sh set --state "$STATE" --key has_macos --value "$HAS_MACOS"
if [ "$HAS_MACOS" -ne 1 ]; then
  bail "no macOS deployment target found; audit-apple-macos only runs on projects that ship to macOS. Try /audit-apple-build-release or /audit-apple-design."
fi
```

### 4. Entitlements snapshot (Hardened Runtime + App Sandbox)

```bash
find "$PROJECT_CWD" -name "*.entitlements" -not -path '*/.build/*' \
  -exec sh -c 'echo "=== $1 ==="; cat "$1"; echo' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/entitlements-per-target.txt" 2>&1 || true
```

The reviewers will scan this file for:
- `com.apple.security.app-sandbox` — required for Mac App Store
- `com.apple.security.cs.disable-library-validation`, `com.apple.security.cs.allow-jit`, `com.apple.security.cs.allow-unsigned-executable-memory`, `com.apple.security.cs.allow-dyld-environment-variables` — Hardened Runtime exceptions, each must be justified
- `com.apple.security.files.user-selected.read-write` / `read-only` — Powerbox file access for sandboxed apps
- `com.apple.security.files.bookmarks.app-scope` / `document-scope` — security-scoped bookmark capability

### 5. Info.plist snapshot (LSUIElement + UTType)

```bash
find "$PROJECT_CWD" -name "Info.plist" -not -path '*/.build/*' -not -path '*/Pods/*' \
  -exec sh -c 'echo "=== $1 ==="; plutil -p "$1" 2>/dev/null || cat "$1"; echo' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/info-plists.txt" 2>&1 || true
```

Reviewers look for `LSUIElement` (menu bar app), `LSApplicationCategoryType`, `UTExportedTypeDeclarations` / `UTImportedTypeDeclarations` (document-based apps), `LSMinimumSystemVersion`, and `CFBundleDocumentTypes`.

### 6. Distribution config — ExportOptions.plist `method`

```bash
find "$PROJECT_CWD" -name "ExportOptions*.plist" -not -path '*/.build/*' \
  -exec sh -c 'echo "=== $1 ==="; plutil -p "$1" 2>/dev/null || cat "$1"; echo' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/export-options-plists.txt" 2>&1 || true
```

The `method` key (`app-store`, `developer-id`, `mac-application`, `release-testing`) determines which signing/notarization rules apply. Reviewers cross-reference this against the entitlements: `app-store` requires App Sandbox; `developer-id` requires Notarization stapling.

### 7. Built `.app` bundles — codesign + spctl

```bash
APPS=()
for d in "$PROJECT_CWD/build" "$PROJECT_CWD/DerivedData" \
         "$HOME/Library/Developer/Xcode/DerivedData"; do
  [ -d "$d" ] && while IFS= read -r p; do APPS+=("$p"); done < \
    <(find "$d" -maxdepth 6 -name "*.app" -type d 2>/dev/null | head -10)
done

{
  for a in "${APPS[@]}"; do
    echo "=== $a ==="
    codesign --display --entitlements - --xml "$a" 2>&1 || true
    echo
    spctl --assess --type execute --verbose=2 "$a" 2>&1 || true
    echo "----"
  done
} > "$AUDIT_DIR/tooling-raw/codesign-display.txt" 2>&1

[ ${#APPS[@]} -eq 0 ] && echo "no built *.app bundles found; codesign/spctl checks skipped" \
  >> "$AUDIT_DIR/tooling-raw/STATUS.md"
```

### 8. Sparkle detection (1 vs 2)

```bash
{
  grep -E '"sparkle-project/Sparkle"|"sparkle"' \
    "$PROJECT_CWD/Package.resolved" \
    "$PROJECT_CWD"/*.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved \
    "$PROJECT_CWD"/*.xcworkspace/xcshareddata/swiftpm/Package.resolved 2>/dev/null || true
  grep -E "pod ['\"]Sparkle['\"]" "$PROJECT_CWD/Podfile" 2>/dev/null || true
  grep -rE '^import Sparkle' "$PROJECT_CWD" --include='*.swift' 2>/dev/null | head -20 || true
  grep -E 'SUPublicEDKey|SUPublicDSAKeyFile|SUFeedURL' \
    "$AUDIT_DIR/tooling-raw/info-plists.txt" 2>/dev/null || true
} > "$AUDIT_DIR/tooling-raw/sparkle-detection.txt" 2>&1
```

### 9. Phase 1 emergency-exit check

**Apple-macos has no emergency-exit triggers.** Always proceed.

```bash
EMERGENCY=0
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "$EMERGENCY"
```

### 10. Survey

In conversational text, note: macOS deployment target value, whether Mac Catalyst or native AppKit/SwiftUI for macOS (or both), `ExportOptions.plist` `method` if found, presence of App Sandbox entitlement, count of `com.apple.security.cs.*` Hardened Runtime exceptions, Sparkle major version detected, distribution channel inferred (MAS vs Developer ID Direct), `LSUIElement` set (menu bar app), document-based app indicators.

## Outputs

- `$AUDIT_DIR/tooling-raw/` populated
- `$AUDIT_DIR/tooling-raw/STATUS.md` documents skipped tools
- Walker state has `has_macos`, `emergency_exit` set

## Outgoing edges

- **`proceed`** → `independent_reviews`. Normal path.
- **`emergency`** → `emergency_exit`. Never taken.

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- No macOS target → bail with pointer to `audit-apple-build-release` / `audit-apple-design`.
- `xcodebuild -showBuildSettings` times out → captured; reviewers use source-only fallback.
- No built `.app` → `codesign-display.txt` is empty; reviewers operate on source + entitlements only, and the report's verification steps include "rebuild + re-run `codesign --display`".
