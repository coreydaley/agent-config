You are an INDEPENDENT reviewer. You did NOT write the code or artifact
under review — approach it with fresh eyes and review it on its merits alone.
(The Claude session that invoked this audit may well have authored what you
are now reviewing; that is exactly why this review is delegated to you rather
than done in that session, which would share its own blind spots.)

Write your findings to claude.md (ID prefix A) per the specification below.

Perform a thorough Apple platform testing audit of the scope at the
project root you've been pointed at. This audit goes BEYOND line
coverage into test design and quality unique to Apple. Tooling has
already been run; raw output is in the audit dir's tooling-raw/
subdirectory — read test-inventory.txt to see which test frameworks the
project uses, and swift-test.log for coverage output if it ran.

Write all findings to claude.md (in the audit dir you were granted
write access to) using this exact table format:

| ID | Severity | TestLayer | Framework | Title | Location | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix A (e.g. A001, A002).

TestLayer: Unit, Integration, UI (XCUITest), Preview, Snapshot,
Performance, Fixture.
Framework: XCTest, Swift Testing (Xcode 16+), SwiftUI Preview,
XCUITest, Snapshot library, or Other.
Verification: code (inspectable) or runtime (requires running the test
suite).

DO NOT measure or report raw line/branch coverage percentages — this
audit is about test DESIGN and quality, not coverage measurement.

Cover these 10 categories (skip if not applicable):

(1) XCTest vs Swift Testing migration (Xcode 16+) — Swift Testing
offers better ergonomics (@Test, #expect, parameterized, @Suite). New
tests should use it where the project's toolchain supports it (Xcode
16+). Swift Testing is gated by toolchain, NOT by the app's
iOS/macOS deployment target — do not infer support from deployment
target alone. Flag migration opportunities, but don't demand wholesale
rewrites of working XCTest suites.

(2) Test isolation & @MainActor — UI-touching tests on @MainActor;
state isolation between tests (fresh fixtures per test); no shared
mutable state across tests; Swift Testing's per-test instance vs
XCTest's setUp/tearDown semantics.

(3) Async test patterns — async test methods over XCTestExpectation
where Swift Concurrency applies; Task.cancel testing; testing
actor-isolated code; explicit timeouts; no wall-clock sleep.

(4) XCUITest UI flow coverage — primary user flows have XCUITest
coverage (onboarding, sign-in, primary purchase, primary content
creation); UI tests use accessibility identifiers (not text matching
where text is localized). XCUITest is cross-platform but the primary
flows differ per platform: scope expectations to the project's
detected target platforms. For iOS-distinctive XCUITest affordances
(scene lifecycle handoff, Lock Screen / StandBy widget surfaces,
Dynamic Island), cross-ref audit-apple-ios. For macOS-distinctive
XCUITest surface (menu bar, AppKit accessibility tree, document-
based apps), cross-ref audit-apple-macos.

(5) SwiftUI view-testing strategy — verify the project has A coherent
strategy: ViewInspector OR snapshot testing OR preview-based OR
business-logic-only-in-VM. Not all four. Verify it's actually applied
where complex views live; a strategy that exists only in one file
isn't a strategy.

(6) Preview coverage — every public View has at least one #Preview;
previews exercise representative states (empty, loading, error,
populated); preview data uses realistic fixtures (no real network).

(7) Snapshot testing — if used (SnapshotTesting, AccessibilitySnapshot,
etc.): tests cover light + dark + AX text size; snapshots are reviewed
by eye when updated (not rubber-stamped); per-device-size matrices
where layout varies.

(8) Mocking & dependency injection — tests use protocols-at-boundaries
DI not heavyweight mocking frameworks; in-memory stores for SwiftData
/ Core Data tests; no real network in unit tests; clock injection for
time-dependent code.

(9) Tautological & flaky tests — tests that pass when the assertion
is removed (no signal); time-based assertions without injected clocks;
wall-clock sleep; run-order dependence; tests that depend on real
network / real device IDs / Bundle.main resources unavailable in test
target.

(10) Test fixtures & data — realistic, centralized; SwiftData / Core
Data test models in dedicated Tests/Fixtures/; no test depending on
Bundle.main resources that don't exist in the test target.

Rate severity on evidence:

Critical anchors:
- Production code path with zero tests on a primary flow (auth,
  payments, data persistence)
- Test that passes regardless of code behavior (tautological)
- Shared mutable state causing intermittent failures

High anchors:
- No XCUITest coverage on a primary user flow
- No SwiftUI view-testing strategy at all for a large SwiftUI app
- Mocking strategy that hides real bugs (e.g. mock unconditionally
  returns success)

Medium anchors:
- Suboptimal patterns: still on XCTestExpectation when async would be
  cleaner
- Missing previews on important Views
- Snapshot tests not covering AX5 / dark mode
- CI does not run the UI test target

Low anchors:
- Swift Testing migration opportunities on working XCTest suites
- Minor fixture cleanup
- Preview-only gaps on internal/private Views

Every finding must include a Verification field. For Apple testing,
runtime verification means: temporarily break the production code
(mutation check) and confirm the test fails. Code-only verification is
allowed only when the test's tautological nature can be read off the
source.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to claude.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
