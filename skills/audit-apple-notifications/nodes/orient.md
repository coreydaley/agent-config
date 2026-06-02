# Node: orient

Phase 1 of the framework — collect the notifications artifact snapshot the reviewers need. **Notifications has Phase 1 tooling (entitlement / Info.plist extraction + source grep) but no emergency-exit conditions** — the `orient → emergency_exit` edge is structurally present but never taken.

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

### 0. Detect target platforms

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

`UIBackgroundModes` and silent-push lifecycle apply on iOS / iPadOS / visionOS only — if the detected platforms list excludes iOS-family targets, the `background-modes.txt` snapshot may be empty; that's a status note, not a failure.

### 1. Extract aps-environment from every .entitlements file

The `aps-environment` entitlement is the single highest-yield artifact for this audit. A `development` value in a Release-config entitlements file silently breaks push on every Release device — the APNs handshake uses the sandbox gateway and production tokens are rejected.

```bash
{
  find "$PROJECT_CWD" \( -name "*.entitlements" -o -name "*.plist" \) \
    -not -path '*/.build/*' -not -path '*/DerivedData/*' -not -path '*/Pods/*' \
    -print0 2>/dev/null | while IFS= read -r -d '' f; do
    if plutil -extract aps-environment raw -o - "$f" >/dev/null 2>&1; then
      VAL=$(plutil -extract aps-environment raw -o - "$f" 2>/dev/null)
      echo "$f → aps-environment=$VAL"
    fi
  done
} > "$AUDIT_DIR/tooling-raw/aps-environments.txt" 2>&1 || true
```

### 2. Extract UIBackgroundModes from every Info.plist

`remote-notification` in `UIBackgroundModes` is required for silent push (`content-available: 1`) to wake the app. Its absence is the single most common reason silent push "doesn't work."

```bash
{
  find "$PROJECT_CWD" -name "Info.plist" \
    -not -path '*/.build/*' -not -path '*/DerivedData/*' -not -path '*/Pods/*' \
    -print0 2>/dev/null | while IFS= read -r -d '' f; do
    echo "=== $f ==="
    plutil -extract UIBackgroundModes raw -o - "$f" 2>/dev/null || echo "(no UIBackgroundModes)"
    echo
  done
} > "$AUDIT_DIR/tooling-raw/background-modes.txt" 2>&1 || true
```

### 3. Grep source for UNUserNotificationCenter calls

```bash
grep -rEn --include='*.swift' --include='*.m' \
  -e 'UNUserNotificationCenter\.current\(\)' \
  -e 'requestAuthorization' \
  -e 'getNotificationSettings' \
  -e '\.notDetermined' -e '\.authorized' -e '\.denied' -e '\.provisional' \
  "$PROJECT_CWD" 2>/dev/null \
  > "$AUDIT_DIR/tooling-raw/un-center-calls.txt" || true
```

### 4. Grep source for categories, actions, and intents donation

```bash
grep -rEn --include='*.swift' --include='*.m' \
  -e 'UNNotificationCategory' \
  -e 'UNNotificationAction' \
  -e 'UNTextInputNotificationAction' \
  -e 'setNotificationCategories' \
  -e 'categoryIdentifier' \
  "$PROJECT_CWD" 2>/dev/null \
  > "$AUDIT_DIR/tooling-raw/categories-and-actions.txt" || true

grep -rEn --include='*.swift' --include='*.m' \
  -e 'INSendMessageIntent' \
  -e 'INPersonHandle' \
  -e 'INInteraction' \
  -e '\.donate(' \
  "$PROJECT_CWD" 2>/dev/null \
  > "$AUDIT_DIR/tooling-raw/intents-donation.txt" || true
```

### 5. Detect Notification Service / Content Extension targets

```bash
{
  echo "=== Notification Service Extensions ==="
  grep -lrE --include='*.swift' --include='*.m' \
    'UNNotificationServiceExtension' "$PROJECT_CWD" 2>/dev/null || true
  echo
  echo "=== NSExtensionPointIdentifier matches ==="
  grep -rEn --include='Info.plist' \
    -e 'com.apple.usernotifications.service' \
    -e 'com.apple.usernotifications.content-extension' \
    "$PROJECT_CWD" 2>/dev/null || true
} > "$AUDIT_DIR/tooling-raw/nse-targets.txt" 2>&1 || true

{
  echo "=== Notification Content Extensions ==="
  grep -lrE --include='*.swift' --include='*.m' \
    'UNNotificationContentExtension' "$PROJECT_CWD" 2>/dev/null || true
} > "$AUDIT_DIR/tooling-raw/nce-targets.txt" 2>&1 || true
```

### 6. Locate delegate-wiring sites and payload-string literals

```bash
grep -rEn --include='*.swift' --include='*.m' \
  -e 'UNUserNotificationCenter\.current\(\)\.delegate' \
  -e 'willPresent notification' \
  -e 'didReceive response' \
  -e 'didRegisterForRemoteNotificationsWithDeviceToken' \
  -e 'didReceiveRemoteNotification' \
  "$PROJECT_CWD" 2>/dev/null \
  > "$AUDIT_DIR/tooling-raw/delegate-wiring.txt" || true

# Payload-shape literals that might appear in Swift source (mock pushes,
# integration tests, server SDK glue, debug-trigger UI):
grep -rEn --include='*.swift' --include='*.m' --include='*.json' \
  -e 'apns-push-type' -e 'apns-priority' -e 'apns-topic' \
  -e 'apns-collapse-id' -e 'apns-expiration' -e 'mutable-content' \
  -e 'content-available' -e 'interruption-level' -e 'relevance-score' \
  -e 'thread-id' \
  "$PROJECT_CWD" 2>/dev/null \
  > "$AUDIT_DIR/tooling-raw/payload-strings.txt" || true
```

### 7. Phase 1 emergency-exit check

**Notifications has no emergency-exit triggers.** Always proceed.

```bash
EMERGENCY=0
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "$EMERGENCY"
```

### 8. Survey

In conversational text (not a persisted file), note:

- Which targets declare `aps-environment`, and whether the value matches the build configuration the target ships in (development vs production)
- Whether `UIBackgroundModes` contains `remote-notification` in the app target's Info.plist and whether the app handles silent push (`content-available: 1`)
- Whether `UNUserNotificationCenter.current().requestAuthorization(options:)` exists at all; which options it requests (`.alert`, `.badge`, `.sound`, `.provisional`, `.criticalAlert`, `.timeSensitive`)
- Whether authorization is requested at launch (anti-pattern) or at a contextual moment (mid-onboarding, after a user action)
- Whether `UNUserNotificationCenter.current().delegate` is assigned, and at what lifecycle point (early-app vs after first view-load)
- Whether the project ships a Notification Service Extension (NSE) target — required for rich notifications, encrypted-payload decryption, and dynamic content modification
- Whether the project donates `INSendMessageIntent` before scheduling notifications (Communication Notifications affordance)
- Use of `interruptionLevel: .timeSensitive` / `.critical` and whether the corresponding entitlements (`com.apple.developer.usernotifications.time-sensitive`, `com.apple.developer.usernotifications.critical-alerts`) are present
- Any Swift source containing literal `apns-push-type` / `apns-priority` payload keys — suggests a server SDK pattern is co-located, or a dev-trigger UI exists

**If no Swift / Obj-C source found and no entitlement files reference `aps-environment`**: notify and stop — the project doesn't use Apple notifications.

This is for the user's situational awareness, not a persisted artifact.

## Outputs

- `$AUDIT_DIR/tooling-raw/` populated with whatever was available
- `$AUDIT_DIR/tooling-raw/STATUS.md` documents skipped tools
- Walker state has `emergency_exit` set

## Outgoing edges

- **`proceed`** → `independent_reviews`. Normal path.
- **`emergency`** → `emergency_exit`. Never taken (no triggers).

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- No `.entitlements` files anywhere → `aps-environments.txt` will be empty; not a failure, just means the project doesn't use APNs. The reviewers will still find local-notification findings if `UNUserNotificationCenter` calls exist.
- `plutil` missing → unlikely on macOS; if it is, the grep-based fallback (`grep -A1 aps-environment`) still produces a usable snapshot. Document in STATUS.md.
- Very large source tree → grep may take longer than usual; the tooling commands are bounded by `find` traversal, not size, so this remains tractable.
