# Node: orient

Phase 1 of the framework — run audit-specific tooling into `$AUDIT_DIR/tooling-raw/` and build a brief orientation note. **Apple localization has Phase 1 tooling (filesystem snapshots + grep candidates) but no emergency-exit gate** — localization issues are never live-credential urgent.

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

Localized UI surface varies per platform (menu titles on macOS, complication strings on watchOS, ornaments on visionOS). Record detected platforms so reviewers can scope expectations.

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

Localization tooling is mostly filesystem inspection and grep — there's no equivalent of `gitleaks`/`semgrep` for l10n. Snapshot what exists; let Phase 2 reviewers read those snapshots.

```bash
mkdir -p "$AUDIT_DIR/tooling-raw"

# Snapshot String Catalogs (Xcode 15+).
find "$PROJECT_CWD" -name "*.xcstrings" -not -path '*/.*' \
  -exec sh -c 'echo "=== $1 ==="; head -100 "$1"' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/string-catalogs.txt" 2>&1 || true

# Snapshot legacy .strings files.
find "$PROJECT_CWD" -name "*.strings" -not -path '*/.*' \
  -not -path '*/Pods/*' \
  -exec sh -c 'echo "=== $1 ==="; head -50 "$1"' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/legacy-strings.txt" 2>&1 || true

# Snapshot .stringsdict (legacy pluralization).
find "$PROJECT_CWD" -name "*.stringsdict" -not -path '*/.*' \
  -exec sh -c 'echo "=== $1 ==="; cat "$1"' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/stringsdict.txt" 2>&1 || true

# Detect declared supported languages via CFBundleLocalizations.
find "$PROJECT_CWD" -name "Info.plist" -not -path '*/.*' -not -path '*/Pods/*' \
  -exec sh -c '/usr/libexec/PlistBuddy -c "Print :CFBundleLocalizations" "$1" 2>/dev/null \
    && echo "[from $1]"' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/supported-languages.txt" 2>&1 || true

# List .lproj directories — surfaces per-locale asset directories.
find "$PROJECT_CWD" -type d -name "*.lproj" -not -path '*/.*' \
  > "$AUDIT_DIR/tooling-raw/lproj-dirs.txt" 2>&1 || true

# Grep for hardcoded-looking strings near UI code (candidate signal).
{
  echo "=== Candidate hardcoded strings in Text(\"...\") ===";
  grep -rn 'Text("[A-Z]' --include="*.swift" "$PROJECT_CWD" 2>/dev/null \
    | grep -v "LocalizedStringKey\|String(localized:" | head -100;
  echo;
  echo "=== Alert/Button hardcoded titles ===";
  grep -rn 'Alert(title.*Text("\|Button("' --include="*.swift" "$PROJECT_CWD" 2>/dev/null \
    | grep -v "LocalizedStringKey" | head -50;
} > "$AUDIT_DIR/tooling-raw/grep-candidates.txt" 2>&1 || true
```

Document any missing prerequisites (e.g. `PlistBuddy` not available — unlikely on macOS) in `STATUS.md`.

### 2. Emergency-exit check

**None.** Apple localization has no emergency conditions. Always proceed to Phase 2.

```bash
EMERGENCY=0
```

### 3. Survey

In conversational text (not a persisted file), note:

- Resolved scope (`$PROJECT_CWD`) and any obvious sub-paths (`*.xcodeproj/`, `Package.swift`)
- Declared supported languages from `tooling-raw/supported-languages.txt` — this drives severity calibration
- Whether the project uses String Catalogs (`*.xcstrings`), legacy `.strings`/`.stringsdict`, or mixed
- Whether any RTL languages (Arabic / Hebrew / Persian) are declared targets — RTL findings escalate if so
- Formatter style in use: modern `FormatStyle` (iOS 15+) vs legacy `DateFormatter`/`NumberFormatter`
- At least 5 representative SwiftUI views read to assess hardcoded-string patterns
- **If no Swift/Apple source found**: notify and stop (this is a degenerate scope — let the user re-target)

This is for the user's situational awareness, not a persisted artifact.

### 4. Persist any run-scoped state Phase 2 needs

```bash
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "$EMERGENCY"
```

## Outputs

- `$AUDIT_DIR/tooling-raw/` populated with localization snapshots
- `$AUDIT_DIR/tooling-raw/STATUS.md` documents any skipped tooling
- `$AUDIT_DIR/tooling-raw/supported-languages.txt` exists (may be empty if no Info.plist)
- Walker state has `emergency_exit=0`

## Outgoing edges

- **`proceed`** → `independent_reviews`. Normal path (always taken for this audit).
- **`emergency`** → `emergency_exit`. **Never taken** — localization has no emergency triggers, but the edge exists for graph uniformity.

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- A find/grep command hits a permissions error → captured as a non-fatal `|| true`; orient proceeds.
- No Swift source / no localization assets anywhere → flag in survey, ask the user whether to continue (this is usually a wrong-scope mistake).
