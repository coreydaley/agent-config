---
name: audit-apple-testing
description: Dual-agent Apple platform test-design audit — XCTest vs Swift Testing (Xcode 16), XCUITest critical-flow coverage, SwiftUI view-testing strategy, Preview coverage, snapshot testing, @MainActor in tests, async test patterns. Goes beyond line coverage into test quality. Uses `audit-test-coverage` raw data if present.
---

# Apple Platform Testing Audit

You are orchestrating a dual-agent audit of test design and coverage
strategy for a native Apple app — beyond line coverage into the
unique testing concerns of Apple platforms.

**Required reading**: Before starting, read [`lib/audit-framework.md`](../lib/audit-framework.md).
This file specifies only the audit-specific deltas.

**Audit identifier**: `apple-testing` — `$AUDIT_DIR` is
`~/Reports/<org>/<repo>/audits/<TS>-apple-testing/`

**Scope**: Swift source files for native Apple apps and their test
targets. For platform-agnostic line/branch coverage measurement, use
`audit-test-coverage` — this audit can reuse its `tooling-raw/`
output if it's been run.

**Inherent limitations**: Test quality is partly objective (test
fails when assertion is removed → real test; otherwise tautological)
and partly judgment (is *this* the right test to write?). Static
review catches the objective parts; judgment requires team context.

---

## Schema extensions

Beyond the framework baseline, add:

| Column | Description |
|---|---|
| `TestLayer` | The test layer affected: `Unit`, `Integration`, `UI` (XCUITest), `Preview`, `Snapshot`, `Performance`, `Fixture` |
| `Framework` | Test framework: `XCTest`, `Swift Testing` (Xcode 16+), `SwiftUI Preview`, `XCUITest`, `Snapshot library`, or `Other` |
| `Verification` | `code` (inspectable) or `runtime` (requires running the test suite) |

Full schema:
```
| ID | Severity | TestLayer | Framework | Title | Location | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

---

## Categories

The audit reviews ten categories:

| # | Category | Covers |
|---|---|---|
| 1 | XCTest vs Swift Testing migration (Xcode 16+) | Swift Testing offers better ergonomics (`@Test`, `#expect`, parameterized tests, suites). New tests should use it; legacy XCTest is fine but flag opportunities |
| 2 | Test isolation & `@MainActor` | UI-touching tests on MainActor; state isolation between tests (fresh fixtures per test); no shared mutable state across tests |
| 3 | Async test patterns | `async` test methods over `XCTestExpectation` where Swift Concurrency applies; `Task.cancel` testing; testing actor-isolated code; timeouts |
| 4 | XCUITest UI flow coverage | Primary user flows have XCUITest coverage (onboarding, sign-in, primary purchase, primary content creation); UI tests use accessibility identifiers (not text matching where text is localized) |
| 5 | SwiftUI view testing strategy | Strategy for view testing: ViewInspector / snapshot testing / preview-based / business-logic-only-in-VM. Verify the project has a coherent strategy, not all four |
| 6 | Preview coverage | Every public View has at least one `#Preview`; previews exercise representative states; preview data uses realistic fixtures (no real network) |
| 7 | Snapshot testing | If snapshot testing is used (`SnapshotTesting`, `AccessibilitySnapshot`): tests cover light + dark + AX text size; snapshots are reviewed when updated; per-device-size matrices used where layout varies |
| 8 | Mocking & dependency injection | Tests use protocols-at-boundaries DI not heavyweight mocking; in-memory stores for SwiftData / Core Data tests; no real network in unit tests; clock injection for time-dependent code |
| 9 | Tautological & flaky tests | Tests that pass when the assertion is removed (no signal); time-based assertions without injected clocks; wall-clock `sleep`; tests that depend on Run Order |
| 10 | Test fixtures & data | Test fixtures realistic and centralized; SwiftData / Core Data test models in dedicated `Tests/Fixtures/`; no test depending on Bundle.main resources that don't exist in test target |

---

## Severity calibration

| Severity | Anchor |
|---|---|
| **Critical** | Production code path with zero tests on a primary flow (auth, payments, data persistence); test that passes regardless of code behavior (tautological); shared mutable state causing intermittent failures |
| **High** | No XCUITest coverage on a primary user flow; no SwiftUI view testing strategy at all for a large SwiftUI app; mocking strategy that hides real bugs |
| **Medium** | Suboptimal patterns: still on XCTestExpectation when async would be cleaner; missing previews on important Views; snapshot tests not covering AX5 / dark mode |
| **Low** | Migration opportunities to Swift Testing; minor fixture cleanup |

---

## Phase 1: Audit-specific orient

### Tooling

If `audit-test-coverage` has been run recently on this scope, reuse
its `tooling-raw/` output. Otherwise, run minimal coverage tooling:

```bash
mkdir -p "$AUDIT_DIR/tooling-raw"

# Reuse audit-test-coverage data if present
LATEST_COV=$(ls -dt "$HOME/Reports/$ORG_REPO/audits/"*-test-coverage 2>/dev/null | head -1)
if [[ -n "$LATEST_COV" && -d "$LATEST_COV/tooling-raw" ]]; then
  echo "Reusing coverage data from $LATEST_COV" \
    > "$AUDIT_DIR/tooling-raw/COVERAGE-SOURCE.md"
  cp -R "$LATEST_COV/tooling-raw/"* "$AUDIT_DIR/tooling-raw/" 2>/dev/null
else
  # Run Swift coverage directly
  [[ -f Package.swift ]] && command -v swift >/dev/null && \
    timeout 600 swift test --enable-code-coverage \
      > "$AUDIT_DIR/tooling-raw/swift-test.log" 2>&1
fi

# Inventory test targets and frameworks in use
{
  echo "=== Test target files ===";
  find "$PROJECT_CWD" -name "*Tests.swift" -not -path '*/.*' 2>/dev/null;
  echo;
  echo "=== UI test target files ===";
  find "$PROJECT_CWD" -name "*UITests.swift" -not -path '*/.*' 2>/dev/null;
  echo;
  echo "=== Swift Testing usage (@Test, #expect) ===";
  grep -rln "@Test\|#expect\|import Testing" --include="*.swift" "$PROJECT_CWD" 2>/dev/null;
  echo;
  echo "=== XCTest usage (legacy) ===";
  grep -rln "XCTestCase\|XCTAssert" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -20;
  echo;
  echo "=== XCUITest usage ===";
  grep -rln "XCUIApplication\|XCUIElement" --include="*.swift" "$PROJECT_CWD" 2>/dev/null;
  echo;
  echo "=== SwiftUI Preview count ===";
  grep -rln "#Preview\|PreviewProvider" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | wc -l;
  echo;
  echo "=== Snapshot testing libraries ===";
  grep -rln "SnapshotTesting\|assertSnapshot\|AccessibilitySnapshot" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -10;
} > "$AUDIT_DIR/tooling-raw/test-inventory.txt"
```

### Emergency exit

None.

### Survey

Beyond the framework baseline:

- Read `tooling-raw/test-inventory.txt` to see what test frameworks
  and patterns the project uses
- Determine deployment target (affects Swift Testing availability —
  requires Xcode 16+ / Swift 6)
- Identify the project's SwiftUI view-testing strategy (if any):
  ViewInspector? snapshot testing? business logic in view models
  only?
- Note CI configuration — does it actually run the UI test target?
- **If no Swift/Apple source found**: notify and stop

---

## Phase 2: Codex prompt body

Substitute into the canonical invocation (framework Phase 2 Step 1):

```text
Perform a thorough Apple platform testing audit of [RESOLVED_SCOPE].
Goes BEYOND line coverage into test design and quality unique to
Apple. Tooling output is in $AUDIT_DIR/tooling-raw/ — check
COVERAGE-SOURCE.md to see if coverage data came from a recent
audit-test-coverage run.

Write all findings to $AUDIT_DIR/codex.md using this exact table
format:
| ID | Severity | TestLayer | Framework | Title | Location | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
where ID uses prefix C (e.g. C001, C002).

TestLayer column: Unit, Integration, UI (XCUITest), Preview,
Snapshot, Performance, Fixture.
Framework: XCTest, Swift Testing (Xcode 16+), SwiftUI Preview,
XCUITest, Snapshot library, or Other.
Verification: code or runtime (requires running the test suite).

Cover these 10 categories:
(1) XCTest vs Swift Testing migration (Xcode 16+) — Swift Testing
offers better ergonomics (@Test, #expect, parameterized,
@Suite). New tests should use it where deployment target supports
it. Flag migration opportunities, but don't demand wholesale rewrite.
(2) Test isolation & @MainActor — UI-touching tests on MainActor;
state isolation between tests (fresh fixtures per test); no shared
mutable state across tests; Swift Testing's per-test instance vs
XCTest's setUp/tearDown.
(3) Async test patterns — async test methods over XCTestExpectation
where Swift Concurrency applies; Task.cancel testing; testing actor-
isolated code; explicit timeouts.
(4) XCUITest UI flow coverage — primary user flows have XCUITest
coverage (onboarding, sign-in, primary purchase, primary content
creation); UI tests use accessibility identifiers (not text matching
where text is localized).
(5) SwiftUI view testing strategy — verify the project has A
coherent strategy: ViewInspector OR snapshot testing OR preview-based
OR business-logic-only-in-VM. Not all four. Verify it's actually
applied where complex views live.
(6) Preview coverage — every public View has at least one #Preview;
previews exercise representative states (empty, loading, error,
populated); preview data uses realistic fixtures (no real network).
(7) Snapshot testing — if used: tests cover light + dark + AX text
size; snapshots reviewed when updated; per-device-size matrices
where layout varies.
(8) Mocking & dependency injection — tests use protocols-at-
boundaries DI not heavyweight mocking; in-memory stores for SwiftData
/ Core Data tests; no real network in unit tests; clock injection
for time-dependent code.
(9) Tautological & flaky tests — tests that pass when the assertion
is removed (no signal); time-based assertions without injected
clocks; wall-clock sleep; run-order dependence; tests depending on
real network / real device IDs.
(10) Test fixtures & data — realistic, centralized; SwiftData / Core
Data test models in dedicated Tests/Fixtures/; no test depending on
Bundle.main resources that don't exist in test target.

Rate severity: critical = production path zero-tested or
tautological; high = primary flow without UI tests; medium =
suboptimal but functional; low = migration opportunities.

Do not read or reference any other review file.
```

## Phase 2: Claude review checklist

Same 10 categories. Read `tooling-raw/test-inventory.txt` first.
Look at actual test files — not just inventory. The most important
thing is whether tests would catch real regressions on critical
paths.

---

## Phase 4: Devil's advocate prompt body

```text
Read $AUDIT_DIR/synthesis.md and the tooling output in
$AUDIT_DIR/tooling-raw/. Your job is to attack the synthesis, not
improve it. Write your challenge to $AUDIT_DIR/devils-advocate.md
covering:
(1) False positives — findings that don't apply because of project
constraints (e.g. Swift Testing migration finding on a project with
iOS 15 deployment target; UI test finding on a watchOS complication
that genuinely doesn't need UI tests; preview finding on a private
type not exposed).
(2) Severity miscalibrations — findings rated too high (a test that
LOOKS tautological but actually asserts something subtle); too low
(missing UI tests on a primary purchase flow is Critical, not High).
(3) Missing findings — testing issues both reviewers missed,
especially: Swift 6 strict-concurrency-related test fragility,
SwiftData @MainActor model fetches in tests, MainActor isolation
gaps causing real bugs, XCUITest accessibility-identifier collisions,
fixture data drift from production schemas, missing test
coverage on App Intents / Live Activities / Widgets / share
extensions, test plan configurations missing localizations / dark
mode coverage.
(4) Remediation steps that are wrong — adding XCUITest where unit
tests would suffice, adding snapshot tests that will be brittle,
moving to Swift Testing without considering team familiarity.
Be specific. Every challenge must cite the finding ID and the
TestLayer.
```

---

## Phase 5: Sprint mapping override

Baseline P0/P1/Deferred mapping applies. Each task's verification
must demand a measurable outcome — the test exists, runs in CI, and
catches a known regression (mutation check: temporarily break the
code, confirm the test fails). "Test added" is insufficient.

---

## Output checklist additions

Beyond framework baseline:

- [ ] Each task has: finding ID, TestLayer, Framework, Verification
      mode, location, issue, remediation, verification with mutation
      check
- [ ] Critical findings (zero-tested production paths) listed
      first in the report
- [ ] Hand-off note recommends running the test suite in CI after
      task completion, not just locally

---

## Reference

- Audit reference doc: [`docs/apple-testing/README.md`](../docs/apple-testing/README.md)
- Framework: [`lib/audit-framework.md`](../lib/audit-framework.md)
- Swift Testing: https://developer.apple.com/xcode/swift-testing/
- XCTest: https://developer.apple.com/documentation/xctest
- XCUITest: https://developer.apple.com/documentation/xctest/user_interface_tests
- SnapshotTesting: https://github.com/pointfreeco/swift-snapshot-testing
- SwiftUI Previews: https://developer.apple.com/documentation/swiftui/preview
- Apple's testing guide: https://developer.apple.com/documentation/xcode/testing-your-apps-in-xcode
