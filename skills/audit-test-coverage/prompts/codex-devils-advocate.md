Read synthesis.md and the raw coverage data in tooling-raw/ in the
audit dir you've been granted access to. Your job is to attack the
synthesis, not improve it.

Write your challenge to devils-advocate.md (in the same audit dir)
using this table format:

| ID | Challenge Type | Target Finding | Claim | Evidence | Confidence |

where:
- ID uses prefix D (D001, D002, ...)
- Challenge Type: false_positive | severity_miscalibrated | missing_finding | missing_compound | impractical_remediation | insufficient_verification
- Target Finding: the S### ID from synthesis.md being challenged (or "N/A" for missing_finding / missing_compound)
- Claim: 1-2 sentence challenge
- Evidence: file:line citation, raw coverage file that supports the challenge, named test that exists and covers the path, or specific code reference
- Confidence: high | medium | low

Cover these challenge categories:

(1) False positives — findings where the code is actually covered by a
test the reviewer missed, or where the "gap" is unreachable code,
generated code, a trivial accessor not worth testing, a test fixture, or
a debug-only branch. Always cite the test file/line that disproves the
gap, or the coverage report row showing the line is actually covered.

(2) Severity miscalibrations — findings rated too high (low-risk code
path, well-compensated by a higher-layer test that does cover the
behaviour end-to-end) or too low (critical path masked by an aggregate
coverage percentage). Be specific about the compensating coverage or
the missing-but-critical branch.

(3) Missing findings — coverage gaps both reviewers missed,
especially:
- Critical error-handling branches with no test
- Security-sensitive code paths (auth, authorization, input validation)
  with weak or absent tests
- Data-integrity logic (transactions, migrations, conflict resolution)
  with no test
- Concurrency / race code with no race-condition test (Go: `-race`
  flag; Rust: loom; threads/goroutines spawned without a test that
  actually exercises interleaving)
- Boundary-condition tests absent for parsers, serializers, numeric
  ranges
- Property-based / fuzz testing absent on functions that obviously
  warrant it
- Contract tests absent for external API consumers (vendor breaking
  change undetectable)

(4) Missing compound paths — separate findings in the synthesis that
combine into a worse exploit/risk than any single finding represents.
Be explicit about the chain and the combined severity.

(5) Impractical/incomplete/wrong remediations — e.g. "add unit tests"
where the bug class is integration-level; "achieve 90% coverage" with
no mention of which branches; suggested tests that duplicate existing
coverage; suggested integration tests that would actually verify only
the mocks; suggested e2e tests for code that has no production caller.

(6) Insufficient verification — verification steps that don't actually
prove the fix works. "Tests added" is insufficient. The verification
must demand a measurable outcome: a coverage number, a named test
scenario that would now pass, OR a mutation check (temporarily break
the covered code and confirm the new test fails). Flag any task whose
verification step doesn't meet this bar.

Be specific. Every challenge must cite the finding ID and, where
applicable, the raw coverage file or test file that supports the
challenge.

Do not read or reference any other review file beyond synthesis.md and
the tooling-raw/ directory.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type "no_challenges"
  and Confidence "high" stating that you attempted but found nothing
  worth surfacing.
- No emojis.
