# Node: orient

Phase 1 of the framework — detect the visionOS target, then capture the spatial-scene and ARKit-provider surface the reviewers will work against. **visionOS has Phase 1 tooling but no emergency-exit conditions** — the `orient → emergency_exit` edge is structurally present but never taken.

The single highest-leverage Phase 1 activity is *confirming there is a visionOS target at all*. If `XROS_DEPLOYMENT_TARGET` is unset everywhere and no source uses RealityKit + visionOS scene types, this audit has nothing to review and should bail with a pointer back to `/audit-apple-adaptivity` or the iOS / macOS design audits.

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only)
- Optional env vars: `SKIP_XCODEBUILD=1` skips `xcodebuild`-driven steps (CI without Xcode, or projects without a working scheme)

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
TO=$(bash ~/.claude/lib/audit-runner.sh timeout-bin)
[ -z "$TO" ] && echo "no timeout command available; install via 'brew install coreutils' for tool timeouts" \
  >> "$AUDIT_DIR/tooling-raw/STATUS.md"
```

## Steps

### 1. Detect visionOS target

```bash
WORKSPACE=$(ls "$PROJECT_CWD"/*.xcworkspace 2>/dev/null | head -1)
PROJECT=$(ls "$PROJECT_CWD"/*.xcodeproj 2>/dev/null | head -1)
PACKAGE_SWIFT="$PROJECT_CWD/Package.swift"

if [ -z "${SKIP_XCODEBUILD:-}" ] && command -v xcodebuild >/dev/null; then
  if [ -n "$WORKSPACE" ]; then
    xcodebuild -list -workspace "$WORKSPACE" > "$AUDIT_DIR/tooling-raw/schemes.txt" 2>&1 || true
  elif [ -n "$PROJECT" ]; then
    xcodebuild -list -project "$PROJECT" > "$AUDIT_DIR/tooling-raw/schemes.txt" 2>&1 || true
  fi
  SCHEME=$(awk '/Schemes:/{flag=1;next}/^$/{flag=0}flag{print $1; exit}' "$AUDIT_DIR/tooling-raw/schemes.txt" 2>/dev/null)
  if [ -n "$SCHEME" ]; then
    XC_ARGS=()
    [ -n "$WORKSPACE" ] && XC_ARGS+=(-workspace "$WORKSPACE") || XC_ARGS+=(-project "$PROJECT")
    ${TO:+$TO 120} xcodebuild -showBuildSettings "${XC_ARGS[@]}" -scheme "$SCHEME" -configuration Debug \
      > "$AUDIT_DIR/tooling-raw/build-settings-debug.txt" 2>&1 || true
    ${TO:+$TO 120} xcodebuild -showBuildSettings "${XC_ARGS[@]}" -scheme "$SCHEME" -configuration Release \
      > "$AUDIT_DIR/tooling-raw/build-settings-release.txt" 2>&1 || true
  fi
fi

# visionOS-target detection — any of these three signals counts
HAS_XROS_BUILD=$(grep -l '^[[:space:]]*XROS_DEPLOYMENT_TARGET' "$AUDIT_DIR/tooling-raw/"build-settings-*.txt 2>/dev/null | head -1)
HAS_XROS_PACKAGE=$(grep -l '\.visionOS' "$PACKAGE_SWIFT" 2>/dev/null)
HAS_REALITYKIT=$(grep -rln 'import RealityKit\|ImmersiveSpace\|WindowGroup\|RealityView' "$PROJECT_CWD" \
  --include='*.swift' --exclude-dir='.build' --exclude-dir='Pods' 2>/dev/null | head -1)

if [ -z "$HAS_XROS_BUILD" ] && [ -z "$HAS_XROS_PACKAGE" ] && [ -z "$HAS_REALITYKIT" ]; then
  echo "No visionOS target detected (no XROS_DEPLOYMENT_TARGET, no .visionOS in Package.swift, no RealityKit + visionOS scene-type usage)." \
    > "$AUDIT_DIR/tooling-raw/visionos-targets.txt"
  bail "audit-apple-visionos: scope has no visionOS target. Use /audit-apple-adaptivity for visionOS *windowing* as part of broader adaptive UI, or the iOS / macOS design audits."
fi
```

### 2. Capture visionOS-target build settings

```bash
{
  echo "=== XROS_DEPLOYMENT_TARGET (Debug) ==="
  grep -E '^[[:space:]]*XROS_DEPLOYMENT_TARGET|^[[:space:]]*SUPPORTED_PLATFORMS|^[[:space:]]*TARGETED_DEVICE_FAMILY' \
    "$AUDIT_DIR/tooling-raw/build-settings-debug.txt" 2>/dev/null
  echo
  echo "=== XROS_DEPLOYMENT_TARGET (Release) ==="
  grep -E '^[[:space:]]*XROS_DEPLOYMENT_TARGET|^[[:space:]]*SUPPORTED_PLATFORMS|^[[:space:]]*TARGETED_DEVICE_FAMILY' \
    "$AUDIT_DIR/tooling-raw/build-settings-release.txt" 2>/dev/null
  echo
  [ -f "$PACKAGE_SWIFT" ] && { echo "=== Package.swift platforms ==="; grep -E 'platforms|\.visionOS' "$PACKAGE_SWIFT"; }
} > "$AUDIT_DIR/tooling-raw/visionos-targets.txt" 2>&1
```

### 3. Snapshot spatial scene-type usage

```bash
{
  echo "=== ImmersiveSpace usages ==="
  grep -rn 'ImmersiveSpace\|openImmersiveSpace\|dismissImmersiveSpace\|ImmersionStyle\|\.mixed\|\.progressive\|\.full' \
    "$PROJECT_CWD" --include='*.swift' --exclude-dir='.build' --exclude-dir='Pods' 2>/dev/null
  echo
  echo "=== WindowGroup / Window / Volume usages ==="
  grep -rn 'WindowGroup\|^.*\bWindow(\|\.windowStyle\|\.volumetric\|defaultSize' \
    "$PROJECT_CWD" --include='*.swift' --exclude-dir='.build' --exclude-dir='Pods' 2>/dev/null
  echo
  echo "=== RealityView usages ==="
  grep -rn 'RealityView\|RealityViewContent\|Entity(named:\|loadModel\|Entity\.load' \
    "$PROJECT_CWD" --include='*.swift' --exclude-dir='.build' --exclude-dir='Pods' 2>/dev/null
  echo
  echo "=== Hover effects + spatial taps ==="
  grep -rn '\.hoverEffect\|HoverEffectComponent\|SpatialTapGesture\|onSpatialTap' \
    "$PROJECT_CWD" --include='*.swift' --exclude-dir='.build' --exclude-dir='Pods' 2>/dev/null
  echo
  echo "=== Ornaments ==="
  grep -rn '\.ornament(' \
    "$PROJECT_CWD" --include='*.swift' --exclude-dir='.build' --exclude-dir='Pods' 2>/dev/null
} > "$AUDIT_DIR/tooling-raw/scene-types.txt" 2>&1
```

### 4. Snapshot ARKit-provider usage

```bash
{
  echo "=== ARKitSession + providers ==="
  grep -rn 'ARKitSession\|HandTrackingProvider\|WorldTrackingProvider\|SceneReconstructionProvider\|PlaneDetectionProvider\|ImageTrackingProvider' \
    "$PROJECT_CWD" --include='*.swift' --exclude-dir='.build' --exclude-dir='Pods' 2>/dev/null
  echo
  echo "=== WorldAnchor usage ==="
  grep -rn 'WorldAnchor\|loadAnchors\|removeAnchor' \
    "$PROJECT_CWD" --include='*.swift' --exclude-dir='.build' --exclude-dir='Pods' 2>/dev/null
  echo
  echo "=== Spatial audio (PHASE + SpatialAudioComponent) ==="
  grep -rn 'PHASEEngine\|PHASESource\|SpatialAudioComponent\|AmbientAudioComponent\|ChannelAudioComponent' \
    "$PROJECT_CWD" --include='*.swift' --exclude-dir='.build' --exclude-dir='Pods' 2>/dev/null
} > "$AUDIT_DIR/tooling-raw/arkit-providers.txt" 2>&1
```

### 5. Snapshot entitlements, Info.plist purpose strings, USDZ inventory

```bash
find "$PROJECT_CWD" -name "*.entitlements" -not -path '*/.build/*' \
  -exec sh -c 'echo "=== $1 ==="; cat "$1"; echo' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/entitlements-per-target.txt" 2>&1 || true

find "$PROJECT_CWD" -name "Info.plist" -not -path '*/.build/*' -not -path '*/Pods/*' \
  -exec sh -c 'echo "=== $1 ==="; plutil -p "$1" 2>/dev/null || cat "$1"; echo' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/info-plists.txt" 2>&1 || true

# USDZ inventory — size matters for main-thread-load Critical findings
find "$PROJECT_CWD" \( -name "*.usdz" -o -name "*.usda" -o -name "*.reality" \) \
  -not -path '*/.build/*' -not -path '*/Pods/*' -exec ls -l {} \; \
  > "$AUDIT_DIR/tooling-raw/usdz-assets.txt" 2>&1 || true
```

### 6. Phase 1 emergency-exit check

**visionOS has no emergency-exit triggers.** Always proceed.

```bash
EMERGENCY=0
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "$EMERGENCY"
```

### 7. Survey

In conversational text (not a persisted file), note:

- visionOS target list (which targets have `XROS_DEPLOYMENT_TARGET` set; the deployment-target version)
- Scene-type mix: how many `WindowGroup` vs `ImmersiveSpace` vs `Volume`; whether `ImmersionStyle` is `.mixed`, `.progressive`, or `.full`; presence of `defaultSize` in volumetric units
- RealityKit usage shape: `RealityView` count, USDZ load paths (`Entity(named:in:)` vs `Entity.load` async), presence of Reality Composer Pro packages
- ARKit provider mix: `HandTrackingProvider` (requires entitlement + purpose string), `WorldTrackingProvider` (world anchors), `SceneReconstructionProvider`, `PlaneDetectionProvider`
- Entitlements: presence of `com.apple.developer.arkit.hand-tracking` and matching Info.plist `NSHandsTrackingUsageDescription`
- USDZ assets > ~10MB — main-thread-load candidates for "Memory crash" compound finding
- Spatial audio shape: `PHASEEngine` + `SpatialAudioComponent` vs ad-hoc mono audio sources
- Hover-effect coverage: tappable elements that lack `.hoverEffect()`

This is for the user's situational awareness, not a persisted artifact.

## Outputs

- `$AUDIT_DIR/tooling-raw/` populated (build-settings-*.txt, visionos-targets.txt, scene-types.txt, arkit-providers.txt, entitlements-per-target.txt, info-plists.txt, usdz-assets.txt)
- `$AUDIT_DIR/tooling-raw/STATUS.md` documents skipped tools
- Walker state has `emergency_exit` set

## Outgoing edges

- **`proceed`** → `independent_reviews`. Normal path.
- **`emergency`** → `emergency_exit`. Never taken (no triggers).

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- No visionOS target detected → bail in step 1 with a pointer to `/audit-apple-adaptivity` or the iOS / macOS design audits.
- `xcodebuild` times out → captured in the log; orient proceeds with source-only reading.
- `xcodebuild -list` returns no schemes → flagged as a finding in Phase 2 under `SceneTypes` / project-shape coverage.
