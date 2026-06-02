# Node: orient

Phase 1 of the framework — run audit-specific tooling into `$AUDIT_DIR/tooling-raw/`, build a brief orientation note. Apple testing has **Phase 1 tooling but no emergency-exit gate** — the `emergency` edge is never taken.

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only)
- Optionally, a prior `audit-test-coverage` run's `tooling-raw/` (reused if present)

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
ORG_REPO=$(jq -r '.org + "/" + .repo' "$AUDIT_DIR/MANIFEST.json" 2>/dev/null || true)
TO=$(bash ~/.claude/lib/audit-runner.sh timeout-bin)
[ -z "$TO" ] && echo "⚠️ no timeout command available; install via 'brew install coreutils' for tool timeouts" \
  >> "$AUDIT_DIR/tooling-raw/STATUS.md"
```

## Steps

### 0. Detect target Apple platforms

Test-design expectations differ across Apple platforms — XCUITest critical-flow lists, snapshot test orientation matrices, and UI test affordances are platform-shaped. Record detected platforms so reviewers can scope expectations.

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

Apple testing tooling is thin — most signal comes from inventorying the test surface and reading test files. Reuse coverage data from a prior `audit-test-coverage` run if available, otherwise run `swift test --enable-code-coverage` directly. **Never block on a missing tool.**

```bash
# Reuse audit-test-coverage data if a recent run exists for this org/repo.
# Use find rather than a bare glob to survive zsh's default `nomatch` setting.
if [ -n "$ORG_REPO" ]; then
  LATEST_COV=$(find "$HOME/Reports/$ORG_REPO/audits" -maxdepth 1 -type d \
    -name '*-test-coverage' 2>/dev/null | sort -r | head -1)
else
  LATEST_COV=""
fi
if [ -n "$LATEST_COV" ] && [ -d "$LATEST_COV/tooling-raw" ]; then
  echo "Reusing coverage data from $LATEST_COV" \
    > "$AUDIT_DIR/tooling-raw/COVERAGE-SOURCE.md"
  # Use `/.` so cp copies contents safely even if the source dir is empty.
  cp -R "$LATEST_COV/tooling-raw/." "$AUDIT_DIR/tooling-raw/" 2>/dev/null || true
else
  # Run Swift coverage directly if there's a Package.swift.
  if [ -f "$PROJECT_CWD/Package.swift" ] && command -v swift >/dev/null; then
    ${TO:+$TO 600} swift test --enable-code-coverage --package-path "$PROJECT_CWD" \
      > "$AUDIT_DIR/tooling-raw/swift-test.log" 2>&1 || true
  else
    echo "⚠️ no Package.swift or swift toolchain — skipping coverage run" \
      >> "$AUDIT_DIR/tooling-raw/STATUS.md"
  fi
fi

# Inventory test targets and frameworks in use.
{
  echo "=== Test target files ==="
  find "$PROJECT_CWD" -name "*Tests.swift" -not -path '*/.*' 2>/dev/null
  echo
  echo "=== UI test target files ==="
  find "$PROJECT_CWD" -name "*UITests.swift" -not -path '*/.*' 2>/dev/null
  echo
  echo "=== Swift Testing usage (@Test, #expect, import Testing) ==="
  grep -rln "@Test\|#expect\|import Testing" --include="*.swift" "$PROJECT_CWD" 2>/dev/null
  echo
  echo "=== XCTest usage (legacy) ==="
  grep -rln "XCTestCase\|XCTAssert" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50
  echo
  echo "=== XCUITest usage ==="
  grep -rln "XCUIApplication\|XCUIElement" --include="*.swift" "$PROJECT_CWD" 2>/dev/null
  echo
  echo "=== SwiftUI Preview count ==="
  grep -rln "#Preview\|PreviewProvider" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | wc -l
  echo
  echo "=== Snapshot testing libraries ==="
  grep -rln "SnapshotTesting\|assertSnapshot\|AccessibilitySnapshot" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -20
} > "$AUDIT_DIR/tooling-raw/test-inventory.txt"
```

Make sure `$AUDIT_DIR/tooling-raw/STATUS.md` exists even when nothing was skipped — the verify gate relies on the directory being populated:

```bash
[ -f "$AUDIT_DIR/tooling-raw/STATUS.md" ] || touch "$AUDIT_DIR/tooling-raw/STATUS.md"
```

### 2. Emergency-exit check

None. Apple testing has no live-credential trigger or equivalent halt condition. Always take the `proceed` edge.

### 3. Survey

In conversational text (not a persisted file), note:

- Resolved scope (`$PROJECT_CWD`) and obvious sub-paths (`*.xcodeproj/`, `Package.swift`, `Tests/`)
- Whether the project ships unit, UI, and/or snapshot tests
- Mix of XCTest vs Swift Testing (Swift Testing ships with Xcode 16+ and runs alongside XCTest; gated by **toolchain**, not deployment target)
- Whether `#Preview` blocks exist for SwiftUI Views
- The project's apparent SwiftUI view-testing strategy (ViewInspector? snapshot? preview-based? business-logic-in-VM only?)
- Whether CI configuration runs the UI test target (look at `.github/workflows/`, `fastlane/`, `Bitrise.yml`, etc.)
- Whether a prior `audit-test-coverage` run was reused
- **If no Swift/Apple source found**: notify and stop

### 4. Persist any run-scoped state Phase 2 needs

```bash
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "0"
```

## Outputs

- `$AUDIT_DIR/tooling-raw/test-inventory.txt` populated
- `$AUDIT_DIR/tooling-raw/STATUS.md` documents any skipped tools (may be empty)
- `$AUDIT_DIR/tooling-raw/COVERAGE-SOURCE.md` exists if data was reused from `audit-test-coverage`
- `$AUDIT_DIR/tooling-raw/swift-test.log` exists if `swift test` ran
- Walker state has `emergency_exit` flag set to `0`

## Outgoing edges

- **`proceed`** → `independent_reviews`. Always — testing audit has no emergency-exit conditions.
- **`emergency`** → `emergency_exit`. Never taken; retained on the graph for shape uniformity with other `/audit-*` skills.

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- `swift test` times out or fails to compile → captured in `swift-test.log`; orient proceeds. Phase 2 reviewers see the partial output.
- No coverage data and no `Package.swift` → `STATUS.md` documents the degradation; orient still proceeds. Reviewers fall back to inventory + code reading.
- Inventory grep finds zero Swift test files at all → flag for Phase 2 as a likely top finding; do not halt.
