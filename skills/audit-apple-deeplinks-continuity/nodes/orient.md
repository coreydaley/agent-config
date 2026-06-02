# Node: orient

Phase 1 of the framework — collect the deep-links / continuity artifact snapshot the reviewers need. **Deep-links has Phase 1 tooling (entitlement + Info.plist extraction + grep for the continuity APIs) but no emergency-exit conditions** — the `orient → emergency_exit` edge is structurally present but never taken.

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only)

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
TO=$(bash ~/.claude/lib/audit-runner.sh timeout-bin)
[ -z "$TO" ] && echo "no timeout command available; install via 'brew install coreutils' for tool timeouts" \
  >> "$AUDIT_DIR/tooling-raw/STATUS.md"
```

## Steps

### 1. Snapshot Associated Domains entitlement

The single highest-yield Phase 1 artifact. `com.apple.developer.associated-domains` is what binds the app to one or more domains for `applinks:`, `webcredentials:`, `activitycontinuation:`, and `appclips:` services. A missing or `?mode=developer`-suffixed entry on a Release build is the root cause of "Universal Links silently broken".

```bash
{
  echo "=== Associated Domains entries ==="
  find "$PROJECT_CWD" -name "*.entitlements" -not -path '*/.build/*' -not -path '*/Pods/*' \
    -exec sh -c '
      echo "--- $1 ---"
      plutil -extract com.apple.developer.associated-domains xml1 -o - "$1" 2>/dev/null \
        || echo "(no associated-domains key)"
      echo
    ' _ {} \;
} > "$AUDIT_DIR/tooling-raw/associated-domains.txt" 2>&1 || true
```

### 2. Snapshot Info.plist URL declarations

```bash
# CFBundleURLTypes — declared incoming custom URL schemes
{
  echo "=== CFBundleURLTypes per Info.plist ==="
  find "$PROJECT_CWD" -name "Info.plist" -not -path '*/.build/*' -not -path '*/Pods/*' \
    -exec sh -c '
      echo "--- $1 ---"
      plutil -extract CFBundleURLTypes xml1 -o - "$1" 2>/dev/null || echo "(no CFBundleURLTypes)"
      echo
    ' _ {} \;
} > "$AUDIT_DIR/tooling-raw/url-types.txt" 2>&1 || true

# LSApplicationQueriesSchemes — outgoing schemes the app probes
{
  echo "=== LSApplicationQueriesSchemes per Info.plist ==="
  find "$PROJECT_CWD" -name "Info.plist" -not -path '*/.build/*' -not -path '*/Pods/*' \
    -exec sh -c '
      echo "--- $1 ---"
      plutil -extract LSApplicationQueriesSchemes xml1 -o - "$1" 2>/dev/null \
        || echo "(no LSApplicationQueriesSchemes)"
      echo
    ' _ {} \;
} > "$AUDIT_DIR/tooling-raw/queries-schemes.txt" 2>&1 || true

# NSUserActivityTypes — declared NSUserActivity activity types for Handoff / Spotlight / Siri
{
  echo "=== NSUserActivityTypes per Info.plist ==="
  find "$PROJECT_CWD" -name "Info.plist" -not -path '*/.build/*' -not -path '*/Pods/*' \
    -exec sh -c '
      echo "--- $1 ---"
      plutil -extract NSUserActivityTypes xml1 -o - "$1" 2>/dev/null || echo "(no NSUserActivityTypes)"
      echo
    ' _ {} \;
} > "$AUDIT_DIR/tooling-raw/user-activity-types.txt" 2>&1 || true
```

### 3. Grep for continuity APIs

```bash
# application(_:continue:) / scene(_:continue:) / .onContinueUserActivity — Universal Link + Handoff entry points
{
  echo "=== application(_:continue:) and .onContinueUserActivity sites ==="
  grep -RInE 'application\(_:continue:|application\(_, *continue|scene\(_:continueUserActivity|onContinueUserActivity\(' \
    --include='*.swift' --include='*.m' --include='*.mm' \
    "$PROJECT_CWD" 2>/dev/null \
    | grep -v '/.build/' | grep -v '/Pods/' | grep -v 'DerivedData' || echo "(no matches)"
} > "$AUDIT_DIR/tooling-raw/continue-useractivity.txt" 2>&1

# NSUserActivity construction + becomeCurrent + webpageURL
{
  echo "=== NSUserActivity construction and lifecycle ==="
  grep -RInE 'NSUserActivity\(|becomeCurrent\(\)|\.webpageURL|isEligibleForHandoff|isEligibleForSearch|isEligibleForPrediction|isEligibleForPublicIndexing|persistentIdentifier' \
    --include='*.swift' --include='*.m' --include='*.mm' \
    "$PROJECT_CWD" 2>/dev/null \
    | grep -v '/.build/' | grep -v '/Pods/' | grep -v 'DerivedData' || echo "(no matches)"
} >> "$AUDIT_DIR/tooling-raw/continue-useractivity.txt" 2>&1
```

### 4. Grep for URL-scheme handlers

```bash
{
  echo "=== open(_:) / openURL / scene(_:openURLContexts:) / .onOpenURL sites ==="
  grep -RInE 'application\(_:open:|scene\(_:openURLContexts:|\.onOpenURL\(|UIApplication\.shared\.open\(|UIApplication\.shared\.canOpenURL\(' \
    --include='*.swift' --include='*.m' --include='*.mm' \
    "$PROJECT_CWD" 2>/dev/null \
    | grep -v '/.build/' | grep -v '/Pods/' | grep -v 'DerivedData' || echo "(no matches)"
} > "$AUDIT_DIR/tooling-raw/url-scheme-handlers.txt" 2>&1
```

### 5. Grep for Spotlight / Core Spotlight

```bash
{
  echo "=== CSSearchableIndex / CSSearchableItem references ==="
  grep -RInE 'CSSearchableIndex|CSSearchableItem|CSSearchableItemAttributeSet|indexSearchableItems|deleteSearchableItems|domainIdentifier|kCSSearchableItemActivityIdentifier' \
    --include='*.swift' --include='*.m' --include='*.mm' \
    "$PROJECT_CWD" 2>/dev/null \
    | grep -v '/.build/' | grep -v '/Pods/' | grep -v 'DerivedData' || echo "(no matches)"
} > "$AUDIT_DIR/tooling-raw/spotlight-refs.txt" 2>&1
```

### 6. Grep for App Intents handoff / indexing

```bash
{
  echo "=== AppIntent / AppShortcut / IndexedEntity / donate references ==="
  grep -RInE 'AppIntent\b|AppShortcut\b|AppShortcutsProvider|IndexedEntity|EntityQuery|\.donate\(|IntentDonationManager' \
    --include='*.swift' "$PROJECT_CWD" 2>/dev/null \
    | grep -v '/.build/' | grep -v '/Pods/' | grep -v 'DerivedData' || echo "(no matches)"
} > "$AUDIT_DIR/tooling-raw/app-intents-refs.txt" 2>&1
```

### 7. Grep for AASA file references in code / CI / docs

`apple-app-site-association` is most often served by web infrastructure outside the Apple project root, but references to it (in docs, CI scripts that fetch it for verification, server-side route handlers) are common and useful to surface for the reviewers.

```bash
{
  echo "=== apple-app-site-association references ==="
  grep -RInE 'apple-app-site-association|\.well-known/apple-app-site-association|applinks:|webcredentials:|activitycontinuation:|appclips:' \
    "$PROJECT_CWD" 2>/dev/null \
    | grep -v '/.build/' | grep -v '/Pods/' | grep -v 'DerivedData' || echo "(no matches)"
} > "$AUDIT_DIR/tooling-raw/aasa-references.txt" 2>&1
```

### 8. Detect target platforms

Record which Apple platforms the project targets so reviewers can scope correctly (App Clips are iOS-only; macOS deep-link routing goes through different APIs).

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

### 9. Phase 1 emergency-exit check

**Deep-links has no emergency-exit triggers.** Always proceed.

```bash
EMERGENCY=0
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "$EMERGENCY"
```

### 10. Survey

In conversational text (not a persisted file), note:

- Domains declared in Associated Domains entitlement, per service (`applinks:`, `webcredentials:`, `activitycontinuation:`, `appclips:`); any `?mode=developer` suffixes
- Custom URL schemes declared in `CFBundleURLTypes` per target; flag schemes that overlap with well-known apps (`facebook`, `whatsapp`, `slack`, etc.) or system schemes
- Whether `application(_:continue:)` / `.onContinueUserActivity` handlers exist at the right lifecycle layer (scene-level for SwiftUI lifecycle apps; AppDelegate for UIKit lifecycle)
- Spotlight indexing call sites and whether matching deindex paths exist
- App Intents adoption shape (App Shortcuts? IndexedEntity? donation sites?)
- AASA references in the repo — CI scripts that curl the AASA, server-side route handlers serving it, docs describing the format

**If none of the deep-link surfaces are touched at all** (no entitlement, no `CFBundleURLTypes`, no `application(_:continue:)`, no Spotlight): notify, write that to STATUS.md, but still proceed to Phase 2 — reviewers may surface a "you have no deep-link surface and should consider one" recommendation.

This is for the user's situational awareness, not a persisted artifact.

## Outputs

- `$AUDIT_DIR/tooling-raw/associated-domains.txt`
- `$AUDIT_DIR/tooling-raw/url-types.txt`
- `$AUDIT_DIR/tooling-raw/queries-schemes.txt`
- `$AUDIT_DIR/tooling-raw/user-activity-types.txt`
- `$AUDIT_DIR/tooling-raw/continue-useractivity.txt`
- `$AUDIT_DIR/tooling-raw/url-scheme-handlers.txt`
- `$AUDIT_DIR/tooling-raw/spotlight-refs.txt`
- `$AUDIT_DIR/tooling-raw/app-intents-refs.txt`
- `$AUDIT_DIR/tooling-raw/aasa-references.txt`
- `$AUDIT_DIR/tooling-raw/STATUS.md` documents anything skipped
- Walker state has `target_platforms` set (comma-separated list of detected Apple platforms, or `unknown`)
- Walker state has `emergency_exit` set

## Outgoing edges

- **`proceed`** → `independent_reviews`. Normal path.
- **`emergency`** → `emergency_exit`. Never taken (no triggers).

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- No `.entitlements`, `Info.plist`, or Swift / Obj-C source in scope → write that to STATUS.md and still transition; reviewers will produce a one-row "no deep-link surface" finding.
- `plutil` missing (extraordinarily unusual on macOS) → fall back to raw `cat` of the plist; capture STATUS.md note.
- `grep` finds zero references across every artifact → STATUS.md notes "no deep-link surface detected"; reviewers handle.
