# Node: orient

Phase 1 of the framework — run audit-specific tooling into `$AUDIT_DIR/tooling-raw/` and build a brief orientation note. **Apple App Store Review has Phase 1 tooling but no emergency-exit gate** — App Review rejection is not a "now" event the way a leaked credential is.

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

The iOS App Store and Mac App Store apply somewhat different guideline subsections (App Sandbox requirement, ATT applicability, IAP rules for non-consumable Mac software). Record detected platforms so reviewers can tag each finding with the platform(s) it applies to.

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

App Store Review tooling is grep/plist-based — surface IAP usage, push usage, Sign in with Apple presence, third-party sign-in, and placeholder content for the reviewers. **Never block on a missing tool.**

```bash
# Snapshot Info.plist (full)
find "$PROJECT_CWD" -name "Info.plist" -not -path '*/.*' -not -path '*/Pods/*' \
  -exec sh -c 'echo "=== $1 ==="; /usr/libexec/PlistBuddy -c "Print" "$1" 2>/dev/null' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/info-plist-full.txt" 2>&1

# Privacy Manifest snapshot
find "$PROJECT_CWD" -name "PrivacyInfo.xcprivacy" -not -path '*/.*' \
  -exec sh -c 'echo "=== $1 ==="; cat "$1"' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/privacy-manifests.txt" 2>&1

# Detect IAP / StoreKit
{
  echo "=== StoreKit usage ===";
  grep -rn "StoreKit\|SKProduct\|SKPaymentQueue\|Product.products\|Transaction\." \
    --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50;
  echo;
  echo "=== Subscription terminology ===";
  grep -rn -i "subscription\|auto-renew\|free trial\|introductory" \
    --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -30;
} > "$AUDIT_DIR/tooling-raw/storekit-usage.txt"

# Detect SiriKit / Push / Sign in with Apple
{
  echo "=== Push notifications ===";
  grep -rn "UNUserNotificationCenter\|registerForRemoteNotifications" \
    --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -30;
  echo;
  echo "=== Sign in with Apple ===";
  grep -rn "ASAuthorizationAppleID\|AuthenticationServices" \
    --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -20;
  echo;
  echo "=== Third-party sign-in ===";
  grep -rn -i "GoogleSignIn\|FacebookLogin\|TwitterKit\|FBSDKLoginManager" \
    --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -20;
} > "$AUDIT_DIR/tooling-raw/auth-and-push.txt"

# Detect placeholder content
{
  echo "=== Placeholder text ===";
  grep -rn -i "lorem ipsum\|todo:\|fixme:\|placeholder\|coming soon\|test123\|example.com" \
    --include="*.swift" --include="*.json" "$PROJECT_CWD" 2>/dev/null | head -50;
} > "$AUDIT_DIR/tooling-raw/placeholder-content.txt"
```

### 2. Emergency-exit check

**None for this audit.** App Review rejection is not a "now" event — it's a sprint blocker, surfaced via the Submission Blocker tier in the final report. The `orient → emergency_exit` edge in the graph stays for graph uniformity but is never taken here.

### 3. Survey

In conversational text (not a persisted file), note:

- Resolved scope (`$PROJECT_CWD`) and any obvious sub-paths (`*.xcodeproj/`, `Package.swift`, `Podfile`, `fastlane/metadata/`)
- IAP usage, push usage, Sign in with Apple presence, third-party sign-in presence, placeholder content (from `tooling-raw/`)
- Category-specific concerns: medical app? kids category? HealthKit? location-based? UGC?
- Any App Store Connect metadata checked into the repo (Fastlane metadata, descriptions, screenshots) — if present, audit it for accuracy
- App category and audience (kids? regulated? consumer? B2B?) — many guidelines are category-specific
- **If no Swift/Apple source found**: notify the user and bail; this audit doesn't apply

This is for the user's situational awareness, not a persisted artifact.

### 4. Persist any run-scoped state Phase 2 needs

```bash
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "0"
```

## Outputs

- `$AUDIT_DIR/tooling-raw/` populated with whatever tools were available
- `$AUDIT_DIR/tooling-raw/STATUS.md` documents skipped tools
- `$AUDIT_DIR/tooling-raw/info-plist-full.txt`, `privacy-manifests.txt`, `storekit-usage.txt`, `auth-and-push.txt`, `placeholder-content.txt` exist (may be empty)
- Walker state has `emergency_exit=0`

## Outgoing edges

- **`proceed`** → `independent_reviews`. Always taken in this audit.
- **`emergency`** → `emergency_exit`. Never taken in this audit (kept for graph uniformity).

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- A tool times out → captured in its `.log` file; orient proceeds. Phase 2 reviewers see the partial output.
- All tooling fails / missing → `STATUS.md` documents the degradation; orient still proceeds. Phase 2 reviewers do more manual code reading.
- No Swift/Apple source in scope → this audit doesn't apply; notify the user and stop before Phase 2.
