Perform a thorough test coverage audit of the scope at the project root
you've been pointed at. Coverage tooling has already been run; raw output
is in the audit dir's tooling-raw/ subdirectory. Read those files first:
cover.out / cover-func.txt (Go), pytest-cov.log / coverage.json
(Python), jest.log (Node Jest), vitest.log (Node Vitest), tarpaulin.log
or cargo-llvm-cov.log (Rust), swift-test.log / swift-cov-summary.txt /
swift-cov.lcov (Swift SPM), xcodebuild-test.log (Xcode), STATUS.md
(skipped or failed tools).

If $AUDIT_DIR/tooling-raw/STATUS.md indicates measured coverage was
unavailable, proceed with source-reading only and note that limitation
prominently in your findings.

Write all findings to codex.md (in the audit dir you were granted write
access to) using this exact table format:

| ID | Severity | Category | Title | Location | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix C (e.g. C001, C002). Category is one of: Gap,
Pyramid, Quality, Missing-Layer. Severity is Critical | High | Medium |
Low.

Cover these four areas:

(1) Gap — coverage gaps. Untested functions, error paths, branches.
Cite specific files and line ranges from the raw coverage data.
Prioritize gaps in critical code (auth, payments, data integrity,
security boundaries, public API surface). A high overall coverage % can
mask a critical-path gap; cross-check against per-file/per-function
data, not just totals.

(2) Pyramid — test pyramid balance. Over- or under-investment per
layer. Examples: integration tests doing what unit tests should; unit
tests that mock so much they only verify the mocks; no e2e tests for
flows that cross multiple services or trust boundaries; the test suite
that's 95% unit, 5% integration, 0% e2e for a system with non-trivial
inter-service contracts.

(3) Quality — test quality. Tautological assertions, excessive mocking,
shared mutable state between tests, flake-prone patterns (sleep,
wall-clock, real network in unit tests), tests that pass when the
assertion is removed, tests that duplicate without adding signal,
tests that exist purely to satisfy a coverage threshold.

(4) Missing-Layer — entire layers absent for important code. No
integration tests at all; no e2e for the primary user flow; no tests
for the CLI entry point; no contract tests for external APIs; no
property/fuzz tests for parsers or serializers; no benchmarks for
performance-sensitive code where regressions would matter.

Severity calibration anchored examples:

Critical:
- Production code path with no tests of any kind, especially auth,
  payments, data integrity, security-sensitive logic
- Tests so weak they would not catch a known-class regression
- Zero tests in the entire project

High:
- Important code path with significant coverage gap
- No integration/e2e coverage for a flow that crosses trust boundaries
- Heavy reliance on mocks that verify only the mocks for critical logic
- Critical assertion masked by an over-broad `expect(...).toBeDefined()`

Medium:
- Moderate gap on important-but-not-critical code
- Test-quality issue likely to cause false confidence or flakes
  (wall-clock, sleep, shared state)
- Missing layer for a less-critical subsystem

Low:
- Minor gap on rarely-exercised code
- Cosmetic test-quality issue, test-only code

Severity is assessed on evidence: criticality of the untested path,
blast radius of a regression, confidence the suite currently provides.
Severity is independent of remediation cost. A High Gap on a file
showing 95% line coverage probably belongs at Medium unless the missing
5% is a critical branch.

Inherent limitation: line/branch coverage measures execution, not
correctness. A line covered by a tautological assertion is still
under-tested. Treat measured coverage as the floor for findings, not
the ceiling — use it to anchor the cited gaps, and use judgment to
identify weakly-tested covered paths.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to codex.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
