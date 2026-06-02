# Node: orient

Phase 1 of the framework — survey the scope and document the absence of tooling. **Apple adaptivity has no Phase 1 tooling and no emergency-exit gate** — it's a pure-LLM audit. Reviewers note any existing snapshot tests covering multiple device sizes (e.g. `SnapshotTesting` matrices) during their Phase 2 reading.

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only)

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
```

## Steps

### 1. Run Phase 1 tooling

This audit runs no Phase 1 tooling — adaptivity issues are LLM-only review. Still record this in `tooling-raw/STATUS.md` so downstream nodes and the verify gate see a populated `tooling-raw/`.

```bash
mkdir -p "$AUDIT_DIR/tooling-raw"
cat > "$AUDIT_DIR/tooling-raw/STATUS.md" <<EOF
# Phase 1 Tooling Status — apple-adaptivity

No automated tooling is run for this audit. Adaptive-UI issues
(size class, orientation, multitasking, Dynamic Type AX5,
windowing) require manual code reading plus runtime verification
in Simulator at multiple device sizes / orientations / AX sizes.

Reviewers should note any existing snapshot tests covering
multiple device sizes (e.g. SnapshotTesting matrices) during
Phase 2.
EOF
```

### 2. Survey

In conversational text (not a persisted file), note:

- Resolved scope (`$PROJECT_CWD`) and any obvious sub-paths (`*.xcodeproj/`, `Package.swift`, `Podfile`)
- Apple project artifacts and target platforms — `Package.swift` `platforms:` array, `Info.plist` device family (`UIDeviceFamily`), `UISupportedInterfaceOrientations`, `UIRequiredDeviceCapabilities`
- Detected adaptive frameworks in use: SwiftUI (`WindowGroup`, `Scene`), UIKit (`UIWindowScene`, `UISceneDelegate`), AppKit, Mac Catalyst (`targetEnvironment(macCatalyst)` checks)
- `Info.plist` flags relevant to multitasking: `UIApplicationSupportsMultipleScenes`, `UIRequiresFullScreen` (iPad), `UISupportsDocumentBrowser`
- Size-class-aware code via grep for `horizontalSizeClass`, `verticalSizeClass`, `traitCollection`, `ViewThatFits`, `dynamicTypeSize`
- For visionOS: check for `ImmersiveSpace`, `RealityView`, `Volume`
- **If no Swift/Apple source found**: notify and stop; suggest `/audit-web-responsive` if the scope looks like a web frontend.

This is for the user's situational awareness, not a persisted artifact.

### 3. Detect target platforms

Record which Apple platforms the project targets so Phase 2 reviewers know which configurations are in scope (e.g. only flag visionOS findings if there's a visionOS target).

```bash
PLATFORMS=""
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
if [ -f "$PROJECT_CWD/Package.swift" ]; then
  for p in iOS macOS watchOS tvOS visionOS macCatalyst; do
    grep -qE "\.${p}\(" "$PROJECT_CWD/Package.swift" && PLATFORMS="$PLATFORMS $p"
  done
fi
PLATFORMS=$(echo "$PLATFORMS" | tr ' ' '\n' | sort -u | tr '\n' ',' | sed 's/^,//;s/,$//')
scripts/walk.sh set --state "$STATE" --key target_platforms --value "${PLATFORMS:-unknown}"
echo "Detected target platforms: ${PLATFORMS:-unknown}" >> "$AUDIT_DIR/tooling-raw/STATUS.md"
```

### 4. Persist any run-scoped state Phase 2 needs

```bash
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "0"
```

This audit has no emergency-exit conditions; the flag exists only for graph uniformity across the audit suite.

## Outputs

- `$AUDIT_DIR/tooling-raw/STATUS.md` documents the no-tooling posture
- Walker state has `target_platforms` set (comma-separated list of detected Apple platforms, or `unknown`)
- Walker state has `emergency_exit=0`

## Outgoing edges

- **`proceed`** → `independent_reviews`. The only path this audit ever takes.

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- No Swift / Apple source detected → stop the audit; tell the user and suggest a more appropriate audit. The graph has no clean "abort here" node, so use a hard bail rather than transitioning.
