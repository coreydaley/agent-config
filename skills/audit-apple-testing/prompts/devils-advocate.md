Read synthesis.md and the raw tooling output in tooling-raw/ in the
audit dir you've been granted access to. Your job is to attack the
synthesis, not improve it.

Write your challenge to devils-advocate.md (in the same audit dir)
using this table format:

| ID | Challenge Type | Target Finding | Claim | Evidence | Confidence |

where:
- ID uses prefix D (D001, D002, ...)
- Challenge Type: false_positive | severity_miscalibrated |
  missing_finding | missing_compound | impractical_remediation |
  insufficient_verification
- Target Finding: the S### ID from synthesis.md being challenged
  (or "N/A" for missing_finding / missing_compound)
- Claim: 1-2 sentence challenge
- Evidence: file:line citation, compensating control identification, or
  specific code reference
- Confidence: high | medium | low

Cover these challenge categories:

(1) False positives — findings that don't apply because of project
constraints. Specifically for Apple testing:
- Swift Testing migration finding on a project pinned to an older
  Xcode/toolchain that doesn't ship Swift Testing.
- UI test finding on a target that genuinely doesn't need UI tests
  (watchOS complication, widget extension that's purely declarative,
  daemon target).
- Preview finding on a private/internal type that isn't visible to
  consumers.
- Snapshot AX/dark-mode gap on a screen that's always one mode
  (e.g. an in-app camera viewfinder).
- Mocking-strategy finding on a target that doesn't have network or
  persistence dependencies.

(2) Severity miscalibrations — findings rated too high (a test that
LOOKS tautological but actually asserts something subtle; a missing
XCUITest where unit + integration cover the same regression surface)
or too low (missing UI tests on a primary purchase flow is Critical,
not High; tautological test on a payment path is Critical, not
Medium).

(3) Missing findings — Apple-testing issues the review missed:
- Swift 6 strict-concurrency-related test fragility (data races
  surfacing only under -strict-concurrency=complete).
- SwiftData @MainActor model fetches in tests (or the reverse:
  background-context tests doing main-actor work).
- MainActor isolation gaps causing real bugs the test suite ratifies.
- XCUITest accessibility-identifier collisions across screens.
- Fixture data drift from production schemas.
- Missing test coverage on App Intents / Live Activities / Widgets /
  share extensions / custom keyboards.
- Test plan configurations missing localizations / dark mode / AX
  variants.
- Snapshot tests with platform-dependent baselines (Intel vs
  Apple Silicon, macOS version variance).
- CI does not run the UI test target on every PR.
- Tests that only run in Debug configuration.

(4) Missing compound paths — separate findings in the synthesis that
combine into a worse risk than any single finding represents (e.g. no
unit tests on payments AND no XCUITest on payments AND tautological
tests in the receipts module = total absence of regression coverage on
the revenue path). Be explicit about the chain and the combined
severity.

(5) Impractical/incomplete/wrong remediations:
- Adding XCUITest where unit tests would suffice (XCUITest is slow,
  flaky, and expensive — only justified for primary user flows).
- Adding snapshot tests that will be brittle (animated screens,
  date-dependent content, font-rendering variance).
- Moving wholesale to Swift Testing without considering team
  familiarity / build-server toolchain.
- "Add mock for X" when the real issue is the design (heavy mocking
  hiding tight coupling — fix the seam, don't add more mocks).

(6) Insufficient verification steps — for testing audits, every
remediation needs a mutation check: temporarily break the production
code (or remove the assertion), confirm the new test fails. "Test
added" without that step is insufficient. Also: the test must run in
CI on every PR, not just locally. Verification steps that don't
include both are insufficient.

Be specific. Every challenge must cite the finding ID and the
TestLayer.

Do not read or reference any other review file beyond synthesis.md
and the tooling-raw/ directory.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type
  "no_challenges" and Confidence "high" stating that you attempted but
  found nothing worth surfacing.
- No emojis.
