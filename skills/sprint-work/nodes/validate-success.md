# Node: validate-success

Phase 9: full test suite per repo + Success Criteria walk. If any criteria aren't met, ask the user how to proceed inline.

## Inputs

- `path_mode`, `repos`, `context_dir`, `implement_results` from walker state

```bash
STATE="<path>"
PATH_MODE=$(scripts/walk.sh get --state "$STATE" --key path_mode)
REPOS=$(scripts/walk.sh get --state "$STATE" --key repos)
```

## Steps

### 1. Run the full test suite per repo

For each repo in `$REPOS`:

```bash
# Go: go test ./...
# Python: pytest (or make test if Makefile defines it)
# Node: npm test (or yarn / pnpm equivalent)
```

Capture pass/fail. Save full output to a per-repo log:

```bash
TEST_LOG_DIR="${STATE%.walk-state.json}.test-logs"
mkdir -p "$TEST_LOG_DIR"
# write per-repo log files
```

Surface failures immediately.

### 2. Walk Success Criteria

For each criterion (Linear: issue body's Success Criteria; SPRINT.md: Definition of Done):

- **Confirm met.** Brief justification (e.g., "tests pass for the new behavior", "docs updated in `README.md`").
- **Or surface as not-yet-met** and AskUserQuestion per criterion:
  > Criterion `<text>` is not met. How would you like to proceed?
  >
  > 1. **Ship without** — open the PR anyway; flag in PR body
  > 2. **Fix before PR** — pause; surface what's missing; bail to terminal
  > 3. **Defer** — note in PR body as known-incomplete; open a follow-up issue (suggest `linear issue create` after)

For "Fix before PR", route the skill to `terminal` via `user_blocked` after recording state.

### 3. Persist results

```bash
scripts/walk.sh set --state "$STATE" --key tests_passed     --value "<true|false>"
scripts/walk.sh set --state "$STATE" --key criteria_results --value "<JSON: per-criterion met/ship/defer>"
```

## Outputs

- Test logs per repo
- `tests_passed`, `criteria_results` in walker state

## Outgoing edges

- **`criteria_satisfied`** → `open-prs`. All criteria met (or user picked ship/defer for unmet ones).
- **`user_blocked`** → `terminal`. User picked "fix before PR" on at least one criterion.

Record exactly one:

```bash
# All criteria handled — proceed to PR open:
scripts/walk.sh transition --state "$STATE" --from validate_success --to open_prs --condition criteria_satisfied

# User wants to fix before PR:
scripts/walk.sh transition --state "$STATE" --from validate_success --to terminal --condition user_blocked
```

## Notes

- **Tests fail → still walk Success Criteria.** Failing tests are themselves a Success Criterion failure (typically). Surface both clearly.
- **"Ship without" isn't always wrong.** Some criteria are aspirational ("perf regression suite green"); the user may have valid reasons to ship and address later.
- **Don't ship if any test is hard-failing without explicit user opt-in.** Tests can be flaky, but a real failure should not silently slip past `validate-success`.
