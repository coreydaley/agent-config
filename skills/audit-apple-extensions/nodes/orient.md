# Node: orient

Phase 1 of the framework — collect the extension-target snapshot the reviewers need. **Apple extensions has Phase 1 tooling (pure file inspection — `.appex` discovery, `plutil` over NSExtension Info.plist subkeys, entitlements per target) but no emergency-exit conditions** — the `orient → emergency_exit` edge is structurally present but never taken.

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only)

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
```

## Steps

### 1. Locate `.appex` extension targets

Extensions are declared in the `.pbxproj` as `PBXNativeTarget` rows with `productType = "com.apple.product-type.app-extension"` (or one of its more-specific variants — `messages-extension`, `watchkit2-extension`, etc.). The `Info.plist` for each extension carries the `NSExtension` dictionary that tells the OS what kind of extension it is.

```bash
mkdir -p "$AUDIT_DIR/tooling-raw"

# Find every Info.plist that declares an NSExtension dictionary.
# This catches both file-on-disk Info.plists and the generated kind
# (Xcode 15+ INFOPLIST_KEY_* still ends up in a built Info.plist at
# archive time; source-time we only see the file-on-disk variant).
{
  while IFS= read -r plist; do
    if plutil -extract NSExtension xml1 -o - "$plist" >/dev/null 2>&1; then
      EXT_POINT=$(plutil -extract NSExtension.NSExtensionPointIdentifier raw -o - "$plist" 2>/dev/null || echo "unknown")
      PRINCIPAL=$(plutil -extract NSExtension.NSExtensionPrincipalClass raw -o - "$plist" 2>/dev/null || echo "")
      MAIN_STORYBOARD=$(plutil -extract NSExtension.NSExtensionMainStoryboard raw -o - "$plist" 2>/dev/null || echo "")
      echo "=== $plist ==="
      echo "NSExtensionPointIdentifier: $EXT_POINT"
      echo "NSExtensionPrincipalClass: $PRINCIPAL"
      echo "NSExtensionMainStoryboard: $MAIN_STORYBOARD"
      echo "--- NSExtensionAttributes ---"
      plutil -extract NSExtension.NSExtensionAttributes xml1 -o - "$plist" 2>/dev/null \
        | sed 's/^/  /'
      echo
    fi
  done < <(find "$PROJECT_CWD" -name "Info.plist" \
            -not -path '*/.build/*' \
            -not -path '*/DerivedData/*' \
            -not -path '*/Pods/*' \
            -not -path '*/build/*' 2>/dev/null)
} > "$AUDIT_DIR/tooling-raw/appex-targets.txt" 2>&1

# Also scan the .pbxproj directly for productType lines — this catches
# extension targets that use INFOPLIST_KEY_* generated Info.plists where
# the NSExtension dictionary isn't on disk yet.
find "$PROJECT_CWD" -name "project.pbxproj" -not -path '*/.build/*' 2>/dev/null \
  | while IFS= read -r pbx; do
      echo "=== $pbx (extension target rows) ==="
      grep -nE 'productType = "com\.apple\.product-type\.[^"]*-extension"' "$pbx" 2>/dev/null || true
      echo
    done >> "$AUDIT_DIR/tooling-raw/appex-targets.txt" 2>&1
```

### 2. Snapshot extension entitlements (and host-app entitlements for drift diff)

```bash
# Every .entitlements file — name preserved so reviewers can match it
# back to a target via the .pbxproj CODE_SIGN_ENTITLEMENTS setting.
find "$PROJECT_CWD" -name "*.entitlements" \
  -not -path '*/.build/*' -not -path '*/DerivedData/*' \
  -exec sh -c 'echo "=== $1 ==="; plutil -p "$1" 2>/dev/null || cat "$1"; echo' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/extension-entitlements.txt" 2>&1 || true

# The host app's entitlements are also captured here — drift between host
# and extension is one of the top-3 findings for this audit.
cp "$AUDIT_DIR/tooling-raw/extension-entitlements.txt" \
   "$AUDIT_DIR/tooling-raw/host-app-entitlements.txt"
```

### 3. Snapshot App Group identifiers in use

App Groups are the primary IPC channel between host app and extension. The same group ID must appear in BOTH entitlements files, AND the code on both sides must use `UserDefaults(suiteName:)` / `FileManager.containerURL(forSecurityApplicationGroupIdentifier:)` referencing it.

```bash
{
  echo "=== App Group identifiers declared in entitlements ==="
  grep -hE 'group\.[a-zA-Z0-9._-]+' "$AUDIT_DIR/tooling-raw/extension-entitlements.txt" 2>/dev/null \
    | grep -oE 'group\.[a-zA-Z0-9._-]+' | sort -u
  echo
  echo "=== App Group identifiers used in code (suiteName / containerURL) ==="
  grep -rEn 'suiteName:[[:space:]]*"group\.[^"]+"' "$PROJECT_CWD" \
    --include='*.swift' --include='*.m' --include='*.mm' \
    --exclude-dir=.build --exclude-dir=DerivedData --exclude-dir=Pods 2>/dev/null || true
  grep -rEn 'containerURL\(forSecurityApplicationGroupIdentifier:[[:space:]]*"group\.[^"]+"' "$PROJECT_CWD" \
    --include='*.swift' --include='*.m' --include='*.mm' \
    --exclude-dir=.build --exclude-dir=DerivedData --exclude-dir=Pods 2>/dev/null || true
} > "$AUDIT_DIR/tooling-raw/app-groups.txt" 2>&1
```

### 4. Snapshot Info.plist files (full, not just NSExtension)

```bash
find "$PROJECT_CWD" -name "Info.plist" \
  -not -path '*/.build/*' -not -path '*/Pods/*' -not -path '*/DerivedData/*' \
  -exec sh -c 'echo "=== $1 ==="; plutil -p "$1" 2>/dev/null || cat "$1"; echo' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/info-plists.txt" 2>&1 || true
```

### 5. Record OS-imposed memory budgets per extension type

This is reference material for the reviewers — the OS kills any extension that crosses these thresholds. The numbers shift across iOS / macOS / watchOS versions; the audit treats them as anchors, not statutes.

```bash
cat > "$AUDIT_DIR/tooling-raw/extension-budgets.txt" <<'EOF'
# Apple extension memory budgets (reviewer reference)
#
# These are the OS-imposed runtime memory caps. Crossing them gets the
# extension killed (jetsam on iOS) or — in NSE's case — silently reverts
# the push to its unmodified server-sent form. Numbers are the public
# anchors; they shift across OS releases. Treat as upper bounds; design
# for headroom.
#
# NSExtensionPointIdentifier                          | Cap   | Lifecycle / notes
# com.apple.usernotifications.service                 | 24MB  | NSE; 30s wallclock budget;
#                                                     |       | expiry handler MUST call
#                                                     |       | contentHandler with the
#                                                     |       | unmodified content.
# com.apple.usernotifications.content-extension       | 24MB  | UI-only; brief.
# com.apple.widgetkit-extension                       | ~30MB | TimelineProvider /
#                                                     |       | AppIntentTimelineProvider;
#                                                     |       | getTimeline() must return
#                                                     |       | quickly (5-15s practical).
# com.apple.intents-service / app-intents             | ~120MB | App Intents perform() in
#                                                     |       | Shortcuts/Siri context;
#                                                     |       | crash → Spotlight reports
#                                                     |       | intent failure.
# com.apple.share-services                            | 120MB | Share extension UI.
# com.apple.ui-services (action)                      | 120MB | Action extension UI.
# com.apple.fileprovider-nonui                        | ~15MB | Tight; FileProvider
#                                                     |       | enumerator + working set.
# com.apple.authentication-services-credential-provider | ~60MB | AutoFill credential UI.
# com.apple.keyboard-service                          | ~50MB | Custom keyboard.
# com.apple.Safari.web-extension                      | per WKWebExtension model; no
#                                                     |       | hard MB cap, but content
#                                                     |       | scripts run inside Safari's
#                                                     |       | renderer process.
EOF
```

### 6. Detect target platforms

Record which Apple platforms the project targets so Phase 2 reviewers can skip categories that don't apply (e.g. don't flag Keyboard extension findings on macOS-only projects; don't flag Live Activity findings on projects without an iOS target).

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
```

### 7. Phase 1 emergency-exit check

**Apple extensions has no emergency-exit triggers.** Always proceed.

```bash
EMERGENCY=0
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "$EMERGENCY"

cat > "$AUDIT_DIR/tooling-raw/STATUS.md" <<EOF
# Phase 1 tooling status — apple-extensions

Phase 1 tooling: pure file inspection (find / plutil / grep). No
external tools required.

Captured:
- appex-targets.txt        — extension targets + NSExtension subkeys
- extension-entitlements.txt — every .entitlements in the project
- host-app-entitlements.txt  — duplicate for drift-diff convenience
- app-groups.txt           — group.* identifiers declared / used
- info-plists.txt          — every Info.plist (including non-extension)
- extension-budgets.txt    — OS-imposed memory budgets reference table

Detected target platforms: ${PLATFORMS:-unknown}
EOF
```

### 8. Survey

In conversational text (not a persisted file), note:

- Number and types of extension targets detected (e.g. "2 extensions: 1 Widget, 1 NSE")
- `NSExtensionPointIdentifier` value for each — this drives which category in Phase 2 the extension falls under
- Whether `NSExtensionPrincipalClass` or `NSExtensionMainStoryboard` is used (SwiftUI / WidgetKit-style vs storyboard-driven)
- Whether `NSExtensionAttributes` contains an `NSExtensionActivationRule` (Share / Action extensions) — note overly broad predicates here so reviewers can flag them
- App Group identifiers declared and whether host + extensions reference the same set
- Entitlement drift visible in the snapshot — capabilities present on the host but missing on an extension (Push, App Groups, iCloud, HealthKit)
- Extension `MinimumOSVersion` (from Info.plist) vs host app's deployment target — extension cannot run on an OS older than its `MinimumOSVersion`, and it cannot ship newer than the host's

**If no `.appex` extension targets found**: notify and stop. The audit's entire purpose is the extension surface; without one, there is nothing to review.

This is for the user's situational awareness, not a persisted artifact.

## Outputs

- `$AUDIT_DIR/tooling-raw/` populated with the 6 reference files above
- `$AUDIT_DIR/tooling-raw/STATUS.md` documents what ran
- Walker state has `target_platforms` set (comma-separated list of detected Apple platforms, or `unknown`)
- Walker state has `emergency_exit=0` set

## Outgoing edges

- **`proceed`** → `independent_reviews`. Normal path.
- **`emergency`** → `emergency_exit`. Never taken (no triggers).

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- No `.appex` extension targets in scope → bail with a pointer to the appropriate audit for whatever the project *does* have (likely `/audit-apple-design` or `/audit-apple-architecture`).
- `plutil` unavailable (extremely rare on macOS; impossible in CI containers without macOS) → fall back to raw `cat` of each Info.plist; reviewers parse the XML themselves; STATUS.md notes the degradation.
- Project uses XcodeGen / Tuist with `Info.plist` generated at build time and not committed — file-based discovery may miss extension targets; the `.pbxproj` productType scan in step 1 catches these.
