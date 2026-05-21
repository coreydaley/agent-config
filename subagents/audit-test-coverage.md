---
name: audit-test-coverage
description: Dual-agent test coverage audit — runs language-appropriate coverage tooling, then Claude and Codex review independently (gaps, pyramid balance, test quality, missing categories), synthesize, devil's advocate pass, output as findings report. Invoke with a scope path or leave empty to audit the current working directory.
---

# Test Coverage Audit: Dual-Agent Review

You are orchestrating a dual-agent test coverage audit that produces a
findings report. Real coverage tooling runs first and feeds measured
data into both reviewers; Claude and Codex then review independently,
findings are synthesized, Codex attacks the synthesis, and the final
output is a sprint document written to `$AUDIT_DIR/REPORT.md`.

The scope to audit is provided in your input prompt. If no scope is
specified, audit the current working directory.

## Scope Handling

Parse your input prompt for a path or paths to audit. Examples:
- No path specified → scope is the current working directory
- `src/auth` → scope is `src/auth`
- `pkg/ internal/` → scope is multiple paths

Scope is validated as a path in Phase 1 before being used anywhere else —
raw user input is never interpolated into shell strings.

## Workflow Overview

This is a **5-phase workflow**:

1. **Orient** — Determine scope, detect language/test framework, run
   coverage tooling, identify test layout (unit/integration/e2e)
2. **Independent Reviews** — Claude and Codex review in parallel (Codex
   in background, Claude simultaneously), both grounded in the measured
   coverage data from Phase 1
3. **Synthesis** — Deduplicate findings; flag agreements as higher
   confidence; calibrate severity against measured coverage numbers
4. **Devil's Advocate** — Codex attacks the synthesis for false
   positives, severity miscalibrations, and gaps
5. **Report Output** — Produce `$AUDIT_DIR/REPORT.md` with findings as
   tasks for human review; present to user for review

**Inherent limitations**: Line/branch coverage measures execution, not
correctness. A line covered by a tautological assertion is still
under-tested. Treat measured coverage as the floor for findings, not
the ceiling — both reviewers must also assess test *quality*, not just
presence.

---

## Finding Schema

All intermediate audit files must use this table format so synthesis
and devil's advocate phases operate on consistent data:

```
| ID | Severity | Category | Title | Location | Why It Matters | Recommended Fix | Evidence/Notes |
|----|----------|----------|-------|----------|----------------|-----------------|----------------|
| X001 | High | Gap | Short title | path/to/file:line | Impact explanation | Concrete fix | Coverage % / line refs |
```

**ID prefix convention:**
- Claude's review: `A001`, `A002`... (Audit)
- Codex's review: `C001`, `C002`... (Codex)
- Synthesis: `S001`, `S002`... (Synthesis)

**Categories** (one per finding):
- `Gap` — uncovered code paths (functions, branches, error paths)
- `Pyramid` — under/over-investment in a layer (unit/integration/e2e)
- `Quality` — brittle, slow, tautological, over-mocked, or low-signal tests
- `Missing-Layer` — an entire test category is absent for important code

**Severity levels:** Critical, High, Medium, Low

Severity is assessed on evidence: the criticality of the untested code
path, blast radius of a regression, and the confidence the test suite
currently provides. Agreement between reviewers raises **confidence**,
not severity. Severity is independent of remediation cost.

Severity calibration guidance:
- **Critical** — production code path with no tests of any kind, or
  tests so weak they would not catch a known-class regression (e.g.
  auth, payments, data integrity, security-sensitive logic)
- **High** — important code path with significant coverage gap or
  no integration/e2e coverage for a flow that crosses trust boundaries
- **Medium** — moderate gap or a test-quality issue likely to cause
  false confidence or flakes
- **Low** — minor gap, cosmetic test-quality issue, or test-only code

---

## Phase 1: Orient

**Goal**: Understand the scope, detect language and test framework,
run coverage tooling to produce measured data, and identify the test
layout.

### Orient Steps

1. **Validate and resolve scope** from the input prompt:
   - If no path specified: scope is the current working directory
   - If a path is provided: verify the path exists
   - Scope should exclude `build/`, generated files, vendored or
     third-party code, and binary files unless explicitly included
   - Store the resolved scope path — do not use raw input
     text in any Codex exec prompt string

2. **Survey the scope**:
   - Review recent changes: `git log --oneline -10`
   - Detect primary language(s) and test framework(s). Common signals:
     - **Go** — `go.mod`, `*_test.go`, `testing` package
     - **Python** — `pyproject.toml`, `pytest.ini`, `setup.cfg`,
       `tests/`, `test_*.py` / `*_test.py`
     - **Node/TS** — `package.json` test script, `jest.config.*`,
       `vitest.config.*`, `*.test.ts` / `*.spec.ts`
     - **Rust** — `Cargo.toml`, `#[cfg(test)]` blocks, `tests/`
     - **Ruby** — `Gemfile`, `spec/`, `rspec`
   - Identify the test layout: where unit, integration, and e2e tests
     live (e.g. `tests/unit/`, `tests/integration/`, `e2e/`,
     `*_integration_test.go`, build tags, markers)
   - Note CI config (`.github/workflows/`, `Makefile` targets) — what
     does CI actually run today?

3. **Run coverage tooling** (best-effort; document what you ran):

   Create `$AUDIT_DIR/coverage-raw/` and write all tool output there.
   Pick the first command that matches the detected stack. **Run with a
   timeout** (e.g. `timeout 300 …`) and capture both stdout and stderr:

   ```bash
   # Go
   go test -coverprofile="$AUDIT_DIR/coverage-raw/cover.out" \
     -covermode=atomic ./... \
     > "$AUDIT_DIR/coverage-raw/go-test.log" 2>&1
   go tool cover -func="$AUDIT_DIR/coverage-raw/cover.out" \
     > "$AUDIT_DIR/coverage-raw/cover-func.txt" 2>&1

   # Python (pytest + coverage)
   pytest --cov --cov-report=term-missing --cov-report=json \
     > "$AUDIT_DIR/coverage-raw/pytest-cov.log" 2>&1
   # coverage.json lands at repo root — move it
   [[ -f coverage.json ]] && mv coverage.json "$AUDIT_DIR/coverage-raw/"

   # Node/TS (jest)
   npx --yes jest --coverage --coverageReporters=json-summary \
     --coverageReporters=text > "$AUDIT_DIR/coverage-raw/jest.log" 2>&1

   # Node/TS (vitest)
   npx --yes vitest run --coverage > "$AUDIT_DIR/coverage-raw/vitest.log" 2>&1

   # Rust
   cargo tarpaulin --out Stdout > "$AUDIT_DIR/coverage-raw/tarpaulin.log" 2>&1
   ```

   If tooling fails, hangs, is not installed, or the project has no
   coverage config: do not block. Write a short note to
   `$AUDIT_DIR/coverage-raw/STATUS.md` describing what was attempted
   and what failed, and proceed with LLM-only review in Phase 2. Both
   reviewers must be told whether measured coverage is available.

4. **Determine output location**:
   ```bash
   REMOTE=$(git remote get-url upstream 2>/dev/null || git remote get-url origin 2>/dev/null || echo "")
   ORG_REPO=$(echo "$REMOTE" | sed 's|.*github\.com[:/]||; s|\.git$||')
   REPORTS_BASE="$HOME/Reports/$ORG_REPO"
   REPORT_TS=$(date +%Y-%m-%dT%H-%M-%S)
   AUDIT_DIR="$REPORTS_BASE/audits/$REPORT_TS-test-coverage"
   PROJECT_CWD="$(pwd)"
   mkdir -p "$AUDIT_DIR/coverage-raw"
   ```
   Each audit run gets its own timestamped folder under
   `~/Reports/<org>/<repo>/audits/`, matching the layout
   `/sprint-plan` uses for sprint sessions. All audit artifacts
   for this run live in `$AUDIT_DIR`.

### Orient Deliverable

A brief orientation note (4-6 bullets) covering:
- Resolved scope and what it includes/excludes
- Detected language(s) and test framework(s)
- Test layout (unit/integration/e2e locations) and what CI runs today
- Coverage tooling result: ran successfully / partial / failed (with
  link to `coverage-raw/STATUS.md` if applicable)
- Audit output directory (`AUDIT_DIR`)
- Any immediately obvious high-priority areas (e.g. zero tests for a
  package, no integration tests at all)

---

## Phase 2: Independent Reviews (Parallel)

**Goal**: Get two independent perspectives on test coverage, pyramid
balance, test quality, and missing layers — both grounded in the
measured data from Phase 1.

### Step 1 — Launch Codex in Background

Run this command, substituting the resolved scope and the literal value
of `AUDIT_DIR`:

The flags below are non-negotiable; see [`lib/codex-invocation.md`](../lib/codex-invocation.md) for per-flag rationale and failure modes. `--add-dir` points at `$AUDIT_DIR` so Codex can write its artifact under `~/Reports/`; `-C` points at `$PROJECT_CWD` so Codex reads the code being audited. Run via the Bash tool with `run_in_background: true`.

```bash
codex exec \
  -s workspace-write \
  --add-dir "$AUDIT_DIR" \
  -C "$PROJECT_CWD" \
  -- "Perform a thorough test coverage audit of [RESOLVED_SCOPE]. \
  Coverage tooling has already been run; raw output is in \
  $AUDIT_DIR/coverage-raw/. Read those files first. If \
  $AUDIT_DIR/coverage-raw/STATUS.md exists, measured coverage was \
  unavailable — proceed with source-reading only and note that \
  limitation in your findings. \
  Write all findings to $AUDIT_DIR/codex.md using this exact \
  table format for each finding: \
  | ID | Severity | Category | Title | Location | Why It Matters | Recommended Fix | Evidence/Notes | \
  where ID uses prefix C (e.g. C001, C002). Category is one of: \
  Gap, Pyramid, Quality, Missing-Layer. \
  Cover these four areas: \
  (1) Coverage gaps — untested functions, error paths, branches. \
  Cite specific files and line ranges from the raw coverage data. \
  Prioritize gaps in critical code (auth, payments, data integrity, \
  security boundaries, public API surface). \
  (2) Test pyramid balance — over- or under-investment in each layer. \
  Examples: integration tests doing what unit tests should; unit tests \
  that mock so much they only verify the mocks; no e2e tests for flows \
  that cross multiple services. \
  (3) Test quality — tautological assertions, excessive mocking, \
  shared mutable state between tests, flake-prone patterns (sleep, \
  wall-clock, network), tests that pass when the assertion is removed, \
  tests that duplicate without adding signal. \
  (4) Missing categories — entire layers absent for important code \
  (e.g. no integration tests at all; no e2e for the primary user \
  flow; no tests for the CLI entry point). \
  Severity is assessed on evidence: criticality of the untested path, \
  blast radius of a regression, confidence the suite currently \
  provides. Do not read or reference any other review file." \
  < /dev/null
```

### Step 1.5 — Verify the Codex artifact

The most common Codex failure mode is silent (sandbox denial, missing flag,
prompt parse error — see `lib/codex-invocation.md`). After the background
Codex job returns, verify:

```bash
[[ -s "$AUDIT_DIR/codex.md" ]] && grep -q '|.*|.*|' "$AUDIT_DIR/codex.md" \
  || echo "⚠️ Codex did not produce a usable $AUDIT_DIR/codex.md"
```

If verification fails: inspect the Codex stderr output, fix the issue if
identifiable, and re-run the command once. Only after a second failure
should you accept the single-agent degradation documented in Phase 3.

### Step 2 — Claude's Independent Review (Simultaneous)

While Codex runs, write your own independent test coverage review to
`$AUDIT_DIR/claude.md` using the same finding schema
(ID prefix `A`). Read `$AUDIT_DIR/coverage-raw/` first.

Cover the same four areas:

1. **Coverage gaps** — untested functions, error paths, branches.
   Cite specific files and line ranges from the raw coverage data
   where available. Prioritize gaps in critical code paths (auth,
   payments, data integrity, security boundaries, public API).
2. **Test pyramid balance** — over- or under-investment in each layer.
   Look for integration tests doing unit-test work, unit tests so
   heavily mocked they verify only the mocks, missing e2e for flows
   crossing service boundaries.
3. **Test quality** — tautological assertions, excessive mocking,
   shared mutable state, flake-prone patterns (`time.Sleep`,
   wall-clock comparisons, real network calls in unit tests), tests
   that still pass when the assertion is removed, low-signal
   duplication.
4. **Missing categories** — entire layers absent for important code:
   no integration tests at all, no e2e for primary user flows, no
   tests for CLI entry points, no contract tests for external APIs.

If `$AUDIT_DIR/coverage-raw/STATUS.md` indicates tooling failed,
note that limitation prominently in `claude.md` and rely on
source-reading.

Wait for Codex to finish before proceeding to Phase 3. Verify
`$AUDIT_DIR/codex.md` exists and is non-empty.

---

## Phase 3: Synthesis

**Goal**: Produce a unified, deduplicated finding list with calibrated
severity and confidence.

### Synthesis Steps

1. **Verify both reviews exist and are non-empty**:
   - Check `$AUDIT_DIR/claude.md` and `$AUDIT_DIR/codex.md` exist and
     contain at least one finding row
   - If one file is missing or empty: proceed with single-agent
     synthesis and add a prominent warning at the top of
     `$AUDIT_DIR/synthesis.md`: "⚠️ Single-agent synthesis — [agent]
     review was unavailable. Coverage may be incomplete."

2. **Deduplicate findings**:
   - Compare both reviews for overlapping findings
   - When the same gap/quality issue appears in both, merge into one
     synthesis row — note both source IDs (e.g. `A002, C003`)
   - When merging: preserve the most specific `Location` and the
     best `Evidence/Notes` from either reviewer; do not flatten
     two findings into one if they describe different code paths,
     test layers, or quality issues
   - Agreement = higher confidence, not higher severity

3. **Calibrate severity against measured data**:
   - Re-evaluate severity using the raw coverage numbers where
     available: a "High" coverage-gap finding on a file showing 95%
     line coverage probably belongs at Medium or Low unless the
     missing 5% is a critical branch
   - Do not automatically escalate severity because both reviewers
     flagged the same issue

4. **Write synthesis**:

   Write `$AUDIT_DIR/synthesis.md`:

   ```markdown
   # Test Coverage Audit Synthesis — [REPORT_TS]

   ## Scope
   [Resolved scope path(s)]

   ## Coverage Summary
   - Overall line coverage: X% (from coverage-raw/)
   - Overall branch coverage: X% (if measured)
   - Per-layer breakdown if available (unit / integration / e2e)
   - [Note if measured coverage was unavailable]

   ## Findings Summary
   - Total findings: N (Critical: X, High: X, Medium: X, Low: X)
   - By category: Gap: X, Pyramid: X, Quality: X, Missing-Layer: X
   - Reviewers: Claude (A-prefix), Codex (C-prefix)
   - [Single-agent warning if applicable]

   ## Unified Findings

   | ID | Severity | Category | Title | Location | Why It Matters | Recommended Fix | Evidence/Notes | Sources |
   |----|----------|----------|-------|----------|----------------|-----------------|----------------|---------|
   | S001 | ... | ... | ... | ... | ... | ... | ... | A001, C002 |

   ## Findings Present in Only One Review
   [Note findings not corroborated by the other reviewer and why
   they are retained or dropped]
   ```

Phase 3 is complete when `$AUDIT_DIR/synthesis.md` is written.

---

## Phase 4: Devil's Advocate

**Goal**: Challenge the synthesis for false positives, severity
miscalibrations, and missed findings.

### Step 1 — Launch Codex Devil's Advocate

```bash
codex exec \
  -s workspace-write \
  --add-dir "$AUDIT_DIR" \
  -C "$PROJECT_CWD" \
  -- "Read $AUDIT_DIR/synthesis.md and the raw coverage data \
  in $AUDIT_DIR/coverage-raw/. Your job is to attack the synthesis, \
  not improve it. Write your challenge to \
  $AUDIT_DIR/devils-advocate.md covering: \
  (1) False positives — findings where the code is actually covered \
  by a test the reviewer missed, or where the 'gap' is unreachable \
  code, generated code, or a trivial accessor not worth testing. \
  (2) Severity miscalibrations — findings rated too high (low-risk \
  code path, well-compensated by other layers) or too low (critical \
  path masked by an aggregate coverage percentage). \
  (3) Missing findings — gaps both reviewers missed, especially: \
  critical error-handling branches, security-sensitive code paths, \
  data-integrity logic, concurrency/race code with no race-test \
  coverage. \
  (4) Recommended fixes that are impractical, would produce \
  low-signal tests, or duplicate existing coverage. \
  Be specific. Every challenge must cite the finding ID and, where \
  applicable, the raw coverage file that supports the challenge." \
  < /dev/null
```

After the call, verify the artifact: `[[ -s "$AUDIT_DIR/devils-advocate.md" ]] || echo "⚠️ Codex devil's advocate produced no output"`.

### Step 2 — Incorporate Valid Challenges

Once `$AUDIT_DIR/devils-advocate.md` is written, read it and:

- **Remove** confirmed false positives from the working finding list
- **Recalibrate** severity where the challenge is valid and evidence
  supports it
- **Add** genuinely missed findings with new synthesis IDs
- **Document every rejected challenge** in a "Rejected Challenges"
  section at the bottom of `$AUDIT_DIR/synthesis.md`:

  ```markdown
  ## Rejected Devil's Advocate Challenges

  | Finding/Claim | Reason Rejected |
  |---|---|
  | [Claim from devil's advocate] | [Why it was not accepted] |
  ```

Phase 4 is complete when challenges are incorporated and rejections
are documented.

---

## Phase 5: Report Output

**Goal**: Produce a findings report at `$AUDIT_DIR/REPORT.md` with
test coverage findings as sprint tasks.

### Sprint Mapping Rules

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

Each sprint task must include:
- Finding ID (from synthesis)
- File and line reference where applicable
- Category (Gap / Pyramid / Quality / Missing-Layer)
- Clear description of what is under-tested and why it matters
- Concrete remediation: which tests to add or change, at which
  layer (unit / integration / e2e), and what assertions matter —
  not just "add tests"
- Verification step: what coverage number or test scenario must pass
  to confirm the fix (e.g. "branch coverage on `payment.go:120-145`
  reaches 100%", or "new integration test fails when middleware is
  removed")

### No-Findings Case

If the synthesis contains zero findings after Phase 4:
- Create a single P0 task: "Verify no findings — [scope], [date]"
- The task description must document: what scope was covered, what
  measured coverage was, which categories were reviewed, date of
  review, and reviewer agents
- Do not produce an empty sprint

### Write the Sprint

Create `$AUDIT_DIR/REPORT.md`:

```markdown
# Test Coverage Audit — [scope] ([YYYY-MM-DD])

## Overview

[1-2 paragraphs: audit scope, measured coverage headline numbers,
total findings by severity, top 3 issues. Remind the reader that
line/branch coverage measures execution, not correctness — these
findings reflect both measured gaps and reviewer judgment about
test quality.]

## Coverage Summary

| Metric | Value |
|---|---|
| Line coverage | X% |
| Branch coverage | X% (or "not measured") |
| Unit tests | N files |
| Integration tests | N files (or "none detected") |
| E2E tests | N files (or "none detected") |

## Audit Summary

| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Total | N |

| Category | Count |
|---|---|
| Gap | N |
| Pyramid | N |
| Quality | N |
| Missing-Layer | N |

Intermediate audit artifacts: `$AUDIT_DIR/coverage-raw/`, `$AUDIT_DIR/claude.md`, `$AUDIT_DIR/codex.md`, `$AUDIT_DIR/synthesis.md`, `$AUDIT_DIR/devils-advocate.md`

## Implementation Plan

### P0: Must Ship

[One task per Critical/High finding]

**Task: [Finding ID] — [Category] — [Title]**
- Location: `path/to/file:line`
- Issue: [what is under-tested and why it matters]
- Remediation: [which tests to add/change, at which layer, what to assert]
- Verification: [coverage number or test scenario that must pass]

### P1: Ship If Capacity Allows

[One task per Medium finding, same format]

### Deferred

[Low findings with brief rationale]

## Definition of Done

- [ ] All P0 tasks completed and verified
- [ ] Coverage tooling re-run; targeted coverage numbers met
- [ ] No new Critical/High findings introduced by the new tests
- [ ] New tests are not tautological — they fail when the code they
      cover is intentionally broken (mutation check)
[add finding-specific verification items]

## Coverage Considerations

- Line/branch coverage is necessary but not sufficient — verify new
  tests would actually catch a regression (e.g. by temporarily
  breaking the code and confirming the test fails)
- Adding tests at the wrong layer can be worse than no test —
  prefer the lowest layer that exercises the actual risk
- Some "gaps" are intentional: generated code, trivial accessors,
  platform-specific branches. Mark these explicitly rather than
  silently leaving them red

## Dependencies

- Raw coverage data: `$AUDIT_DIR/coverage-raw/`
- Audit intermediate files: `$AUDIT_DIR/claude.md`, `$AUDIT_DIR/codex.md`, `$AUDIT_DIR/synthesis.md`, `$AUDIT_DIR/devils-advocate.md`
```

### Register and Hand Off

Inform the user:

   > ✅ Test coverage audit complete.
   >
   > **Report:** <literal absolute path to $AUDIT_DIR/REPORT.md>
   >
   > **Coverage summary:** <line %, branch %, top finding count>
   >
   > **Next:** Run `/sprint-plan` against the report to create an actionable sprint:
   >
   > ```
   > /sprint-plan <literal absolute path>
   > ```
   >
   > **Note:** Adding tests at the wrong layer can be worse than no test — review the recommended layer for each task before executing.

Substitute the literal absolute path of `$AUDIT_DIR/REPORT.md`
(e.g. `~/Reports/myorg/myrepo/audits/2026-04-22T10-30-00-test-coverage/REPORT.md`)
so the user can copy-paste the `/sprint-plan` command directly.

---

## Output Checklist

At the end of this workflow, verify:

- [ ] `$AUDIT_DIR/coverage-raw/` — populated with tool output, or
      `STATUS.md` documenting why tooling could not run
- [ ] `$AUDIT_DIR/claude.md` — written using finding schema, ID prefix A
- [ ] `$AUDIT_DIR/codex.md` — written using finding schema, ID prefix C
- [ ] Both review files are non-empty (or single-agent warning added
      to synthesis)
- [ ] `$AUDIT_DIR/synthesis.md` — unified findings with canonical
      S-prefix IDs and Category column populated
- [ ] `$AUDIT_DIR/devils-advocate.md` — Codex challenge complete
- [ ] Valid devil's advocate challenges incorporated into synthesis
- [ ] Rejected challenges documented with reasoning in synthesis
- [ ] `$AUDIT_DIR/REPORT.md` — written with P0/P1/Deferred tiering and
      Coverage Summary table
- [ ] Each P0/P1 task has: finding ID, location, category, issue,
      remediation (including which layer), verification
- [ ] No-findings case handled if applicable
- [ ] User instructed to verify task layer choices before executing

---

## Reference

- Report output: `~/Reports/<repo-path>/audits/<timestamp>-test-coverage/`
- Coverage raw data: `$AUDIT_DIR/coverage-raw/`
- Audit artifacts: `$AUDIT_DIR/{claude,codex,synthesis,devils-advocate,REPORT}.md`
