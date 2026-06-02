# Node: orient

Phase 1 of the framework — run audit-specific tooling into `$AUDIT_DIR/tooling-raw/`, scan for emergency-exit conditions, build a brief orientation note. **Apple privacy has Phase 1 tooling AND an emergency-exit gate** — the gate fires on App Store submission blockers (missing Privacy Manifest, third-party SDK without manifest, IDFA without ATT).

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only)

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
TO=$(bash ~/.claude/lib/audit-runner.sh timeout-bin)
[ -z "$TO" ] && echo "⚠️ no timeout command available; install via 'brew install coreutils' for tool timeouts" \
  >> "$AUDIT_DIR/tooling-raw/STATUS.md"
```

## Steps

### 0. Detect target Apple platforms

Privacy requirements differ across Apple platforms — ATT applies to iOS / iPadOS / tvOS / visionOS; App Privacy Report is iOS-only; PrivacyInfo.xcprivacy is platform-wide. Record detected platforms so reviewers can calibrate severity and tag findings with platform applicability.

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

### 1. Run Phase 1 tooling

Privacy tooling is almost entirely Apple-artifact inspection — Privacy Manifests, Info.plist, third-party SDK directories, IDFA/ATT call sites, required-reason API candidates. **Never block on a missing tool.**

```bash
# Privacy Manifest snapshots (app + every SDK)
find "$PROJECT_CWD" -name "PrivacyInfo.xcprivacy" -not -path '*/.*' \
  -exec sh -c 'echo "=== $1 ==="; cat "$1"' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/privacy-manifests.txt" 2>&1 || true

# Info.plist purpose strings
find "$PROJECT_CWD" -name "Info.plist" -not -path '*/.*' -not -path '*/Pods/*' \
  -exec sh -c 'echo "=== $1 ==="; \
    /usr/libexec/PlistBuddy -c "Print" "$1" 2>/dev/null \
    | grep -E "UsageDescription|NSApp|NSPrivacy|UIRequires" || true' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/info-plist-privacy.txt" 2>&1 || true

# List third-party SDKs (SPM + Cocoapods + binary frameworks)
{
  echo "=== SPM dependencies ===";
  [ -f "$PROJECT_CWD/Package.resolved" ] && cat "$PROJECT_CWD/Package.resolved";
  echo;
  echo "=== Cocoapods ===";
  [ -f "$PROJECT_CWD/Podfile.lock" ] && cat "$PROJECT_CWD/Podfile.lock";
  echo;
  echo "=== XCFrameworks ===";
  find "$PROJECT_CWD" -name "*.xcframework" -not -path '*/.*' -not -path '*/build/*' \
    -maxdepth 4 2>/dev/null;
} > "$AUDIT_DIR/tooling-raw/third-party-sdks.txt" 2>&1 || true

# Check for IDFA / ATT usage
{
  echo "=== IDFA usage ===";
  grep -rn "ASIdentifierManager\|advertisingIdentifier" --include="*.swift" "$PROJECT_CWD" 2>/dev/null;
  echo;
  echo "=== ATT usage ===";
  grep -rn "ATTrackingManager\|requestTrackingAuthorization" --include="*.swift" "$PROJECT_CWD" 2>/dev/null;
} > "$AUDIT_DIR/tooling-raw/idfa-att.txt" 2>&1 || true

# Required-reason API candidates
{
  echo "=== UserDefaults ===";
  grep -rn "UserDefaults" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50;
  echo;
  echo "=== File timestamps ===";
  grep -rn "creationDate\|contentModificationDate\|contentAccessDate\|attributeModificationDate\|fileAttributes\|getattrlist" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50;
  echo;
  echo "=== System boot time ===";
  grep -rn "systemUptime\|kern.boottime" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50;
  echo;
  echo "=== Disk space ===";
  grep -rn "volumeAvailableCapacity\|systemFreeSize" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50;
  echo;
  echo "=== Active keyboards ===";
  grep -rn "activeInputModes\|UITextInputMode" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50;
} > "$AUDIT_DIR/tooling-raw/required-reason-candidates.txt" 2>&1 || true

# Detect distribution channel hints (App Store provisioning vs. enterprise/dev).
{
  echo "=== Provisioning profiles ===";
  find "$PROJECT_CWD" -name "*.mobileprovision" -not -path '*/.*' 2>/dev/null;
  echo;
  echo "=== Xcode export options ===";
  find "$PROJECT_CWD" -name "ExportOptions.plist" -not -path '*/.*' \
    -exec sh -c 'echo "=== $1 ==="; cat "$1"' _ {} \; 2>/dev/null;
} > "$AUDIT_DIR/tooling-raw/distribution-channel.txt" 2>&1 || true
```

### 2. Emergency-exit check — App Store rejection imminent

Apple privacy has an emergency-exit gate. After tooling runs, if any of these are true, halt before Phase 2:

1. **Project ships to App Store** (Xcode project with App Store distribution provisioning, not a side project) **AND no `PrivacyInfo.xcprivacy` exists** — App Review will reject.
2. **Third-party SDK on Apple's required-manifest list is bundled without its `PrivacyInfo.xcprivacy`** (Firebase, Branch, GoogleSignIn, AppsFlyer, Amplitude, Adjust, OneSignal, etc.) — App Review will reject.
3. **IDFA accessed (`ASIdentifierManager`, `advertisingIdentifier`) but no ATT flow** (`ATTrackingManager.requestTrackingAuthorization`) in the code — App Review will reject.

```bash
EMERGENCY=0
EMERGENCY_REASONS=""

# 1. App-level Privacy Manifest absent?
APP_MANIFEST_COUNT=$(grep -c "=== " "$AUDIT_DIR/tooling-raw/privacy-manifests.txt" 2>/dev/null || echo 0)
SHIPS_APPSTORE=0
if grep -qi "app-store\|appstore" "$AUDIT_DIR/tooling-raw/distribution-channel.txt" 2>/dev/null \
   || ls "$PROJECT_CWD"/*.xcodeproj >/dev/null 2>&1; then
  SHIPS_APPSTORE=1
fi
if [ "$SHIPS_APPSTORE" -eq 1 ] && [ "$APP_MANIFEST_COUNT" -eq 0 ]; then
  EMERGENCY=1
  EMERGENCY_REASONS="$EMERGENCY_REASONS\n- App Store-bound project has NO PrivacyInfo.xcprivacy"
fi

# 2. Third-party SDK without manifest? Check Apple's required-SDK list.
REQUIRED_SDKS="Firebase|Branch|GoogleSignIn|AppsFlyer|Amplitude|Adjust|OneSignal|FBSDK|FacebookSDK|Mixpanel|Segment|Crashlytics|FirebaseAnalytics"
SDKS_PRESENT=$(grep -iE "$REQUIRED_SDKS" "$AUDIT_DIR/tooling-raw/third-party-sdks.txt" 2>/dev/null | head -10)
if [ -n "$SDKS_PRESENT" ]; then
  # For each named SDK present, check if a matching PrivacyInfo.xcprivacy exists nearby.
  for sdk in $(echo "$SDKS_PRESENT" | grep -oiE "$REQUIRED_SDKS" | sort -u); do
    if ! grep -qi "$sdk" "$AUDIT_DIR/tooling-raw/privacy-manifests.txt" 2>/dev/null; then
      EMERGENCY=1
      EMERGENCY_REASONS="$EMERGENCY_REASONS\n- Required-list SDK '$sdk' present without its PrivacyInfo.xcprivacy"
    fi
  done
fi

# 3. IDFA accessed without ATT flow?
IDFA_HITS=$(grep -c "ASIdentifierManager\|advertisingIdentifier" "$AUDIT_DIR/tooling-raw/idfa-att.txt" 2>/dev/null || echo 0)
ATT_HITS=$(grep -c "ATTrackingManager\|requestTrackingAuthorization" "$AUDIT_DIR/tooling-raw/idfa-att.txt" 2>/dev/null || echo 0)
if [ "$IDFA_HITS" -gt 0 ] && [ "$ATT_HITS" -eq 0 ]; then
  EMERGENCY=1
  EMERGENCY_REASONS="$EMERGENCY_REASONS\n- IDFA accessed but no ATTrackingManager.requestTrackingAuthorization flow"
fi

scripts/walk.sh set --state "$STATE" --key emergency_reasons --value "$EMERGENCY_REASONS"
```

If `--allow-noncompliant` is set in `$ARGUMENTS`, proceed but flag every Submission Blocker as Critical in synthesis instead of halting. **In all other cases**, if `EMERGENCY=1`, take the `emergency_exit` outgoing edge. Manually re-confirm before exiting — the `appstore` distribution detection is heuristic and side projects with `*.xcodeproj` should not trigger.

### 3. Survey

In conversational text (not a persisted file), note:

- Resolved scope (`$PROJECT_CWD`) and any obvious sub-paths (`*.xcodeproj/`, `Package.swift`, `Podfile`)
- Whether the app has a `PrivacyInfo.xcprivacy` (from `privacy-manifests.txt`)
- Whether bundled SDKs have manifests (from `privacy-manifests.txt` vs. `third-party-sdks.txt`)
- Whether IDFA is accessed and whether ATT is implemented (from `idfa-att.txt`)
- Declared purpose strings and supported locales (from `info-plist-privacy.txt`)
- Distribution channel hint (App Store vs. Enterprise vs. Developer ID vs. side-load) — calibrates severity
- Required-reason API candidates for cross-reference

This is for the user's situational awareness, not a persisted artifact.

### 4. Persist any run-scoped state Phase 2 needs

```bash
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "$EMERGENCY"
```

## Outputs

- `$AUDIT_DIR/tooling-raw/` populated with privacy-manifests.txt, info-plist-privacy.txt, third-party-sdks.txt, idfa-att.txt, required-reason-candidates.txt, distribution-channel.txt
- `$AUDIT_DIR/tooling-raw/STATUS.md` documents skipped tools
- Walker state has `emergency_exit` and `emergency_reasons` set

## Outgoing edges

- **`proceed`** → `independent_reviews`. Normal path. Phase 1 ran, no submission-blocker emergency.
- **`emergency`** → `emergency_exit`. App Store rejection is imminent; the audit halts before Phase 2.

```bash
if [ "$EMERGENCY" -eq 1 ]; then
  scripts/walk.sh transition --state "$STATE" --from orient --to emergency_exit --condition emergency
else
  scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
fi
```

## Failure modes

- A tool times out → captured in its `.log` file; orient proceeds. Phase 2 reviewers see the partial output.
- All tooling fails / missing → `STATUS.md` documents the degradation; orient still proceeds. Phase 2 reviewers do more manual code reading.
- `appstore` distribution heuristic false-positives on a side project → human judgment call before taking the `emergency` edge; if the project isn't actually submitting to App Store, take `proceed` and let Phase 2 flag the missing manifest as High rather than emergency-exiting.
