---
name: audit-test-coverage
description: Dual-agent test coverage audit — runs language-appropriate coverage tooling in Phase 1 (Go, Python, Node/Jest, Node/Vitest, Rust, Swift), then reviews coverage gaps, test pyramid balance, test quality, and missing categories. Platform-agnostic. For Apple-specific test design depth (XCTest vs Swift Testing, XCUITest coverage, SwiftUI view testing, Preview coverage, snapshot testing), use `audit-apple-testing`.
---

# Test Coverage Audit

You are orchestrating a dual-agent test coverage audit that runs real
coverage tooling and reviews coverage gaps, test pyramid balance, test
quality, and missing categories.

**Required reading**: Before starting, read [`lib/audit-framework.md`](../lib/audit-framework.md).
This file specifies only the audit-specific deltas.

**Audit identifier**: `test-coverage` — `$AUDIT_DIR` is
`~/Reports/<org>/<repo>/audits/<TS>-test-coverage/`

**Scope**: any codebase. Platform-agnostic. Detects Go, Python, Node
(Jest/Vitest), Rust, and Swift stacks. For Apple-specific test-design
review beyond line coverage, use `audit-apple-testing` — it covers
XCTest vs Swift Testing, SwiftUI view testing, XCUITest critical-flow
coverage, Preview coverage, `@MainActor` test patterns, snapshot
testing strategy.

**Inherent limitations**: Line/branch coverage measures execution,
not correctness. A line covered by a tautological assertion is still
under-tested. Findings reflect both measured gaps and reviewer
judgment about test quality — treat measured coverage as the floor
for findings, not the ceiling.

---

## Schema extensions

Beyond the framework baseline, add:

| Column | Description |
|---|---|
| `Category` | One of: `Gap` (uncovered code path), `Pyramid` (under/over-investment in unit/integration/e2e), `Quality` (brittle/over-mocked/tautological), `Missing-Layer` (entire test category absent) |

Full schema:
```
| ID | Severity | Category | Title | Location | Why It Matters | Recommended Fix | Evidence/Notes |
```

---

## Categories

The audit reviews four areas (the `Category` column distinguishes
them in each finding):

| Category | Covers |
|---|---|
| `Gap` | Untested functions, error paths, branches. Cited against raw coverage data. Critical code paths (auth, payments, data integrity, security boundaries, public API surface) prioritized. |
| `Pyramid` | Under/over-investment per layer. Integration tests doing unit-test work; unit tests so heavily mocked they verify only the mocks; no e2e for flows crossing service boundaries. |
| `Quality` | Tautological assertions, excessive mocking, shared mutable state, flake-prone patterns (`Sleep`, wall-clock, real network in unit tests), tests that pass when the assertion is removed. |
| `Missing-Layer` | Entire layers absent: no integration tests, no e2e for primary user flows, no tests for CLI entry points, no contract tests for external APIs. |

---

## Severity calibration

| Severity | Anchor |
|---|---|
| **Critical** | Production code path with no tests of any kind, or tests so weak they would not catch a known-class regression — especially auth, payments, data integrity, security-sensitive logic |
| **High** | Important code path with significant coverage gap, or no integration/e2e coverage for a flow that crosses trust boundaries |
| **Medium** | Moderate gap or a test-quality issue likely to cause false confidence or flakes |
| **Low** | Minor gap, cosmetic test-quality issue, or test-only code |

Severity calibrates against measured data: a "High" coverage-gap
finding on a file showing 95% line coverage probably belongs at
Medium unless the missing 5% is a critical branch.

---

## Phase 1: Audit-specific orient

### Tooling

Detect the stack and run language-appropriate coverage. Capture
stdout+stderr; write raw output to `$AUDIT_DIR/tooling-raw/`. Always
run with a timeout (`${TO:+$TO 300} …` or `600` for slower stacks).

```bash
mkdir -p "$AUDIT_DIR/tooling-raw"
# Detect a timeout command — macOS doesn't ship one by default.
# Falls back to no timeout (with warning to STATUS.md) if neither is available.
TO=$(command -v timeout || command -v gtimeout || echo "")
[[ -z "$TO" ]] && echo "⚠️ no timeout command available; install via 'brew install coreutils' for tool timeouts" \
  >> "$AUDIT_DIR/tooling-raw/STATUS.md"


# Go
[[ -f go.mod ]] && command -v go >/dev/null && {
  ${TO:+$TO 300} go test -coverprofile="$AUDIT_DIR/tooling-raw/cover.out" \
    -covermode=atomic ./... \
    > "$AUDIT_DIR/tooling-raw/go-test.log" 2>&1
  go tool cover -func="$AUDIT_DIR/tooling-raw/cover.out" \
    > "$AUDIT_DIR/tooling-raw/cover-func.txt" 2>&1
}

# Python (pytest + coverage)
{ [[ -f pyproject.toml ]] || [[ -f pytest.ini ]] || [[ -f setup.cfg ]]; } \
  && command -v pytest >/dev/null && {
  ${TO:+$TO 300} pytest --cov --cov-report=term-missing --cov-report=json \
    > "$AUDIT_DIR/tooling-raw/pytest-cov.log" 2>&1
  [[ -f coverage.json ]] && mv coverage.json "$AUDIT_DIR/tooling-raw/"
}

# Node / Jest
[[ -f package.json ]] && grep -q '"jest"' package.json && {
  ${TO:+$TO 600} npx --yes jest --coverage \
    --coverageReporters=json-summary --coverageReporters=text \
    > "$AUDIT_DIR/tooling-raw/jest.log" 2>&1
}

# Node / Vitest
[[ -f package.json ]] && grep -q '"vitest"' package.json && {
  ${TO:+$TO 600} npx --yes vitest run --coverage \
    > "$AUDIT_DIR/tooling-raw/vitest.log" 2>&1
}

# Rust
[[ -f Cargo.toml ]] && command -v cargo-tarpaulin >/dev/null && {
  ${TO:+$TO 600} cargo tarpaulin --out Stdout \
    > "$AUDIT_DIR/tooling-raw/tarpaulin.log" 2>&1
}

# Swift — Swift Package Manager
[[ -f Package.swift ]] && command -v swift >/dev/null && {
  ${TO:+$TO 600} swift test --enable-code-coverage \
    > "$AUDIT_DIR/tooling-raw/swift-test.log" 2>&1
  # Find the merged profdata and resolve the test binary
  PROFDATA=$(find .build -name '*.profdata' 2>/dev/null | head -1)
  TEST_BIN=$(find .build -path '*debug/*xctest' -type f 2>/dev/null | head -1)
  if [[ -n "$PROFDATA" && -n "$TEST_BIN" ]]; then
    xcrun llvm-cov report -instr-profile="$PROFDATA" "$TEST_BIN" \
      > "$AUDIT_DIR/tooling-raw/swift-cov-summary.txt" 2>&1
    xcrun llvm-cov export -instr-profile="$PROFDATA" "$TEST_BIN" \
      -format=lcov > "$AUDIT_DIR/tooling-raw/swift-cov.lcov" 2>&1
  fi
}

# Swift — Xcode project (heavier; requires a build)
PROJ=$(ls *.xcodeproj 2>/dev/null | head -1)
[[ -n "$PROJ" && -z "$SKIP_XCODEBUILD" ]] && command -v xcodebuild >/dev/null && {
  SCHEME=$(xcodebuild -project "$PROJ" -list 2>/dev/null \
    | awk '/Schemes:/{flag=1;next}/^$/{flag=0}flag{print $1; exit}')
  [[ -n "$SCHEME" ]] && \
    ${TO:+$TO 1800} xcodebuild test -project "$PROJ" -scheme "$SCHEME" \
      -enableCodeCoverage YES -derivedDataPath "$AUDIT_DIR/tooling-raw/dd" \
      CODE_SIGNING_ALLOWED=NO -quiet \
      > "$AUDIT_DIR/tooling-raw/xcodebuild-test.log" 2>&1
}
```

If tooling fails, hangs, isn't installed, or there's no coverage
config: write a note to `$AUDIT_DIR/tooling-raw/STATUS.md` and proceed
with LLM-only review. Both reviewers must be told whether measured
coverage is available.

### Emergency exit

None.

### Survey

Beyond the framework baseline:

- Detect primary language(s) and test framework(s):
  - **Go** — `go.mod`, `*_test.go`, `testing` package
  - **Python** — `pyproject.toml`, `pytest.ini`, `setup.cfg`,
    `tests/`, `test_*.py` / `*_test.py`
  - **Node/TS** — `package.json` test script, `jest.config.*`,
    `vitest.config.*`, `*.test.ts` / `*.spec.ts`
  - **Rust** — `Cargo.toml`, `#[cfg(test)]` blocks, `tests/`
  - **Swift** — `Package.swift` (SPM), `*.xcodeproj/` (Xcode),
    `Tests/`, `*Tests.swift` files, XCTest or `import Testing` (Swift
    Testing)
  - **Ruby** — `Gemfile`, `spec/`, `rspec`
- Identify test layout: unit/integration/e2e locations (e.g.
  `tests/unit/`, `tests/integration/`, `e2e/`, `*_integration_test.go`,
  Swift `@MainActor` test classes, XCUITest target)
- Note CI config — what does CI actually run today?

---

## Phase 2: Codex prompt body

Substitute into the canonical invocation (framework Phase 2 Step 1):

```text
Perform a thorough test coverage audit of [RESOLVED_SCOPE]. Coverage
tooling has already been run; raw output is in
$AUDIT_DIR/tooling-raw/. Read those files first. If
$AUDIT_DIR/tooling-raw/STATUS.md exists, measured coverage was
unavailable — proceed with source-reading only and note that
limitation in your findings.

Write all findings to $AUDIT_DIR/codex.md using this exact table
format for each finding:
| ID | Severity | Category | Title | Location | Why It Matters | Recommended Fix | Evidence/Notes |
where ID uses prefix C (e.g. C001, C002). Category is one of: Gap,
Pyramid, Quality, Missing-Layer.

Cover these four areas:
(1) Coverage gaps — untested functions, error paths, branches. Cite
specific files and line ranges from the raw coverage data. Prioritize
gaps in critical code (auth, payments, data integrity, security
boundaries, public API surface).
(2) Test pyramid balance — over- or under-investment in each layer.
Examples: integration tests doing what unit tests should; unit tests
that mock so much they only verify the mocks; no e2e tests for flows
that cross multiple services.
(3) Test quality — tautological assertions, excessive mocking, shared
mutable state between tests, flake-prone patterns (sleep, wall-clock,
network), tests that pass when the assertion is removed, tests that
duplicate without adding signal.
(4) Missing categories — entire layers absent for important code
(e.g. no integration tests at all; no e2e for the primary user flow;
no tests for the CLI entry point).

Severity is assessed on evidence: criticality of the untested path,
blast radius of a regression, confidence the suite currently
provides. Do not read or reference any other review file.
```

## Phase 2: Claude review checklist

Same 4 areas. Read `$AUDIT_DIR/tooling-raw/` first. Cite specific
files and line ranges from the raw coverage data where available.
Prioritize gaps in critical code paths.

If `tooling-raw/STATUS.md` indicates tooling failed, note the
limitation prominently and rely on source-reading.

---

## Phase 4: Devil's advocate prompt body

```text
Read $AUDIT_DIR/synthesis.md and the raw coverage data in
$AUDIT_DIR/tooling-raw/. Your job is to attack the synthesis, not
improve it. Write your challenge to $AUDIT_DIR/devils-advocate.md
covering:
(1) False positives — findings where the code is actually covered by
a test the reviewer missed, or where the "gap" is unreachable code,
generated code, or a trivial accessor not worth testing.
(2) Severity miscalibrations — findings rated too high (low-risk code
path, well-compensated by other layers) or too low (critical path
masked by an aggregate coverage percentage).
(3) Missing findings — gaps both reviewers missed, especially:
critical error-handling branches, security-sensitive code paths,
data-integrity logic, concurrency/race code with no race-test
coverage.
(4) Recommended fixes that are impractical, would produce low-signal
tests, or duplicate existing coverage.
Be specific. Every challenge must cite the finding ID and, where
applicable, the raw coverage file that supports the challenge.
```

---

## Phase 5: Sprint mapping override

Baseline P0/P1/Deferred mapping applies. Each task must include a
recommended **layer** (unit / integration / e2e) — adding tests at
the wrong layer can be worse than no test. Verification must demand a
measurable outcome: coverage number, specific test scenario, or
mutation check (temporarily break the covered code and confirm the
new test fails). "Tests added" is insufficient.

---

## Output checklist additions

Beyond framework baseline:

- [ ] `$AUDIT_DIR/tooling-raw/` populated, or `STATUS.md` explains why
- [ ] Each task includes a recommended layer (unit / integration / e2e)
- [ ] Each task's verification step demands a measurable outcome
      (coverage number / test scenario / mutation check)
- [ ] When Swift is in scope: confirm `swift test --enable-code-coverage`
      or `xcodebuild test -enableCodeCoverage YES` ran (or STATUS.md
      documents why not)

---

## Reference

- Audit reference doc: [`docs/test-coverage/README.md`](../docs/test-coverage/README.md)
- Framework: [`lib/audit-framework.md`](../lib/audit-framework.md)
- Test Pyramid (Martin Fowler): https://martinfowler.com/articles/practical-test-pyramid.html
- Mutation testing concept: https://en.wikipedia.org/wiki/Mutation_testing
- Swift llvm-cov: https://www.swift.org/documentation/articles/swift-test-coverage.html
