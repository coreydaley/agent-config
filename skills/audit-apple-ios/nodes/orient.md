# Node: orient

Phase 1 of the framework — detect the iOS / iPadOS target and capture
the iOS-specific source surface the reviewers need. **iOS audit bails
early if no iOS / iPadOS target is present** — this skill is wholly
inapplicable to projects that only ship macOS / watchOS / visionOS
binaries. There are no emergency-exit conditions beyond that bail; the
`orient → emergency_exit` edge is structurally present but never
taken in practice.

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only)
- Optional env vars: `SKIP_XCODEBUILD=1` skips `xcodebuild`-driven steps (useful when Xcode isn't installed; source-only fallback)

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
TO=$(bash ~/.claude/lib/audit-runner.sh timeout-bin)
[ -z "$TO" ] && echo "no timeout command available; install via 'brew install coreutils' for tool timeouts" \
  >> "$AUDIT_DIR/tooling-raw/STATUS.md"
```

## Steps

### 1. Detect iOS / iPadOS target presence (gate)

This is the only gating decision in orient. If no iOS / iPadOS target
is detected across the project / SPM platforms, bail with a pointer to
a more appropriate platform audit.

```bash
HAS_IOS=0

# Method 1: IPHONEOS_DEPLOYMENT_TARGET in build settings or xcconfig
if grep -rqE 'IPHONEOS_DEPLOYMENT_TARGET\s*=' "$PROJECT_CWD" \
     --include='*.pbxproj' --include='*.xcconfig' 2>/dev/null; then
  HAS_IOS=1
fi

# Method 2: SUPPORTED_PLATFORMS mentions iphoneos / iphonesimulator
if grep -rqE 'SUPPORTED_PLATFORMS[^=]*=.*iphoneos' "$PROJECT_CWD" \
     --include='*.pbxproj' --include='*.xcconfig' 2>/dev/null; then
  HAS_IOS=1
fi

# Method 3: Package.swift declares .iOS platform
if [ -f "$PROJECT_CWD/Package.swift" ] && grep -qE '\.iOS\(' "$PROJECT_CWD/Package.swift" 2>/dev/null; then
  HAS_IOS=1
fi

# Method 4: TARGETED_DEVICE_FAMILY = 1 (iPhone), 2 (iPad), or "1,2" (Universal)
if grep -rqE 'TARGETED_DEVICE_FAMILY\s*=\s*"?[12](,[12])?"?' "$PROJECT_CWD" \
     --include='*.pbxproj' --include='*.xcconfig' 2>/dev/null; then
  HAS_IOS=1
fi

scripts/walk.sh set --state "$STATE" --key has_ios_target --value "$HAS_IOS"

if [ "$HAS_IOS" -eq 0 ]; then
  bail "audit-apple-ios: no iOS / iPadOS target detected in $PROJECT_CWD. This audit is a no-op without an iOS / iPadOS target. If this is a macOS-only project use /audit-apple-macos, watchOS-only use /audit-apple-watchos, visionOS-only use /audit-apple-visionos. To confirm an iOS target should exist, check IPHONEOS_DEPLOYMENT_TARGET in *.xcconfig / *.pbxproj, SUPPORTED_PLATFORMS containing iphoneos, .iOS in Package.swift, or TARGETED_DEVICE_FAMILY in build settings."
fi
```

### 2. Snapshot iOS deployment target + device family

```bash
{
  echo "=== IPHONEOS_DEPLOYMENT_TARGET / TARGETED_DEVICE_FAMILY (source) ==="
  grep -rE 'IPHONEOS_DEPLOYMENT_TARGET\s*=|TARGETED_DEVICE_FAMILY\s*=|SUPPORTED_PLATFORMS\s*=' \
    "$PROJECT_CWD" --include='*.pbxproj' --include='*.xcconfig' 2>/dev/null || true
  echo
  echo "=== Package.swift platforms (if SPM) ==="
  [ -f "$PROJECT_CWD/Package.swift" ] && grep -E '\.iOS\(|\.macCatalyst\(|\.macOS\(|\.watchOS\(|\.visionOS\(|\.tvOS\(' \
    "$PROJECT_CWD/Package.swift" 2>/dev/null || echo "(no Package.swift)"
} > "$AUDIT_DIR/tooling-raw/ios-deployment.txt" 2>&1

if [ -z "${SKIP_XCODEBUILD:-}" ] && command -v xcodebuild >/dev/null; then
  WORKSPACE=$(ls "$PROJECT_CWD"/*.xcworkspace 2>/dev/null | head -1)
  PROJECT=$(ls "$PROJECT_CWD"/*.xcodeproj 2>/dev/null | head -1)
  if [ -n "$WORKSPACE" ] || [ -n "$PROJECT" ]; then
    XC_ARGS=()
    [ -n "$WORKSPACE" ] && XC_ARGS+=(-workspace "$WORKSPACE") || XC_ARGS+=(-project "$PROJECT")
    ${TO:+$TO 60} xcodebuild -showBuildSettings "${XC_ARGS[@]}" 2>/dev/null \
      | grep -E 'IPHONEOS_DEPLOYMENT_TARGET|TARGETED_DEVICE_FAMILY|SUPPORTED_PLATFORMS|PRODUCT_BUNDLE_IDENTIFIER|SDKROOT' \
      >> "$AUDIT_DIR/tooling-raw/ios-deployment.txt" 2>&1 || true
  fi
else
  echo "xcodebuild skipped (SKIP_XCODEBUILD set or xcodebuild missing); source-only fallback" \
    >> "$AUDIT_DIR/tooling-raw/STATUS.md"
fi
```

### 3. Snapshot iOS-relevant Info.plist keys

The single highest-yield artifact for this audit — `UIRequiresFullScreen`,
`UIApplicationSceneManifest`, `UIBackgroundModes`, and
`BGTaskSchedulerPermittedIdentifiers` here drive at least half of the
findings.

```bash
{
  for plist in $(find "$PROJECT_CWD" -name 'Info.plist' -not -path '*/.build/*' -not -path '*/Pods/*' 2>/dev/null); do
    echo "=== $plist ==="
    plutil -p "$plist" 2>/dev/null \
      | grep -E 'UIApplicationSceneManifest|UISupportedInterfaceOrientations|UIRequiresFullScreen|UIBackgroundModes|BGTaskSchedulerPermittedIdentifiers|UILaunchScreen|UILaunchStoryboardName|UIViewControllerBasedStatusBarAppearance|UISupportsDocumentBrowser|UIRequiredDeviceCapabilities|UIAppFonts|UIStatusBarStyle|UIStatusBarHidden|CFBundleURLTypes|NSUserActivityTypes' \
      || cat "$plist"
    echo
  done
  echo "=== INFOPLIST_KEY_* (Xcode 15+ generated keys) ==="
  grep -rE 'INFOPLIST_KEY_UI[A-Za-z_]+\s*=' "$PROJECT_CWD" --include='*.pbxproj' --include='*.xcconfig' 2>/dev/null || echo "(none)"
} > "$AUDIT_DIR/tooling-raw/ios-info-plists.txt" 2>&1
```

### 4. Snapshot scene lifecycle adoption

```bash
{
  echo "=== UIWindowSceneDelegate / UISceneSession adoption ==="
  grep -rnE 'UIWindowSceneDelegate|UISceneDelegate|UISceneSession|UISceneConfiguration|configurationForConnecting|scene\(_:willConnectTo:|scene\(_:continue:|scene\(_:openURLContexts:|stateRestorationActivity' \
    "$PROJECT_CWD" --include='*.swift' --include='*.m' 2>/dev/null || echo "(none found)"
  echo
  echo "=== AppDelegate lifecycle methods (legacy / pre-scene) ==="
  grep -rnE 'application\(_:didFinishLaunchingWithOptions:|application\(_:open:|application\(_:continue:|application\(_:performActionFor:|application\(_:didReceiveRemoteNotification:|UIApplicationDelegateAdaptor' \
    "$PROJECT_CWD" --include='*.swift' --include='*.m' 2>/dev/null || echo "(none found)"
  echo
  echo "=== SwiftUI App / WindowGroup ==="
  grep -rnE '@main|protocol App|WindowGroup|UIApplicationDelegateAdaptor|@UIApplicationDelegateAdaptor' \
    "$PROJECT_CWD" --include='*.swift' 2>/dev/null || echo "(none found)"
} > "$AUDIT_DIR/tooling-raw/scene-lifecycle.txt" 2>&1
```

### 5. Snapshot BGTaskScheduler usage

```bash
{
  echo "=== BGTaskScheduler.register / submit / cancel ==="
  grep -rnE 'BGTaskScheduler\.(shared|default)|BGAppRefreshTask|BGProcessingTask|BGTaskRequest|BGAppRefreshTaskRequest|BGProcessingTaskRequest|register\(forTaskWithIdentifier:|expirationHandler|earliestBeginDate|requiresExternalPower|requiresNetworkConnectivity' \
    "$PROJECT_CWD" --include='*.swift' --include='*.m' 2>/dev/null || echo "(none found)"
  echo
  echo "=== BGTaskSchedulerPermittedIdentifiers (Info.plist) ==="
  grep -rE 'BGTaskSchedulerPermittedIdentifiers' "$PROJECT_CWD" --include='*.plist' -A8 2>/dev/null || echo "(none found)"
} > "$AUDIT_DIR/tooling-raw/bg-task-scheduler.txt" 2>&1
```

### 6. Snapshot UIBackgroundModes flags + silent-push handler

```bash
{
  echo "=== UIBackgroundModes (Info.plist) ==="
  grep -rE 'UIBackgroundModes' "$PROJECT_CWD" --include='*.plist' -A20 2>/dev/null || echo "(none found)"
  echo
  echo "=== Silent-push handler (didReceiveRemoteNotification fetchCompletionHandler) ==="
  grep -rnE 'didReceiveRemoteNotification.*fetchCompletionHandler|UIBackgroundFetchResult\.(newData|noData|failed)|application\(_:didReceiveRemoteNotification:' \
    "$PROJECT_CWD" --include='*.swift' --include='*.m' 2>/dev/null || echo "(none found)"
  echo
  echo "=== PushKit (VoIP push) ==="
  grep -rnE 'import PushKit|PKPushRegistry|PKPushRegistryDelegate|PKPushType\.voIP' \
    "$PROJECT_CWD" --include='*.swift' --include='*.m' 2>/dev/null || echo "(none found)"
} > "$AUDIT_DIR/tooling-raw/ui-background-modes.txt" 2>&1
```

### 7. Snapshot iPad input affordances (pointer / Pencil / keyboard)

```bash
{
  echo "=== UIPointerInteraction / UIHoverGestureRecognizer ==="
  grep -rnE 'UIPointerInteraction|UIPointerInteractionDelegate|UIPointerStyle|UIPointerEffect|UIHoverGestureRecognizer|onHover\b' \
    "$PROJECT_CWD" --include='*.swift' --include='*.m' 2>/dev/null || echo "(none found)"
  echo
  echo "=== UIKeyCommand / keyboardShortcut ==="
  grep -rnE 'UIKeyCommand|keyCommands\b|keyboardShortcut\(|focusable\(|@FocusState' \
    "$PROJECT_CWD" --include='*.swift' --include='*.m' 2>/dev/null || echo "(none found)"
  echo
  echo "=== Apple Pencil (PencilKit / Scribble) ==="
  grep -rnE 'import PencilKit|PKCanvasView|PKToolPicker|PKDrawing|PKStroke|UIIndirectScribbleInteraction|UIPencilInteraction' \
    "$PROJECT_CWD" --include='*.swift' --include='*.m' 2>/dev/null || echo "(none found)"
} > "$AUDIT_DIR/tooling-raw/ipad-input.txt" 2>&1
```

### 8. Snapshot hardware-button integration (Action Button + Camera Control)

```bash
{
  echo "=== AppShortcuts / AppShortcutsProvider (Action Button surface) ==="
  grep -rnE 'AppShortcut\b|AppShortcutsProvider|AppShortcutsBuilder|AppIntent\b|import AppIntents' \
    "$PROJECT_CWD" --include='*.swift' 2>/dev/null || echo "(none found)"
  echo
  echo "=== Camera Control (iPhone 16) — AVCaptureControl ==="
  grep -rnE 'AVCaptureControl|AVCaptureSlider|AVCaptureIndexPicker|supportedControls|AVCaptureSession\.controls' \
    "$PROJECT_CWD" --include='*.swift' --include='*.m' 2>/dev/null || echo "(none found)"
} > "$AUDIT_DIR/tooling-raw/hardware-buttons.txt" 2>&1
```

### 9. Snapshot Live Activity / Dynamic Island / Lock Screen surface

```bash
{
  echo "=== ActivityKit / Live Activity ==="
  grep -rnE 'import ActivityKit|ActivityAttributes|Activity<|ActivityKit\.Activity|ActivityConfiguration|DynamicIsland\b|dynamicIsland\b|ActivityContent\b|pushType\s*:\s*\.token' \
    "$PROJECT_CWD" --include='*.swift' 2>/dev/null || echo "(none found)"
  echo
  echo "=== Lock Screen / StandBy widget families ==="
  grep -rnE '\.accessoryCircular|\.accessoryRectangular|\.accessoryInline|\.systemSmall|\.systemMedium|\.systemLarge|\.systemExtraLarge|supportedFamilies|widgetFamily|contentMarginsDisabled|privacySensitive\(' \
    "$PROJECT_CWD" --include='*.swift' 2>/dev/null || echo "(none found)"
  echo
  echo "=== NSSupportsLiveActivities (Info.plist) ==="
  grep -rE 'NSSupportsLiveActivities' "$PROJECT_CWD" --include='*.plist' -A2 2>/dev/null || echo "(none found)"
} > "$AUDIT_DIR/tooling-raw/live-activity.txt" 2>&1
```

### 10. Snapshot Live Text + VisualLookUp

```bash
{
  echo "=== ImageAnalysisInteraction (Live Text) ==="
  grep -rnE 'ImageAnalysisInteraction|ImageAnalyzer\b|ImageAnalysis\b|preferredInteractionTypes|\.imageSubject\b' \
    "$PROJECT_CWD" --include='*.swift' 2>/dev/null || echo "(none found)"
  echo
  echo "=== Vision OCR (VNRecognizeTextRequest) ==="
  grep -rnE 'VNRecognizeTextRequest|VNImageRequestHandler|VNDocumentCameraViewController' \
    "$PROJECT_CWD" --include='*.swift' --include='*.m' 2>/dev/null || echo "(none found)"
} > "$AUDIT_DIR/tooling-raw/live-text.txt" 2>&1
```

### 11. Snapshot Focus Filter integration

```bash
{
  echo "=== FocusFilterIntent ==="
  grep -rnE 'FocusFilterIntent|SetFocusFilterIntent|FocusFilterAppContext' \
    "$PROJECT_CWD" --include='*.swift' 2>/dev/null || echo "(none found)"
  echo
  echo "=== Notification-filtering entitlement ==="
  grep -rE 'com\.apple\.developer\.usernotifications\.filtering' \
    "$PROJECT_CWD" --include='*.entitlements' --include='*.plist' 2>/dev/null || echo "(none found)"
} > "$AUDIT_DIR/tooling-raw/focus.txt" 2>&1
```

### 12. Phase 1 emergency-exit check

**iOS audit has no emergency-exit triggers beyond the iOS-target gate
handled in step 1.** Always proceed.

```bash
EMERGENCY=0
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "$EMERGENCY"
```

### 13. Survey

In conversational text (not a persisted file), note:

- `IPHONEOS_DEPLOYMENT_TARGET` value — gates whether Lock Screen widgets (iOS 16+), Dynamic Island (iOS 16.1+ on iPhone 14 Pro+), StandBy mode (iOS 17+), and Action Button (iOS 17+ on iPhone 15 Pro+) are even available
- `TARGETED_DEVICE_FAMILY` — `1` (iPhone-only), `2` (iPad-only), `1,2` (Universal); iPad-included targets get iPad-multitasking findings
- Lifecycle adoption: AppDelegate-only (legacy), SceneDelegate-based (iOS 13+), or SwiftUI `App` / `WindowGroup` (modern). Pre-scene on iOS 13+ is a `SceneLifecycle` finding
- `UIRequiresFullScreen` value — **highest-risk Info.plist key**; `YES` on a non-game productivity app breaks iPad multitasking + Stage Manager
- `UIApplicationSceneManifest` present + `UIApplicationSupportsMultipleScenes=YES` — required for iPad multi-scene
- `UISupportedInterfaceOrientations` per device family — portrait-only on iPad is suspicious
- `UIBackgroundModes` flags actually declared — every flag must be justified by a callsite
- `BGTaskSchedulerPermittedIdentifiers` matches the identifiers in source `BGTaskScheduler.register` calls
- Live Activity presence: `import ActivityKit`, `ActivityAttributes` conformances, `DynamicIsland` builder usage
- Action Button readiness: `AppShortcutsProvider` declared with at least one `AppShortcut`
- Live Text / Vision: image-heavy app? `ImageAnalysisInteraction` adopted?
- Focus integration: `FocusFilterIntent` conformance? Notifications-heavy app without it is a friction point

This is for the user's situational awareness, not a persisted artifact.

## Outputs

- `$AUDIT_DIR/tooling-raw/ios-deployment.txt`
- `$AUDIT_DIR/tooling-raw/ios-info-plists.txt`
- `$AUDIT_DIR/tooling-raw/scene-lifecycle.txt`
- `$AUDIT_DIR/tooling-raw/bg-task-scheduler.txt`
- `$AUDIT_DIR/tooling-raw/ui-background-modes.txt`
- `$AUDIT_DIR/tooling-raw/ipad-input.txt`
- `$AUDIT_DIR/tooling-raw/hardware-buttons.txt`
- `$AUDIT_DIR/tooling-raw/live-activity.txt`
- `$AUDIT_DIR/tooling-raw/live-text.txt`
- `$AUDIT_DIR/tooling-raw/focus.txt`
- `$AUDIT_DIR/tooling-raw/STATUS.md` (any skipped tools)
- Walker state has `has_ios_target`, `emergency_exit` set

## Outgoing edges

- **`proceed`** → `independent_reviews`. Normal path.
- **`emergency`** → `emergency_exit`. Never taken (no triggers beyond the bail in step 1).

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- No iOS / iPadOS target → bail in step 1 with a clear pointer to the appropriate platform audit. This is the correct behavior.
- `xcodebuild -showBuildSettings` times out → captured in STATUS.md; orient still proceeds with the grep-based artifacts.
- Project has `IPHONEOS_DEPLOYMENT_TARGET` but no actual iOS source files (e.g. macOS-only project with a stale iOS legacy target) → reviewers flag it as an orphan target in Phase 2 (category: `iOSInfoPlistSurface`).
