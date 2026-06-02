# Node: orient

Phase 1 of the framework — run audit-specific tooling into `$AUDIT_DIR/tooling-raw/`, scan for emergency-exit conditions, build a brief orientation note. **Apple security has Phase 1 tooling AND an emergency-exit gate** — not every audit does.

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

### 1. Run Phase 1 tooling

Apple security tooling is thinner than the web ecosystem. Run what's available, document what's missing in `STATUS.md`. **Never block on a missing tool.**

```bash
# Secrets — gitleaks. Required emergency-exit trigger source.
if command -v gitleaks >/dev/null; then
  ${TO:+$TO 300} gitleaks detect --source "$PROJECT_CWD" \
    --report-format json \
    --report-path "$AUDIT_DIR/tooling-raw/gitleaks.json" \
    --no-banner 2>&1 | tee "$AUDIT_DIR/tooling-raw/gitleaks.log" || true
else
  echo "⚠️ gitleaks not installed — secret scanning skipped" \
    >> "$AUDIT_DIR/tooling-raw/STATUS.md"
fi

# Semgrep with Swift rules (limited but useful).
if command -v semgrep >/dev/null; then
  ${TO:+$TO 600} semgrep --config=p/security-audit --config=p/swift \
    --json --output "$AUDIT_DIR/tooling-raw/semgrep.json" "$PROJECT_CWD" \
    2>&1 | tee "$AUDIT_DIR/tooling-raw/semgrep.log" || true
else
  echo "⚠️ semgrep not installed — SAST skipped" \
    >> "$AUDIT_DIR/tooling-raw/STATUS.md"
fi

# Xcode static analyzer (heavy — requires build). Skip with SKIP_XCODEBUILD=1.
if [ -z "${SKIP_XCODEBUILD:-}" ] && command -v xcodebuild >/dev/null; then
  PROJ=$(ls "$PROJECT_CWD"/*.xcodeproj 2>/dev/null | head -1)
  if [ -n "$PROJ" ]; then
    SCHEME=$(xcodebuild -project "$PROJ" -list 2>/dev/null \
      | awk '/Schemes:/{flag=1;next}/^$/{flag=0}flag{print $1; exit}')
    if [ -n "$SCHEME" ]; then
      ${TO:+$TO 1800} xcodebuild analyze -project "$PROJ" -scheme "$SCHEME" \
        CODE_SIGNING_ALLOWED=NO -quiet \
        > "$AUDIT_DIR/tooling-raw/xcodebuild-analyze.log" 2>&1 || true
    else
      echo "⚠️ xcodebuild: no scheme found for $PROJ; static analyzer skipped" \
        >> "$AUDIT_DIR/tooling-raw/STATUS.md"
    fi
  fi
fi

# Source-level Apple artifact snapshot — declared entitlements.
find "$PROJECT_CWD" -name "*.entitlements" -not -path '*/.*' \
  -exec sh -c 'echo "=== $1 ==="; cat "$1"' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/entitlements-declared.txt" 2>&1 || true

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

### 2. Emergency-exit check

Apple security has the same emergency-exit condition as web security: a live credential in source code. Inspect `gitleaks.json` for hits whose `RuleID` matches a recognized prefix (`ghp_`, `sk_live_`, `AKIA`, private-key blocks, App Store Connect API key `.p8`, push notification certificates `.p12`).

```bash
EMERGENCY=0
if [ -s "$AUDIT_DIR/tooling-raw/gitleaks.json" ]; then
  if command -v jq >/dev/null && jq -e '. | length > 0' \
       "$AUDIT_DIR/tooling-raw/gitleaks.json" >/dev/null 2>&1; then
    # Filter to high-confidence hits; gitleaks's own rules are the source.
    HITS=$(jq -r '.[] | select(.RuleID | test("private-key|apple|app-store|push-cert|github-pat|stripe|aws-access")) | .RuleID' \
           "$AUDIT_DIR/tooling-raw/gitleaks.json" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$HITS" -gt 0 ]; then EMERGENCY=1; fi
  fi
fi
```

If `EMERGENCY=1`, take the `emergency_exit` outgoing edge. Manually re-confirm before exiting — gitleaks has known false positives on vendored C source, test fixtures, and example credentials in docs.

### 3. Survey

In conversational text (not a persisted file), note:

- Resolved scope (`$PROJECT_CWD`) and any obvious sub-paths (`*.xcodeproj/`, `Package.swift`, `Podfile`)
- Detected Swift frameworks via grep on `import` statements: `Security`, `CryptoKit`, `LocalAuthentication`, `StoreKit`, `CloudKit`, `WebKit`, `NetworkExtension`, `XPC`
- Target platforms from `Package.swift`'s `platforms:` array or `Info.plist`
- Which Phase 1 tools ran successfully vs. which are missing
- Apple-specific trust boundary checklist (URL scheme handlers, WKWebView, XPC services, App Groups, pasteboard, document picker, App Intents, share extensions, widgets, custom keyboards)

This is for the user's situational awareness, not a persisted artifact.

### 4. Persist any run-scoped state Phase 2 needs

```bash
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "$EMERGENCY"
```

## Outputs

- `$AUDIT_DIR/tooling-raw/` populated with whatever tools were available
- `$AUDIT_DIR/tooling-raw/STATUS.md` documents skipped tools
- `$AUDIT_DIR/tooling-raw/entitlements-declared.txt` exists (may be empty)
- Walker state has `emergency_exit` flag set

## Outgoing edges

- **`proceed`** → `independent_reviews`. Normal path. Phase 1 ran, no emergency triggered.
- **`emergency`** → `emergency_exit`. `gitleaks` matched a high-confidence live-credential rule; **the audit halts before Phase 2.**

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
- gitleaks reports a hit that turns out to be a false positive (vendored C source, doc example) → human judgment call before taking the `emergency` edge; if uncertain, take `proceed` and let the reviewers re-flag it as a finding rather than halting the audit.
