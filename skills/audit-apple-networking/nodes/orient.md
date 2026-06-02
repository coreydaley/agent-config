# Node: orient

Phase 1 of the framework — collect the URLSession / Network.framework usage snapshot the reviewers need. **Networking has Phase 1 tooling (grep sweep + Info.plist ATS extraction) but no emergency-exit conditions** — the `orient → emergency_exit` edge is structurally present but never taken.

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only)
- Optional env vars: `SKIP_GREP=1` skips the `rg`/`grep` sweep (useful for very large monorepos where the sweep would explode); reviewers fall back to source-only navigation

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
TO=$(bash ~/.claude/lib/audit-runner.sh timeout-bin)
[ -z "$TO" ] && echo "⚠️ no timeout command available; install via 'brew install coreutils' for tool timeouts" \
  >> "$AUDIT_DIR/tooling-raw/STATUS.md"

if command -v rg >/dev/null; then
  GREP="rg -n --no-heading -S"
else
  GREP="grep -RIn"
  echo "⚠️ ripgrep not installed; falling back to grep -RIn (slower)" \
    >> "$AUDIT_DIR/tooling-raw/STATUS.md"
fi
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

URLSession + Network.framework are cross-platform; `.background` URLSession lifecycle hooks fire on iOS / iPadOS / visionOS (depth in `audit-apple-ios`); NetworkExtension provider configuration is macOS-distinctive (depth in `audit-apple-macos`).

### 1. URLSessionConfiguration usage

The single highest-yield artifact for this audit is a complete list of every `URLSessionConfiguration` and `URLSession.shared` reference. Configuration choice (`.default` vs `.ephemeral` vs `.background(withIdentifier:)`) is where token-cache-poisoning and DDOS-self chains start.

```bash
if [ -z "${SKIP_GREP:-}" ]; then
  ${TO:+$TO 60} $GREP -e 'URLSessionConfiguration' \
    -e 'URLSessionConfiguration\.default' \
    -e 'URLSessionConfiguration\.ephemeral' \
    -e 'URLSessionConfiguration\.background' \
    -e 'httpAdditionalHeaders' \
    -e 'timeoutIntervalForRequest' \
    -e 'timeoutIntervalForResource' \
    "$PROJECT_CWD" > "$AUDIT_DIR/tooling-raw/urlsession-config.txt" 2>&1 || true

  ${TO:+$TO 60} $GREP -e 'URLSession\.shared' -e 'URLSession(configuration:' \
    "$PROJECT_CWD" > "$AUDIT_DIR/tooling-raw/urlsession-shared.txt" 2>&1 || true
fi
```

### 2. Authentication challenge / pinning hooks

`urlSession(_:didReceive:completionHandler:)` is the canonical hook for cert pinning. Capture every site where it's implemented to inspect the algorithm (cert hash vs SPKI hash), the multi-pin fallback strategy, and the disposition returned for unrecognized challenges.

```bash
if [ -z "${SKIP_GREP:-}" ]; then
  ${TO:+$TO 60} $GREP \
    -e 'URLAuthenticationChallenge' \
    -e 'urlSession.*didReceive.*completionHandler' \
    -e 'SecTrustEvaluate' \
    -e 'SecTrustEvaluateWithError' \
    -e 'SecCertificateCopyData' \
    -e 'SecKeyCopyExternalRepresentation' \
    -e 'kSecTrustResultProceed' \
    -e 'NWConnection' \
    -e 'sec_protocol_options_set_verify_block' \
    "$PROJECT_CWD" > "$AUDIT_DIR/tooling-raw/auth-challenge.txt" 2>&1 || true
fi
```

### 3. WebSocket usage

```bash
if [ -z "${SKIP_GREP:-}" ]; then
  ${TO:+$TO 60} $GREP \
    -e 'URLSessionWebSocketTask' \
    -e 'webSocketTask' \
    -e '\.send(\.string' \
    -e '\.send(\.data' \
    -e 'sendPing' \
    "$PROJECT_CWD" > "$AUDIT_DIR/tooling-raw/websocket.txt" 2>&1 || true
fi
```

### 4. NWPathMonitor reachability

```bash
if [ -z "${SKIP_GREP:-}" ]; then
  ${TO:+$TO 60} $GREP \
    -e 'NWPathMonitor' \
    -e 'pathUpdateHandler' \
    -e 'NWPath\.Status' \
    -e 'Reachability' \
    -e 'SCNetworkReachability' \
    "$PROJECT_CWD" > "$AUDIT_DIR/tooling-raw/pathmonitor.txt" 2>&1 || true
fi
```

### 5. Cache policy / URLCache discipline

`URLRequest.cachePolicy` defaults are surprising; `URLCache.shared` defaults are small. Both surfaces are the source of the "token cache poisoning" chain.

```bash
if [ -z "${SKIP_GREP:-}" ]; then
  ${TO:+$TO 60} $GREP \
    -e 'URLRequest.*cachePolicy' \
    -e 'cachePolicy' \
    -e 'URLCache' \
    -e 'URLCache\.shared' \
    -e 'NSURLRequestUseProtocolCachePolicy' \
    -e 'NSURLRequestReloadIgnoringLocalCacheData' \
    -e 'NSURLRequestReturnCacheDataElseLoad' \
    -e 'diskCapacity' \
    -e 'memoryCapacity' \
    "$PROJECT_CWD" > "$AUDIT_DIR/tooling-raw/cachepolicy.txt" 2>&1 || true
fi
```

### 6. NSAppTransportSecurity blocks from Info.plist

ATS exceptions are owned by `audit-apple-security` at the threat-model level, but the *presence* of an ATS dictionary affects networking findings (e.g. flagging `NSAllowsArbitraryLoads=true` here as a cross-ref breadcrumb pointing at the security audit).

```bash
{
  find "$PROJECT_CWD" -name "Info.plist" -not -path '*/.build/*' -not -path '*/Pods/*' -not -path '*/DerivedData/*' | while read -r plist; do
    echo "=== $plist ==="
    plutil -extract NSAppTransportSecurity xml1 -o - "$plist" 2>/dev/null || echo "(no NSAppTransportSecurity block)"
    echo
  done
} > "$AUDIT_DIR/tooling-raw/ats-info-plists.txt" 2>&1
```

### 7. Phase 1 emergency-exit check

**Networking has no emergency-exit triggers.** Always proceed.

```bash
EMERGENCY=0
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "$EMERGENCY"
```

### 8. Survey

In conversational text (not a persisted file), note:

- Apparent networking strategy: bespoke `URLSession`-per-feature, single shared service object, or third-party client (Alamofire, Moya, AsyncHTTPClient, Apollo, gRPC-Swift)
- Number of distinct `URLSessionConfiguration` call sites; how many default vs ephemeral vs background
- Presence and count of `urlSession(_:didReceive:completionHandler:)` implementations (zero ⇒ no pinning; many ⇒ duplicated pinning logic worth deduplicating)
- WebSocket usage (URLSessionWebSocketTask vs Starscream vs Socket.IO)
- `NWPathMonitor` adoption (or deprecated `Reachability`)
- Any `NSAllowsArbitraryLoads=true` or `NSExceptionDomains` entries — note for cross-ref to `audit-apple-security`
- Third-party SDKs that own their own URLSession (Firebase, Sentry, Amplitude) — these escape this audit's recommendations and are flagged for awareness

**If no Swift/Obj-C source found**: notify and stop.

This is for the user's situational awareness, not a persisted artifact.

## Outputs

- `$AUDIT_DIR/tooling-raw/` populated with grep snapshots and ATS extraction
- `$AUDIT_DIR/tooling-raw/STATUS.md` documents skipped tools
- Walker state has `emergency_exit` set

## Outgoing edges

- **`proceed`** → `independent_reviews`. Normal path.
- **`emergency`** → `emergency_exit`. Never taken (no triggers).

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- No Swift/Obj-C source in scope → bail with a pointer to a non-Apple project audit.
- `rg` / `grep` times out on a large monorepo → captured in the log file; orient still proceeds and reviewers use source-only navigation.
- No `URLSession` / `Network.framework` references at all → flagged as a finding category (`URLSessionConfig`) in Phase 2 ("project does network I/O via undocumented surface, or has no network I/O at all").
