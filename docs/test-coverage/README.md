# Test Coverage Audit Reference

Schema and severity reference for the `/audit-test-coverage` command.

Audit artifacts are written outside this repo to
`~/Reports/<org>/<repo>/audits/<TS>-test-coverage/` — `<org>/<repo>` is
derived from the `upstream` remote (falling back to `origin`), and
`<TS>` is the audit start timestamp (`YYYY-MM-DDTHH-MM-SS`).

Unlike the other audits, Phase 1 of this one runs real coverage tooling
(language-appropriate) and writes its raw output into a `coverage-raw/`
subfolder before the reviewers start. Findings are calibrated against
measured data, not just impressions from reading source.

## Output

Each audit run produces these files in its own timestamped `$AUDIT_DIR`:

| File / Folder | Description |
|---|---|
| `coverage-raw/` | Raw output from the language-appropriate coverage tooling. Contents vary by stack: `cover.out` + `cover-func.txt` (Go), `coverage.json` + `pytest-cov.log` (Python), `jest.log` (Node/Jest), `vitest.log` (Node/Vitest), `tarpaulin.log` (Rust). May also contain `STATUS.md` if tooling could not run. |
| `claude.md` | Claude's independent test coverage review (ID prefix `A`) |
| `codex.md` | Codex's independent test coverage review (ID prefix `C`) |
| `synthesis.md` | Unified, deduplicated findings (canonical `S`-prefix IDs); appends a "Rejected Devil's Advocate Challenges" section after Phase 4 |
| `devils-advocate.md` | Codex's challenge pass against the synthesis |
| `REPORT.md` | Final findings report (the human-facing artifact, P0/P1/Deferred sprint task layout, with coverage summary table) |

`REPORT.md` is reference material. To act on the findings, run
`/sprint-plan` with the report path as the seed prompt:

```
/sprint-plan ~/Reports/<org>/<repo>/audits/<TS>-test-coverage/REPORT.md
```

## Finding Schema

All intermediate audit files (`claude.md`, `codex.md`, `synthesis.md`)
use this table format:

```
| ID | Severity | Category | Title | Location | Why It Matters | Recommended Fix | Evidence/Notes |
```

`synthesis.md` adds a `Sources` column listing the source review IDs each
unified finding merges (e.g. `A002, C003`).

**ID prefix convention:**
- Claude's review: `A001`, `A002`... (Audit)
- Codex's review: `C001`, `C002`... (Codex)
- Synthesis: `S001`, `S002`... (Synthesis canonical)

**Severity levels:** Critical, High, Medium, Low

**Category column** (one per finding):

| Category | Meaning |
|---|---|
| `Gap` | Uncovered code path — function, branch, error path |
| `Pyramid` | Test pyramid imbalance — under/over-investment in unit / integration / e2e layer |
| `Quality` | Brittle, slow, tautological, over-mocked, or low-signal test |
| `Missing-Layer` | Entire test category absent for important code (e.g. no integration tests at all, no e2e for primary user flow) |

**Severity calibration guidance:**

| Severity | Meaning |
|---|---|
| Critical | Production code path with no tests of any kind, or tests so weak they would not catch a known-class regression — especially auth, payments, data integrity, security-sensitive logic |
| High | Important code path with significant coverage gap, or no integration/e2e coverage for a flow that crosses trust boundaries |
| Medium | Moderate gap or a test-quality issue likely to cause false confidence or flakes |
| Low | Minor gap, cosmetic test-quality issue, or test-only code |

Reviewer agreement raises **confidence**, not severity. Severity is also
independent of remediation cost.

## Categories Reviewed

The subagent reviews four areas:

1. **Coverage gaps** — untested functions, branches, error paths; cited
   against the raw coverage data where available. Critical code paths
   (auth, payments, data integrity, security boundaries, public API
   surface) are prioritized.
2. **Test pyramid balance** — under/over-investment in each layer.
   Examples: integration tests doing unit-test work; unit tests so
   heavily mocked they only verify the mocks; no e2e for flows crossing
   service boundaries.
3. **Test quality** — tautological assertions, excessive mocking, shared
   mutable state, flake-prone patterns (`Sleep`, wall-clock, real
   network in unit tests), tests that still pass when the assertion is
   removed, low-signal duplication.
4. **Missing categories** — entire layers absent for important code:
   no integration tests, no e2e for primary user flows, no tests for
   CLI entry points, no contract tests for external APIs.

## Sprint Mapping

`REPORT.md` maps findings to sprint priorities:

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

Each task includes a recommended **layer** (unit / integration / e2e) —
adding tests at the wrong layer can be worse than no test. Each task
also includes a verification step that demands a measurable outcome
(coverage number, specific test scenario, or mutation check: temporarily
break the covered code and confirm the new test fails).

## Inherent Limitations

Line/branch coverage measures execution, not correctness. A line covered
by a tautological assertion is still under-tested. Findings reflect
**both** measured gaps and reviewer judgment about test quality —
treat measured coverage as the floor for findings, not the ceiling.

If the coverage tooling could not run, `coverage-raw/STATUS.md`
documents what was attempted and what failed; the reviewers fall back to
source-reading and note that limitation prominently in their findings.

## References

- Subagent definition: [`../../subagents/audit-test-coverage.md`](../../subagents/audit-test-coverage.md)
- Test Pyramid (Martin Fowler): https://martinfowler.com/articles/practical-test-pyramid.html
- Mutation testing concept: https://en.wikipedia.org/wiki/Mutation_testing
