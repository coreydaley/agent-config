# Node: orient

Phase 1 of the framework — establish a survey for the reviewers. **Apple design has no Phase 1 tooling and no emergency-exit conditions** — it's a pure-LLM review against Apple's Human Interface Guidelines (HIG). This node is largely a no-op for tooling, but still records a `STATUS.md` for parity with the rest of the audit suite.

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only)

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
```

## Steps

### 1. Run Phase 1 tooling

This audit runs no Phase 1 tooling — design issues are LLM-only review against Apple HIG. Reviewers note any existing snapshot-test or screenshot-test coverage (e.g. `SnapshotTesting`, Xcode Previews captured as references) during Phase 2; nothing is run automatically here.

Still write a `STATUS.md` so the artifact layout matches the rest of the audit suite:

```bash
cat > "$AUDIT_DIR/tooling-raw/STATUS.md" <<'EOF'
# Phase 1 tooling status — apple-design

This audit runs no Phase 1 tooling. Apple platform design is a pure-LLM
review against Apple's Human Interface Guidelines (HIG) and the platform
UI frameworks (SwiftUI, UIKit, AppKit, WatchKit). Reviewers note any
existing snapshot / screenshot test coverage during Phase 2.
EOF
```

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

### 2. Survey

In conversational text (not a persisted file), note:

- Resolved scope (`$PROJECT_CWD`) and any obvious sub-paths (`*.xcodeproj/`, `*.xcworkspace/`, `Package.swift`)
- Apple project artifacts present: `Package.swift` (+ `Package.resolved`), `Info.plist`, `*.xcassets/`, storyboards/XIBs
- Detected framework via imports: `SwiftUI`, `UIKit`, `AppKit`, `WatchKit`, `RealityKit` (visionOS), `WidgetKit`
- Read `Package.swift` `platforms` array or `Info.plist` to determine target platforms — affects valid `Platform` values for findings
- **Check for a project design system**: custom `Color` extensions (`Color.appPrimary` etc.), modifier libraries, component vendor folders, design tokens — if present, it takes precedence over generic HIG
- Asset catalog (`*.xcassets/`) — color sets with light/dark variants, App Icon, Accent Color, custom SF Symbols
- Navigation patterns in use: `NavigationStack`, `NavigationSplitView`, `TabView`, sidebar patterns, custom navigation
- Existing snapshot/screenshot test coverage if any

**If no Swift/Obj-C source found**: notify and stop, suggest `/audit-design` if it looks like a web project.

This is for the user's situational awareness, not a persisted artifact.

## Outputs

- `$AUDIT_DIR/tooling-raw/STATUS.md` documents the no-tooling status
- Walker state unchanged beyond what `init` set

## Outgoing edges

- **`proceed`** → `independent_reviews`. Normal path — this audit has no emergency-exit conditions.

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- No Swift/Obj-C source in scope → bail with a pointer to `/audit-design`. There's nothing for this audit to review.
