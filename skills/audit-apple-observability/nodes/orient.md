# Node: orient

Phase 1 of the framework — collect the observability call-site snapshot the reviewers need. **Observability has Phase 1 tooling (grep-based call-site capture) but no emergency-exit conditions** — the `orient → emergency_exit` edge is structurally present but never taken.

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

### 1. Detect project shape

```bash
HAS_SWIFT=$(find "$PROJECT_CWD" \( -name '*.swift' -o -name '*.m' -o -name '*.mm' \) -not -path '*/.build/*' -not -path '*/Pods/*' -not -path '*/DerivedData/*' 2>/dev/null | head -1 | wc -l | tr -d ' ')
scripts/walk.sh set --state "$STATE" --key has_source --value "$HAS_SWIFT"

# Target-platform detection — which Apple platforms this project targets.
PLATFORMS=""
for kind in IPHONEOS MACOSX WATCHOS TVOS XROS; do
  if grep -rqE "^[[:space:]]*${kind}_DEPLOYMENT_TARGET" "$PROJECT_CWD" \
       --include='*.pbxproj' --include='*.xcconfig' 2>/dev/null; then
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

If no Swift / Obj-C source is present, bail — there's nothing for this audit to review.

### 2. Capture Logger / os_log call sites

`Logger(subsystem:category:)` (iOS 14+) is the modern API; `os_log` is the deprecated C function. Both go through Apple's unified logging system and are subject to the same privacy-specifier rules. Capturing call sites with surrounding context is the single highest-yield Phase 1 activity for this audit.

```bash
GREP_EXCLUDES=(--exclude-dir=.build --exclude-dir=Pods --exclude-dir=DerivedData --exclude-dir=.git --exclude-dir=Carthage)

{
  echo "## Logger( call sites"
  grep -rn "${GREP_EXCLUDES[@]}" -E 'Logger\s*\(' "$PROJECT_CWD" 2>/dev/null || true
  echo
  echo "## os_log call sites"
  grep -rn "${GREP_EXCLUDES[@]}" -E '\bos_log[a-zA-Z_]*\s*\(' "$PROJECT_CWD" 2>/dev/null || true
  echo
  echo "## OSLog instances"
  grep -rn "${GREP_EXCLUDES[@]}" -E '\bOSLog\s*\(' "$PROJECT_CWD" 2>/dev/null || true
} > "$AUDIT_DIR/tooling-raw/logger-call-sites.txt" 2>&1
```

### 3. Capture privacy specifiers

The `privacy:` argument inside a `Logger` interpolation is what makes (or breaks) PII safety. Capturing every occurrence lets reviewers grep for `.public` on suspicious values.

```bash
{
  echo "## privacy: argument occurrences"
  grep -rn "${GREP_EXCLUDES[@]}" -E 'privacy:\s*\.(public|private|sensitive|auto)' "$PROJECT_CWD" 2>/dev/null || true
  echo
  echo "## C-style format-string privacy markers (%{public} / %{private})"
  grep -rn "${GREP_EXCLUDES[@]}" -E '%\{(public|private|sensitive)\}' "$PROJECT_CWD" 2>/dev/null || true
} > "$AUDIT_DIR/tooling-raw/privacy-specifiers.txt" 2>&1
```

### 4. Capture OSSignposter / os_signpost call sites

`OSSignposter` (iOS 15+ / macOS 12+) is the modern API; `os_signpost` is the deprecated C function. Capturing these tells reviewers what's instrumented and what's not.

```bash
{
  echo "## OSSignposter instances"
  grep -rn "${GREP_EXCLUDES[@]}" -E '\bOSSignposter\s*\(' "$PROJECT_CWD" 2>/dev/null || true
  echo
  echo "## Signpost intervals and events"
  grep -rn "${GREP_EXCLUDES[@]}" -E '\b(withIntervalSignpost|beginInterval|endInterval|emitEvent)\b' "$PROJECT_CWD" 2>/dev/null || true
  echo
  echo "## os_signpost call sites"
  grep -rn "${GREP_EXCLUDES[@]}" -E '\bos_signpost\s*\(' "$PROJECT_CWD" 2>/dev/null || true
} > "$AUDIT_DIR/tooling-raw/signpost-call-sites.txt" 2>&1
```

### 5. Capture MetricKit call sites

```bash
{
  echo "## MXMetricManager subscriber registration"
  grep -rn "${GREP_EXCLUDES[@]}" -E 'MXMetricManager\.shared\.add' "$PROJECT_CWD" 2>/dev/null || true
  echo
  echo "## MXMetricManagerSubscriber conformances"
  grep -rn "${GREP_EXCLUDES[@]}" -E 'MXMetricManagerSubscriber' "$PROJECT_CWD" 2>/dev/null || true
  echo
  echo "## MetricKit didReceive callbacks"
  grep -rn "${GREP_EXCLUDES[@]}" -E 'didReceive.*\b(MXMetricPayload|MXDiagnosticPayload)\b' "$PROJECT_CWD" 2>/dev/null || true
  echo
  echo "## Crash / hang / CPU / disk-write diagnostic types"
  grep -rn "${GREP_EXCLUDES[@]}" -E '\b(MXCrashDiagnostic|MXHangDiagnostic|MXCPUExceptionDiagnostic|MXDiskWriteExceptionDiagnostic)\b' "$PROJECT_CWD" 2>/dev/null || true
} > "$AUDIT_DIR/tooling-raw/metrickit-call-sites.txt" 2>&1
```

### 6. Capture print / NSLog / debugPrint / dump usage

These are the forbidden-in-Release loggers. `print()` / `NSLog()` / `debugPrint()` / `dump()` bypass the unified logging system entirely — no privacy specifier, no subsystem, no `<private>` masking. Every call site needs to be either removed or guarded behind `#if DEBUG`.

```bash
{
  echo "## print() call sites (excluding obvious comments / strings)"
  grep -rn "${GREP_EXCLUDES[@]}" --include='*.swift' -E '^\s*print\s*\(' "$PROJECT_CWD" 2>/dev/null || true
  echo
  echo "## NSLog() call sites"
  grep -rn "${GREP_EXCLUDES[@]}" -E '\bNSLog\s*\(' "$PROJECT_CWD" 2>/dev/null || true
  echo
  echo "## debugPrint() call sites"
  grep -rn "${GREP_EXCLUDES[@]}" --include='*.swift' -E '\bdebugPrint\s*\(' "$PROJECT_CWD" 2>/dev/null || true
  echo
  echo "## dump() call sites"
  grep -rn "${GREP_EXCLUDES[@]}" --include='*.swift' -E '\bdump\s*\(' "$PROJECT_CWD" 2>/dev/null || true
  echo
  echo "## #if DEBUG guard context (lines before/after print)"
  grep -rn "${GREP_EXCLUDES[@]}" --include='*.swift' -B2 -A2 -E '^\s*print\s*\(' "$PROJECT_CWD" 2>/dev/null | head -500 || true
} > "$AUDIT_DIR/tooling-raw/print-nslog-call-sites.txt" 2>&1
```

### 7. Capture Info.plist OSLogPreferences definitions

Apps can ship default log-level configuration per subsystem via Info.plist `OSLogPreferences`. Reviewers need to know whether any subsystem is force-enabled at `.debug` for Release.

```bash
{
  find "$PROJECT_CWD" -name "Info.plist" -not -path '*/.build/*' -not -path '*/Pods/*' \
    -exec sh -c 'echo "=== $1 ==="; plutil -p "$1" 2>/dev/null | grep -A40 -E "OSLogPreferences|OSLog" || true; echo' _ {} \;
} > "$AUDIT_DIR/tooling-raw/oslog-preferences.txt" 2>&1
```

### 8. Phase 1 emergency-exit check

**Observability has no emergency-exit triggers.** Always proceed.

```bash
EMERGENCY=0
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "$EMERGENCY"
```

### 9. Survey

In conversational text (not a persisted file), note:

- Total `Logger(` vs `os_log` vs `print(` / `NSLog(` call-site counts — the ratio tells reviewers whether the app is on the modern unified-logging stack or still on legacy
- Subsystem strings observed in `Logger(subsystem:category:)` — are they reverse-DNS (`com.org.app.networking`) or ad-hoc (`"network"`)?
- Whether any `Logger(` calls use `\(_, privacy: .public)` or `%{public}` — eyeball the captured file for anything that looks like a token / URL / email / userID
- Whether `MXMetricManager.shared.add(self)` appears at all — if no subscriber is registered, every Apple-Diagnostics-API crash is invisible
- Whether `OSSignposter` is used or only `os_signpost` — modern code on iOS 15+ should use the former
- Whether `print()` / `NSLog()` calls are guarded by `#if DEBUG` — unguarded calls in shipping code are Critical
- Detected platforms via `Package.swift` `platforms` or Info.plist — affects valid `Platform` values for findings

**If no Swift/Obj-C source found**: notify and stop.

This is for the user's situational awareness, not a persisted artifact.

## Outputs

- `$AUDIT_DIR/tooling-raw/` populated with the six call-site captures
- `$AUDIT_DIR/tooling-raw/STATUS.md` documents skipped tools (if any)
- Walker state has `has_source`, `emergency_exit` set

## Outgoing edges

- **`proceed`** → `independent_reviews`. Normal path.
- **`emergency`** → `emergency_exit`. Never taken (no triggers).

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- No Swift / Obj-C source in scope → bail with a pointer to a non-Apple project audit.
- `grep` returns no hits for `Logger` / `os_log` / `print` — captured as empty files; reviewers infer the project has no logging at all (an interesting finding in its own right).
- Project uses a third-party logging wrapper (CocoaLumberjack, SwiftyBeaver, etc.) — captured by the broader grep on `NSLog` / `print`; reviewers flag the wrapper in Phase 2.
