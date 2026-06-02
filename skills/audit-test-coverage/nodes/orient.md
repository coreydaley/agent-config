# Node: orient

Phase 1 of the framework — run language-appropriate coverage tooling into `$AUDIT_DIR/tooling-raw/` and build a brief orientation note. **Phase 1 tooling is the critical part of this audit** — it produces the measured coverage data that grounds both reviewers' findings. Test-coverage has **no emergency-exit condition**; the only outgoing edge taken in normal operation is `proceed`.

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only for inspection; tooling may write to its own caches like `.build/`, `target/`, `coverage/`)

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
TO=$(bash ~/.claude/lib/audit-runner.sh timeout-bin)
[ -z "$TO" ] && echo "⚠️ no timeout command available; install via 'brew install coreutils' for tool timeouts" \
  >> "$AUDIT_DIR/tooling-raw/STATUS.md"
```

## Steps

### 1. Run language-appropriate coverage tooling

Detect the stack and run coverage for every language present. Capture stdout+stderr; write raw output to `$AUDIT_DIR/tooling-raw/`. Always run with a timeout. **Never block on a missing tool** — write a note to `STATUS.md` and continue.

Run from the project root:

```bash
cd "$PROJECT_CWD"
```

#### Go

```bash
if [ -f go.mod ] && command -v go >/dev/null; then
  ${TO:+$TO 300} go test -coverprofile="$AUDIT_DIR/tooling-raw/cover.out" \
    -covermode=atomic ./... \
    > "$AUDIT_DIR/tooling-raw/go-test.log" 2>&1 || true
  if [ -f "$AUDIT_DIR/tooling-raw/cover.out" ]; then
    go tool cover -func="$AUDIT_DIR/tooling-raw/cover.out" \
      > "$AUDIT_DIR/tooling-raw/cover-func.txt" 2>&1 || true
  fi
elif [ -f go.mod ]; then
  echo "⚠️ go.mod present but go not installed — Go coverage skipped" \
    >> "$AUDIT_DIR/tooling-raw/STATUS.md"
fi
```

#### Python (pytest + coverage)

```bash
if { [ -f pyproject.toml ] || [ -f pytest.ini ] || [ -f setup.cfg ]; } \
     && command -v pytest >/dev/null; then
  ${TO:+$TO 300} pytest --cov --cov-report=term-missing --cov-report=json \
    > "$AUDIT_DIR/tooling-raw/pytest-cov.log" 2>&1 || true
  [ -f coverage.json ] && mv coverage.json "$AUDIT_DIR/tooling-raw/" || true
elif { [ -f pyproject.toml ] || [ -f pytest.ini ] || [ -f setup.cfg ]; }; then
  echo "⚠️ Python project detected but pytest not installed — Python coverage skipped" \
    >> "$AUDIT_DIR/tooling-raw/STATUS.md"
fi
```

#### Node / Jest

```bash
if [ -f package.json ] && grep -q '"jest"' package.json; then
  ${TO:+$TO 600} npx --yes jest --coverage \
    --coverageReporters=json-summary --coverageReporters=text \
    > "$AUDIT_DIR/tooling-raw/jest.log" 2>&1 || true
fi
```

#### Node / Vitest

```bash
if [ -f package.json ] && grep -q '"vitest"' package.json; then
  ${TO:+$TO 600} npx --yes vitest run --coverage \
    > "$AUDIT_DIR/tooling-raw/vitest.log" 2>&1 || true
fi
```

#### Rust

```bash
if [ -f Cargo.toml ]; then
  if command -v cargo-tarpaulin >/dev/null; then
    ${TO:+$TO 600} cargo tarpaulin --out Stdout \
      > "$AUDIT_DIR/tooling-raw/tarpaulin.log" 2>&1 || true
  elif command -v cargo-llvm-cov >/dev/null; then
    ${TO:+$TO 600} cargo llvm-cov --summary-only \
      > "$AUDIT_DIR/tooling-raw/cargo-llvm-cov.log" 2>&1 || true
  else
    echo "⚠️ Cargo.toml present but neither cargo-tarpaulin nor cargo-llvm-cov installed — Rust coverage skipped" \
      >> "$AUDIT_DIR/tooling-raw/STATUS.md"
  fi
fi
```

#### Swift — Swift Package Manager

```bash
if [ -f Package.swift ] && command -v swift >/dev/null; then
  ${TO:+$TO 600} swift test --enable-code-coverage \
    > "$AUDIT_DIR/tooling-raw/swift-test.log" 2>&1 || true
  PROFDATA=$(find .build -name '*.profdata' 2>/dev/null | head -1)
  TEST_BIN=$(find .build -path '*debug/*xctest' -type f 2>/dev/null | head -1)
  if [ -n "$PROFDATA" ] && [ -n "$TEST_BIN" ]; then
    xcrun llvm-cov report -instr-profile="$PROFDATA" "$TEST_BIN" \
      > "$AUDIT_DIR/tooling-raw/swift-cov-summary.txt" 2>&1 || true
    xcrun llvm-cov export -instr-profile="$PROFDATA" "$TEST_BIN" \
      -format=lcov > "$AUDIT_DIR/tooling-raw/swift-cov.lcov" 2>&1 || true
  fi
fi
```

#### Swift — Xcode project (heavier; requires a build)

```bash
PROJ=$(ls *.xcodeproj 2>/dev/null | head -1)
if [ -n "$PROJ" ] && [ -z "${SKIP_XCODEBUILD:-}" ] && command -v xcodebuild >/dev/null; then
  SCHEME=$(xcodebuild -project "$PROJ" -list 2>/dev/null \
    | awk '/Schemes:/{flag=1;next}/^$/{flag=0}flag{print $1; exit}')
  if [ -n "$SCHEME" ]; then
    ${TO:+$TO 1800} xcodebuild test -project "$PROJ" -scheme "$SCHEME" \
      -enableCodeCoverage YES -derivedDataPath "$AUDIT_DIR/tooling-raw/dd" \
      CODE_SIGNING_ALLOWED=NO -quiet \
      > "$AUDIT_DIR/tooling-raw/xcodebuild-test.log" 2>&1 || true
  else
    echo "⚠️ xcodebuild: no scheme found for $PROJ; Xcode coverage skipped" \
      >> "$AUDIT_DIR/tooling-raw/STATUS.md"
  fi
fi
```

If tooling fails, hangs, isn't installed, or there's no coverage config: ensure `$AUDIT_DIR/tooling-raw/STATUS.md` documents what was skipped or failed. Phase 2 reviewers MUST be told whether measured coverage is available — if `STATUS.md` indicates no usable coverage data, they fall back to source-reading and note the limitation prominently in their findings.

### 2. Survey

In conversational text (not a persisted file), note:

- Resolved scope (`$PROJECT_CWD`) and obvious sub-paths
- Detected primary language(s) and test framework(s):
  - **Go** — `go.mod`, `*_test.go`, `testing` package
  - **Python** — `pyproject.toml`, `pytest.ini`, `setup.cfg`, `tests/`, `test_*.py` / `*_test.py`
  - **Node/TS** — `package.json` test script, `jest.config.*`, `vitest.config.*`, `*.test.ts` / `*.spec.ts`
  - **Rust** — `Cargo.toml`, `#[cfg(test)]` blocks, `tests/`
  - **Swift** — `Package.swift` (SPM), `*.xcodeproj/` (Xcode), `Tests/`, `*Tests.swift`, XCTest or `import Testing` (Swift Testing)
  - **Ruby** — `Gemfile`, `spec/`, `rspec`
- Test layout: unit/integration/e2e locations (`tests/unit/`, `tests/integration/`, `e2e/`, `*_integration_test.go`, XCUITest targets)
- CI configuration — what does CI actually run today? (`.github/workflows/`, `.gitlab-ci.yml`, `circleci/`, etc.)
- Which Phase 1 tools ran successfully vs. which were skipped

This is for the user's situational awareness, not a persisted artifact.

### 3. Persist run-scoped state

```bash
# Test-coverage has no emergency-exit condition; always proceed.
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "0"
```

## Outputs

- `$AUDIT_DIR/tooling-raw/` populated with whatever coverage data could be produced (per-language log + coverage files)
- `$AUDIT_DIR/tooling-raw/STATUS.md` documents skipped or failed tools
- Walker state has `emergency_exit=0`

## Outgoing edges

- **`proceed`** → `independent_reviews`. Always taken for this audit. Phase 1 produced whatever it could; Phase 2 proceeds with measured data where available and source-reading where not.

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

The `emergency` edge to `emergency_exit` is structurally present (canonical audit graph) but **never taken** by test-coverage.

## Failure modes

- A coverage tool times out → captured in its `.log` file; orient proceeds. Phase 2 reviewers see the partial output and note the limitation.
- All tooling fails / missing → `STATUS.md` documents the degradation; orient still proceeds. Reviewers do source-reading only.
- Coverage tool produces empty output (e.g. no tests exist) → that itself is a finding for Phase 2 — reviewers note "zero tests" as a Missing-Layer Critical. Don't bail in orient.
