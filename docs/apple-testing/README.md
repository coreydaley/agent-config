# Apple Platform Testing Audit Reference

Schema and severity reference for the `/audit-apple-testing` command.
Goes beyond line coverage into the unique testing concerns of Apple
platforms. For platform-agnostic line/branch coverage, see
[`../test-coverage/README.md`](../test-coverage/README.md). For the
shared 5-phase audit pattern, see [`../../lib/audit-framework.md`](../../lib/audit-framework.md).

Audit artifacts: `~/Reports/<org>/<repo>/audits/<TS>-apple-testing/`

## Output

| File / Folder | Description |
|---|---|
| `tooling-raw/` | `test-inventory.txt` (XCTest / Swift Testing / XCUITest / Preview / snapshot library inventory), reused coverage data from `audit-test-coverage` if available, `COVERAGE-SOURCE.md` documenting the source |
| `claude.md` | Claude's review (ID prefix `A`) |
| `codex.md` | Codex's review (ID prefix `C`) |
| `synthesis.md` | Unified findings (`S`-prefix IDs) |
| `devils-advocate.md` | Codex challenge |
| `REPORT.md` | Sprint-able findings report |

## Schema

```
| ID | Severity | TestLayer | Framework | Title | Location | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

**TestLayer**: `Unit`, `Integration`, `UI` (XCUITest), `Preview`,
`Snapshot`, `Performance`, `Fixture`.

**Framework**: `XCTest`, `Swift Testing` (Xcode 16+), `SwiftUI Preview`,
`XCUITest`, `Snapshot library`, or `Other`.

**Verification**: `code` or `runtime` (requires running the test suite).

## Categories

1. XCTest vs Swift Testing (Xcode 16+) migration opportunities
2. Test isolation & `@MainActor`
3. Async test patterns (`async`/`await` over `XCTestExpectation`)
4. XCUITest critical-flow coverage (onboarding, sign-in, primary purchase)
5. SwiftUI view-testing strategy
6. Preview coverage
7. Snapshot testing strategy (light/dark/AX5 matrices)
8. Mocking & dependency injection
9. Tautological & flaky tests
10. Test fixtures & data

## Severity (default mapping)

| Issue | Severity |
|---|---|
| Production code path with zero tests on primary flow (auth, payments, persistence) | Critical |
| Test that passes regardless of code behavior (tautological) | Critical |
| Shared mutable state causing intermittent failures | Critical |
| No XCUITest coverage on a primary user flow | High |
| No SwiftUI view-testing strategy at all for large SwiftUI app | High |
| Mocking strategy that hides real bugs | High |
| Suboptimal patterns (XCTestExpectation when async would be cleaner) | Medium |
| Missing previews on important Views | Medium |
| Snapshot tests not covering AX5 / dark mode | Medium |
| Swift Testing migration opportunities | Low |

## Sprint Mapping

Baseline `P0/P1/Deferred`. Each task's verification must demand a
**mutation check**: temporarily break the code, confirm the new test
fails. "Test added" is insufficient.

## Inherent Limitations

Test quality is partly objective (mutation-check works) and partly
judgment (is *this* the right test to write?). Static review catches
the objective parts; judgment requires team context.

## References

- Subagent: [`../../subagents/audit-apple-testing.md`](../../subagents/audit-apple-testing.md)
- Sibling: [`../test-coverage/README.md`](../test-coverage/README.md)
- Swift Testing: https://developer.apple.com/xcode/swift-testing/
- XCTest: https://developer.apple.com/documentation/xctest
- XCUITest: https://developer.apple.com/documentation/xctest/user_interface_tests
- SwiftUI Previews: https://developer.apple.com/documentation/swiftui/preview
- SnapshotTesting: https://github.com/pointfreeco/swift-snapshot-testing
