# Node: orient

Phase 1 of the framework — detect the watchOS target and capture the
watchOS-specific source surface the reviewers need. **watchOS audit
bails early if no watch target is present** — there is no fallback;
this skill is wholly inapplicable to projects that don't ship a watch
app. There are no emergency-exit conditions beyond that bail.

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

### 1. Detect watchOS target presence (gate)

This is the only gating decision in orient. If no watchOS target is
detected, bail with a pointer.

```bash
HAS_WATCH=0

# Method 1: WATCHOS_DEPLOYMENT_TARGET in build settings or pbxproj
if grep -rqE 'WATCHOS_DEPLOYMENT_TARGET\s*=' "$PROJECT_CWD" --include='*.pbxproj' --include='*.xcconfig' 2>/dev/null; then
  HAS_WATCH=1
fi

# Method 2: Package.swift declares .watchOS platform
if [ -f "$PROJECT_CWD/Package.swift" ] && grep -qE '\.watchOS\(' "$PROJECT_CWD/Package.swift" 2>/dev/null; then
  HAS_WATCH=1
fi

# Method 3: WKApplication / WKWatchOnly key in any Info.plist
if grep -rqE 'WKApplication|WKWatchOnly|WKCompanionAppBundleIdentifier' "$PROJECT_CWD" --include='*.plist' 2>/dev/null; then
  HAS_WATCH=1
fi

scripts/walk.sh set --state "$STATE" --key has_watch_target --value "$HAS_WATCH"

if [ "$HAS_WATCH" -eq 0 ]; then
  bail "audit-apple-watchos: no watchOS target detected in $PROJECT_CWD. This audit is a no-op without a watch app target. If the project should have a watch target, check WATCHOS_DEPLOYMENT_TARGET in *.xcconfig / *.pbxproj, .watchOS in Package.swift, or WKApplication in Info.plist."
fi
```

### 2. Snapshot watch-target metadata

```bash
# Watch targets and their bundle IDs (best-effort from pbxproj)
{
  echo "=== Watch target detection ==="
  grep -rE 'WATCHOS_DEPLOYMENT_TARGET\s*=' "$PROJECT_CWD" --include='*.pbxproj' --include='*.xcconfig' 2>/dev/null || true
  echo
  echo "=== WKApplication / WKWatchOnly / WKCompanionAppBundleIdentifier in Info.plist ==="
  grep -rE 'WKApplication|WKWatchOnly|WKCompanionAppBundleIdentifier|WKExtensionDelegateClassName' "$PROJECT_CWD" --include='*.plist' -B1 -A2 2>/dev/null || true
} > "$AUDIT_DIR/tooling-raw/watch-targets.txt" 2>&1

# Deployment target across configs
if [ -z "${SKIP_XCODEBUILD:-}" ] && command -v xcodebuild >/dev/null; then
  WORKSPACE=$(ls "$PROJECT_CWD"/*.xcworkspace 2>/dev/null | head -1)
  PROJECT=$(ls "$PROJECT_CWD"/*.xcodeproj 2>/dev/null | head -1)
  if [ -n "$WORKSPACE" ] || [ -n "$PROJECT" ]; then
    XC_ARGS=()
    [ -n "$WORKSPACE" ] && XC_ARGS+=(-workspace "$WORKSPACE") || XC_ARGS+=(-project "$PROJECT")
    ${TO:+$TO 60} xcodebuild -showBuildSettings "${XC_ARGS[@]}" 2>/dev/null \
      | grep -E 'WATCHOS_DEPLOYMENT_TARGET|IPHONEOS_DEPLOYMENT_TARGET|PRODUCT_BUNDLE_IDENTIFIER|TARGETED_DEVICE_FAMILY' \
      > "$AUDIT_DIR/tooling-raw/watchos-deployment.txt" 2>&1 || true
  fi
else
  echo "xcodebuild skipped (SKIP_XCODEBUILD set or xcodebuild missing); source-only fallback" \
    >> "$AUDIT_DIR/tooling-raw/STATUS.md"
fi
```

### 3. Snapshot complication implementation (WidgetKit vs ClockKit)

The single highest-yield finding category on watchOS 10+. Apps that
still implement complications via `CLKComplicationDataSource` are on
borrowed time — ClockKit is deprecated and complications now ship as
widgets via `WidgetKit` with `.accessoryCircular`, `.accessoryRectangular`,
`.accessoryInline`, and `.accessoryCorner` families.

```bash
{
  echo "=== ClockKit usage (DEPRECATED on watchOS 10+) ==="
  grep -rnE 'CLKComplication(DataSource|Server|Template|Family|Descriptor)|import ClockKit' \
    "$PROJECT_CWD" --include='*.swift' --include='*.m' 2>/dev/null || echo "(none found)"
  echo
  echo "=== WidgetKit complication families (current) ==="
  grep -rnE '\.accessoryCircular|\.accessoryRectangular|\.accessoryInline|\.accessoryCorner|supportedFamilies' \
    "$PROJECT_CWD" --include='*.swift' 2>/dev/null || echo "(none found)"
  echo
  echo "=== WidgetConfiguration / StaticConfiguration / AppIntentConfiguration ==="
  grep -rnE 'StaticConfiguration|AppIntentConfiguration|IntentConfiguration|WidgetConfiguration' \
    "$PROJECT_CWD" --include='*.swift' 2>/dev/null || echo "(none found)"
} > "$AUDIT_DIR/tooling-raw/complication-impl.txt" 2>&1
```

### 4. Snapshot WCSession usage

```bash
{
  echo "=== WCSession activation and delegate ==="
  grep -rnE 'WCSession\.(default|isSupported)|WCSessionDelegate|activationDidCompleteWith|sessionReachabilityDidChange|sessionWatchStateDidChange' \
    "$PROJECT_CWD" --include='*.swift' --include='*.m' 2>/dev/null || echo "(none found)"
  echo
  echo "=== WCSession transfer methods ==="
  grep -rnE 'sendMessage|transferUserInfo|transferFile|updateApplicationContext|transferCurrentComplicationUserInfo' \
    "$PROJECT_CWD" --include='*.swift' --include='*.m' 2>/dev/null || echo "(none found)"
  echo
  echo "=== WCSession state checks ==="
  grep -rnE '\.isReachable|\.isPaired|\.isWatchAppInstalled|\.isComplicationEnabled|\.activationState' \
    "$PROJECT_CWD" --include='*.swift' --include='*.m' 2>/dev/null || echo "(none found)"
} > "$AUDIT_DIR/tooling-raw/wcsession-usage.txt" 2>&1
```

### 5. Snapshot HealthKit workout usage

```bash
{
  echo "=== HKWorkoutSession + HKLiveWorkoutBuilder ==="
  grep -rnE 'HKWorkoutSession|HKLiveWorkoutBuilder|HKWorkoutBuilder|HKWorkoutRouteBuilder|HKLiveWorkoutBuilderDelegate|HKWorkoutSessionDelegate' \
    "$PROJECT_CWD" --include='*.swift' --include='*.m' 2>/dev/null || echo "(none found)"
  echo
  echo "=== HealthKit observers & queries ==="
  grep -rnE 'HKObserverQuery|HKAnchoredObjectQuery|HKStatisticsCollectionQuery|enableBackgroundDelivery' \
    "$PROJECT_CWD" --include='*.swift' --include='*.m' 2>/dev/null || echo "(none found)"
  echo
  echo "=== HealthKit entitlements ==="
  grep -rE 'com\.apple\.developer\.healthkit' "$PROJECT_CWD" --include='*.entitlements' --include='*.plist' 2>/dev/null || echo "(none)"
} > "$AUDIT_DIR/tooling-raw/healthkit-workout-usage.txt" 2>&1
```

### 6. Snapshot watch-target Info.plist subkeys

```bash
{
  for plist in $(find "$PROJECT_CWD" -name 'Info.plist' -not -path '*/.build/*' -not -path '*/Pods/*' 2>/dev/null); do
    if grep -qE 'WKApplication|WKWatchOnly|WKCompanionAppBundleIdentifier|WKBackgroundModes|WKExtensionDelegateClassName' "$plist" 2>/dev/null; then
      echo "=== $plist ==="
      plutil -p "$plist" 2>/dev/null | grep -E 'WK[A-Za-z]+|UIBackgroundModes|CFBundle' || cat "$plist"
      echo
    fi
  done
} > "$AUDIT_DIR/tooling-raw/watch-info-plists.txt" 2>&1
```

### 7. Phase 1 emergency-exit check

**watchOS audit has no emergency-exit triggers beyond the watch-target
gate handled in step 1.** Always proceed.

```bash
EMERGENCY=0
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "$EMERGENCY"
```

### 8. Survey

In conversational text (not a persisted file), note:

- Whether the watch app is **embedded** (inside an iOS app bundle, `WKCompanionAppBundleIdentifier` set) or **independent** (`WKWatchOnly=true`, watchOS 9+)
- `WATCHOS_DEPLOYMENT_TARGET` value — if `< 10.0`, ClockKit is still acceptable; if `>= 10.0`, WidgetKit complications are expected
- Complication implementation seen: WidgetKit-based (modern) vs `CLKComplicationDataSource` (deprecated, breaks eventually)
- WCSession callsites: are both sides (iPhone + Watch) activating? What transfer methods are used?
- HealthKit workout integration: is `HKLiveWorkoutBuilder` present? `enableBackgroundDelivery`?
- Background refresh task types in `WKBackgroundModes`: `WKApplicationRefreshBackgroundTask`, `WKURLSessionRefreshBackgroundTask`, `WKSnapshotRefreshBackgroundTask`, `WKRelevantShortcutRefreshBackgroundTask`, `WKWatchConnectivityRefreshBackgroundTask`
- Always-on display awareness: any `isLuminanceReduced` reads? Any `.privacySensitive()` modifiers?
- Navigation: `NavigationSplitView` (watchOS 10+) vs deprecated `NavigationView`; `TabView` with `.tabViewStyle(.verticalPage)`

This is for the user's situational awareness, not a persisted artifact.

## Outputs

- `$AUDIT_DIR/tooling-raw/watch-targets.txt`
- `$AUDIT_DIR/tooling-raw/watchos-deployment.txt`
- `$AUDIT_DIR/tooling-raw/complication-impl.txt`
- `$AUDIT_DIR/tooling-raw/wcsession-usage.txt`
- `$AUDIT_DIR/tooling-raw/healthkit-workout-usage.txt`
- `$AUDIT_DIR/tooling-raw/watch-info-plists.txt`
- `$AUDIT_DIR/tooling-raw/STATUS.md` (any skipped tools)
- Walker state has `has_watch_target`, `emergency_exit` set

## Outgoing edges

- **`proceed`** → `independent_reviews`. Normal path.
- **`emergency`** → `emergency_exit`. Never taken (no triggers).

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- No watchOS target detected → bail in step 1 with a clear pointer. This is the correct behavior.
- `xcodebuild -showBuildSettings` times out → captured in STATUS.md; orient still proceeds with the grep-based artifacts.
- Project has WATCHOS_DEPLOYMENT_TARGET but no actual watch source files → reviewers flag it as an orphan target in Phase 2 (category: `WatchInstaller`).
