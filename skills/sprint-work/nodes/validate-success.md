# Node: validate-success

Phase 9: full test suite per repo + Success Criteria walk. If any criteria aren't met, ask the user how to proceed inline.

## Inputs

- `path_mode`, `repos`, `worktree_paths`, `context_dir`, `implement_results` from walker state

```bash
STATE="<path>"
PATH_MODE=$(scripts/walk.sh get --state "$STATE" --key path_mode)
REPOS=$(scripts/walk.sh get --state "$STATE" --key repos)
WORKTREE_PATHS=$(scripts/walk.sh get --state "$STATE" --key worktree_paths)
```

For `linear-walk`, `worktree_paths` is the **active issue's** map (rotated per iteration by `implement`'s loop). validate-success treats it transparently — same code path as sprintmd.

## Steps

### 1. Run the full test suite per repo

The skill is cwd-independent. **Run every test command inside the resolved per-repo worktree** via `worktree_paths`. Never assume cwd is in any of the manifest's repos.

**Iterate the active-set's keys** (`keys(worktree_paths)`), not the full `repos` manifest. For sprintmd / linear-issue paths these are the same set; for linear-walk's per-issue active-set rotation, `worktree_paths` is the subset of repos the active issue actually touches. Iterating `repos` would test against worktrees that don't exist (issue X doesn't touch repo Y, but repo Y is in the milestone manifest).

```bash
TEST_LOG_DIR="${STATE%.walk-state.json}.test-logs"
mkdir -p "$TEST_LOG_DIR"

for ORG_REPO in $(echo "$WORKTREE_PATHS" | jq -r 'keys[]'); do
  WT=$(echo "$WORKTREE_PATHS" | jq -r ".[\"$ORG_REPO\"]")
  LOG="$TEST_LOG_DIR/$(echo "$ORG_REPO" | tr / -).log"

  # Detect the right command per worktree from CLAUDE.md / AGENTS.md /
  # manifest heuristics (same detection as `implement.md`'s targeted-tests
  # block). Detection is cheap (read one or two project files); no need
  # to cache across runs.
  #
  # Examples:
  #   Go:     ( cd "$WT" && go test ./... )
  #   Python: ( cd "$WT" && pytest ) or `make test` if Makefile defines it
  #   Node:   ( cd "$WT" && npm test ) or yarn/pnpm equivalent

  ( cd "$WT" && <test cmd> ) > "$LOG" 2>&1
done
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

The persistence shape depends on path mode. linear-walk runs validate-success per issue inside implement's loop; each iteration would otherwise overwrite the prior issue's results, leaving summarize with only the last issue's data.

**sprintmd / linear-issue (one branch unit):** singular fields.

```bash
scripts/walk.sh set --state "$STATE" --key tests_passed     --value "<true|false>"
scripts/walk.sh set --state "$STATE" --key criteria_results --value "<JSON: per-criterion met/ship/defer>"
```

**linear-walk:** namespace under the active issue ID. Read existing `linear_walk_results`, merge in the active issue's slice, write back:

```bash
ACTIVE_ISSUE=$(scripts/walk.sh get --state "$STATE" --key active_issue_id)
EXISTING=$(scripts/walk.sh get --state "$STATE" --key linear_walk_results)
# Build updated map: linear_walk_results.<issue_id>.tests = <true|false>,
#                    linear_walk_results.<issue_id>.criteria = <JSON>
UPDATED=$(echo "$EXISTING" | jq --arg id "$ACTIVE_ISSUE" \
  --argjson tests "<true|false>" --argjson crit "<JSON>" \
  '.[$id] = {tests: $tests, criteria: $crit}')
scripts/walk.sh set --state "$STATE" --key linear_walk_results --value "$UPDATED"
```

`summarize` reads the appropriate shape per path mode.

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
