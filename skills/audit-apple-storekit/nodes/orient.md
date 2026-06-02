# Node: orient

Phase 1 of the framework — collect the StoreKit-surface snapshot the reviewers need. **StoreKit has Phase 1 tooling (`.storekit` configuration files + StoreKit 2 vs StoreKit 1 API grep) but no emergency-exit conditions** — the `orient → emergency_exit` edge is structurally present but never taken.

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only)
- Optional env vars: `SKIP_GREP=1` skips the source-scan steps (rare; only useful when the source tree is gigantic and the reviewers will read source directly)

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
TO=$(bash ~/.claude/lib/audit-runner.sh timeout-bin)
[ -z "$TO" ] && echo "⚠️ no timeout command available; install via 'brew install coreutils' for tool timeouts" \
  >> "$AUDIT_DIR/tooling-raw/STATUS.md"
RG=$(command -v rg || command -v grep)
```

## Steps

### 1. Locate `.storekit` configuration files

The `.storekit` file is Xcode's local IAP configuration for sandbox-less testing. Its presence (and which schemes attach it) determines whether StoreKitTesting findings are even applicable.

```bash
find "$PROJECT_CWD" -name "*.storekit" -not -path '*/.build/*' -not -path '*/DerivedData/*' \
  -exec sh -c 'echo "=== $1 ==="; cat "$1"; echo' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/storekit-configs.txt" 2>&1 || true
```

If the file is empty, that's itself a Phase 2 finding (`StoreKitTesting`).

### 2. Snapshot StoreKit 2 API usage

The single highest-yield activity for this audit is grepping for the StoreKit 2 API surface and reading every call site. Capture them up front so the reviewers can read line-by-line.

```bash
if [ -z "${SKIP_GREP:-}" ] && [ -n "$RG" ]; then
  # StoreKit 2 — the modern surface
  ${TO:+$TO 30} "$RG" -n --no-heading -uu \
    -e 'Transaction\.currentEntitlements' \
    -e 'Transaction\.updates' \
    -e 'Transaction\.all' \
    -e 'Transaction\.unfinished' \
    -e 'Transaction\.latest' \
    -e 'Product\.products' \
    -e 'Product\.SubscriptionInfo' \
    -e 'Product\.SubscriptionOffer' \
    -e '\.purchase\(' \
    "$PROJECT_CWD" 2>/dev/null \
    > "$AUDIT_DIR/tooling-raw/storekit2-usage.txt" || true

  # VerificationResult — the .verified / .unverified discipline
  ${TO:+$TO 30} "$RG" -n --no-heading -uu \
    -e 'VerificationResult' \
    -e '\.unverified' \
    -e '\.verified' \
    -e '\.payloadValue' \
    -e 'jwsRepresentation' \
    "$PROJECT_CWD" 2>/dev/null \
    > "$AUDIT_DIR/tooling-raw/verificationresult-usage.txt" || true

  # Transaction.updates observer sites
  ${TO:+$TO 30} "$RG" -n --no-heading -uu -B 1 -A 6 \
    -e 'for await .* in Transaction\.updates' \
    -e 'Task.*Transaction\.updates' \
    "$PROJECT_CWD" 2>/dev/null \
    > "$AUDIT_DIR/tooling-raw/transaction-updates.txt" || true

  # AppStore.sync — restore-purchases path
  ${TO:+$TO 30} "$RG" -n --no-heading -uu \
    -e 'AppStore\.sync' \
    -e 'AppStore\.requestReview' \
    "$PROJECT_CWD" 2>/dev/null \
    > "$AUDIT_DIR/tooling-raw/appstore-sync-usage.txt" || true
else
  echo "⚠️ StoreKit 2 source scan skipped (SKIP_GREP set or no rg/grep)" \
    >> "$AUDIT_DIR/tooling-raw/STATUS.md"
fi
```

### 3. Snapshot StoreKit 1 (legacy) API usage

For projects targeting iOS 15+, any StoreKit 1 call site is at minimum a Low finding (migrate to StoreKit 2). For mixed projects, it's worth knowing the call sites.

```bash
if [ -z "${SKIP_GREP:-}" ] && [ -n "$RG" ]; then
  ${TO:+$TO 30} "$RG" -n --no-heading -uu \
    -e 'SKPaymentQueue' \
    -e 'SKPaymentTransactionObserver' \
    -e 'SKProduct\b' \
    -e 'SKProductsRequest' \
    -e 'SKReceiptRefreshRequest' \
    -e 'appStoreReceiptURL' \
    -e 'SKPaymentTransaction\b' \
    "$PROJECT_CWD" 2>/dev/null \
    > "$AUDIT_DIR/tooling-raw/storekit1-usage.txt" || true
fi
```

### 4. Locate likely paywall view files

```bash
if [ -z "${SKIP_GREP:-}" ] && [ -n "$RG" ]; then
  ${TO:+$TO 30} "$RG" -l --no-heading -uu \
    -e 'Paywall' \
    -e 'SubscriptionStoreView' \
    -e 'ProductView' \
    -e 'StoreView\b' \
    -e 'Restore.*Purchases' \
    -e 'subscriptionStatusTask' \
    "$PROJECT_CWD" 2>/dev/null \
    > "$AUDIT_DIR/tooling-raw/paywall-views.txt" || true
fi
```

### 5. Target-platform detection

```bash
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

### 6. Phase 1 emergency-exit check

**StoreKit has no emergency-exit triggers.** Always proceed.

```bash
EMERGENCY=0
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "$EMERGENCY"
```

### 7. Survey

In conversational text (not a persisted file), note:

- Whether any `.storekit` file is present, which schemes attach it (visible in `*.xcscheme` files if present), and whether it contains products at all
- StoreKit 2 vs StoreKit 1 footprint: how many call sites in each, whether StoreKit 1 is in a legacy module being phased out or co-exists with StoreKit 2
- Whether a `Transaction.updates` observer exists, where it's started (App lifecycle vs an arbitrary view's `.task`), whether the Task is ever cancelled
- Whether `Transaction.currentEntitlements` is consumed at app launch (bootstrap UI) or only after a `purchase()` call (cross-device restore miss)
- Whether `AppStore.sync()` is wired to a "Restore Purchases" button or only invoked from a Settings screen the user never finds
- Whether any server-side validation appears to exist — search for `jwsRepresentation` being sent over network (`URLSession`, etc.) or only being stored locally
- Paywall surface: is it the SwiftUI `SubscriptionStoreView` / `StoreView` / `ProductView` (Apple-provided, gets HIG correctness for free) or a hand-rolled paywall (audit it for Guideline 3.1.2 compliance)
- Test surface: any `SKTestSession` usage, any XCUITest hitting the paywall, any `.storekit` config attached to a test plan

**If no Swift/Obj-C source found**: notify and stop, no StoreKit to audit.
**If neither StoreKit 2 nor StoreKit 1 imports detected**: notify, suggest the user verify they meant to run a StoreKit audit (maybe the app doesn't ship IAP).

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

- No Swift/Obj-C source in scope → bail with a pointer to a non-Apple audit.
- No StoreKit imports at all (neither StoreKit 1 nor StoreKit 2) → log to STATUS.md but still proceed; the reviewers will flag this as "no IAP detected; audit is single-task no-findings".
- `rg`/`grep` times out (unusual on a sane source tree) → captured in the log; orient still proceeds and reviewers fall back to reading source directly.
