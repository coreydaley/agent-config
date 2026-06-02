# Node: orient

Phase 1 of the framework — run audit-specific tooling into `$AUDIT_DIR/tooling-raw/`, build a brief orientation note. **Apple performance has no emergency-exit gate** — performance is a runtime property; static review cannot trigger a halt.

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only)

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
TO=$(bash ~/.claude/lib/audit-runner.sh timeout-bin)
mkdir -p "$AUDIT_DIR/tooling-raw"
[ -z "$TO" ] && echo "⚠️ no timeout command available; install via 'brew install coreutils' for tool timeouts" \
  >> "$AUDIT_DIR/tooling-raw/STATUS.md"
```

## Steps

### 1. Run Phase 1 tooling

Apple performance tooling is fundamentally runtime — Instruments owns the high-fidelity signal. Static review surfaces likely-problem locations; this Phase 1 captures the pattern-grep candidates that Phase 2 reviewers will validate. **Never block on a missing tool.**

```bash
# Semgrep with Swift / performance rules (limited but useful).
if command -v semgrep >/dev/null; then
  ${TO:+$TO 600} semgrep --config=p/swift --config=p/performance \
    --json --output "$AUDIT_DIR/tooling-raw/semgrep.json" "$PROJECT_CWD" \
    2>&1 | tee "$AUDIT_DIR/tooling-raw/semgrep.log" || true
else
  echo "⚠️ semgrep not installed — SAST skipped" \
    >> "$AUDIT_DIR/tooling-raw/STATUS.md"
fi

# Look for known performance anti-patterns via grep — Phase 2 candidates.
mkdir -p "$AUDIT_DIR/tooling-raw/grep-patterns"
{
  echo "=== Synchronous I/O patterns (Data(contentsOf:)) ==="
  grep -rn "Data(contentsOf:" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50
  echo
  echo "=== Thread.sleep / sleep() ==="
  grep -rn "Thread.sleep\|sleep(" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50
  echo
  echo "=== Strong-self closure captures (potential retain cycle) ==="
  grep -rn "\[self\]\|\[strong self\]" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50
  echo
  echo "=== Force-unwrap on UIImage / Data (decode/load hot paths) ==="
  grep -rn 'UIImage(.*)!\|Data(.*)!' --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50
  echo
  echo "=== application(_:didFinishLaunchingWithOptions:) / App.init bodies ==="
  grep -rn "didFinishLaunchingWithOptions\|App\b.*init\b" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50
  echo
  echo "=== TimelineProvider / getTimeline (widget memory budget) ==="
  grep -rn "TimelineProvider\|getTimeline\|getSnapshot" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50
} > "$AUDIT_DIR/tooling-raw/grep-patterns/perf-patterns.txt"

# Detect any pre-captured Instruments traces in the project (the user may
# have stashed .trace bundles for this audit to reference).
find "$PROJECT_CWD" -name "*.trace" -not -path '*/.*' -maxdepth 4 \
  > "$AUDIT_DIR/tooling-raw/instruments-traces.txt" 2>&1 || true
```

### 2. Emergency-exit check

None. Performance is a runtime property — no static signal warrants halting the audit before Phase 2.

### 3. Survey

In conversational text (not a persisted file), note:

- Resolved scope (`$PROJECT_CWD`) and any obvious sub-paths (`*.xcodeproj/`, `Package.swift`, `Podfile`)
- Detected frameworks via grep on `import` statements: `SwiftUI`, `Combine`, `Concurrency` (`async`/`await`), `CoreData` / `SwiftData`, `WidgetKit`, `ActivityKit`, `CoreLocation`, `CoreMotion`, `CoreBluetooth`, `Network`, `WebKit`
- Target platforms from `Package.swift`'s `platforms:` array or `Info.plist`
- Check for `@main` `App` struct (SwiftUI) or `AppDelegate` / `SceneDelegate` — note initialization patterns
- Existing `MXMetricManager` (MetricKit) integration, `os_signpost` / `OSLog` performance markers, custom performance test targets
- Widget extensions, App Intents, Live Activities — flag for memory-budget review
- Pre-captured Instruments `.trace` bundles, if any

This is for the user's situational awareness, not a persisted artifact.

### 4. Detect target platforms

Record which Apple platforms the project targets so Phase 2 reviewers can scope findings appropriately (e.g. ~24MB watchOS active-app cap only applies if there's a watchOS target).

```bash
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

### 5. Persist any run-scoped state Phase 2 needs

```bash
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "0"
```

## Outputs

- `$AUDIT_DIR/tooling-raw/` populated with whatever tools were available
- `$AUDIT_DIR/tooling-raw/STATUS.md` documents skipped tools
- `$AUDIT_DIR/tooling-raw/grep-patterns/perf-patterns.txt` candidate locations
- Walker state has `emergency_exit` flag set to `0`
- Walker state has `target_platforms` set (comma-separated list of detected Apple platforms, or `unknown`)

## Outgoing edges

- **`proceed`** → `independent_reviews`. Normal path. Performance audits always take this edge — no emergency conditions.

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- A tool times out → captured in its `.log` file; orient proceeds. Phase 2 reviewers see the partial output.
- All tooling fails / missing → `STATUS.md` documents the degradation; orient still proceeds. Phase 2 reviewers do more manual code reading.
