# Node: validate-success

Phase 9: full test suite per repo + Success Criteria walk. Auto-decides — unmet non-test criteria ship with a note; only a hard, unresolvable test failure on a single branch unit stops the run.

## Inputs

- `path_mode`, `repos`, `worktree_paths`, `context_dir`, `implement_results` from walker state

```bash
STATE="<path>"
PATH_MODE=$(scripts/walk.sh get --state "$STATE" --key path_mode)
REPOS=$(scripts/walk.sh get --state "$STATE" --key repos)
WORKTREE_PATHS=$(scripts/walk.sh get --state "$STATE" --key worktree_paths)
```

For `forgejo-walk`, `worktree_paths` is the **active issue's** map (rotated per iteration by `implement`'s loop). validate-success treats it transparently — same code path as sprintmd.

## Steps

### 1. Run the full test suite per repo

The skill is cwd-independent. **Run every test command inside the resolved per-repo worktree** via `worktree_paths`. Never assume cwd is in any of the manifest's repos.

**Iterate the active-set's keys** (`keys(worktree_paths)`), not the full `repos` manifest. For sprintmd / forgejo-issue paths these are the same set; for forgejo-walk's per-issue active-set rotation, `worktree_paths` is the subset of repos the active issue actually touches. Iterating `repos` would test against worktrees that don't exist (issue X doesn't touch repo Y, but repo Y is in the milestone manifest).

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

### 2. Walk Success Criteria — auto-decide, don't prompt

For each criterion (Forgejo: issue body's Success Criteria; SPRINT.md: Definition of Done):

- **Met** → confirm with a brief justification (e.g., "tests pass for the new behavior", "docs updated in `README.md`").
- **Not yet met** → **don't ask the user.** Try to satisfy it as part of the work (it's usually a small gap). If it genuinely can't be met this run (e.g., it depends on something out of scope), record it and **proceed anyway** — `commit-push` notes it in the commit body under `Known incomplete:`. The run keeps moving.

The only hard stop is a **test failure the agent can't resolve** (step 1):
- **forgejo-walk:** the per-issue loop records the failing issue into `forgejo_walk_results` and moves to the next issue — the walk never halts on one issue.
- **forgejo-issue / sprintmd (single branch unit):** there's no next issue, so a hard, unresolvable test failure is a genuine wall — route to `terminal` via `blocked` with the failing test output, so the user can step in.

Don't route to `blocked` for unmet *non-test* criteria — those ship with a note, not a halt.

### 3. Persist results

The persistence shape depends on path mode. forgejo-walk runs validate-success per issue inside implement's loop; each iteration would otherwise overwrite the prior issue's results, leaving summarize with only the last issue's data.

**sprintmd / forgejo-issue (one branch unit):** singular fields.

```bash
scripts/walk.sh set --state "$STATE" --key tests_passed     --value "<true|false>"
scripts/walk.sh set --state "$STATE" --key criteria_results --value "<JSON: per-criterion met/ship/defer>"
```

**forgejo-walk:** namespace under the active issue ref. Read existing `forgejo_walk_results`, merge in the active issue's slice, write back:

```bash
ACTIVE_ISSUE=$(scripts/walk.sh get --state "$STATE" --key active_issue_id)
EXISTING=$(scripts/walk.sh get --state "$STATE" --key forgejo_walk_results)
# Build updated map: forgejo_walk_results.<owner/repo#n>.tests = <true|false>,
#                    forgejo_walk_results.<owner/repo#n>.criteria = <JSON>
UPDATED=$(echo "$EXISTING" | jq --arg id "$ACTIVE_ISSUE" \
  --argjson tests "<true|false>" --argjson crit "<JSON>" \
  '.[$id] = {tests: $tests, criteria: $crit}')
scripts/walk.sh set --state "$STATE" --key forgejo_walk_results --value "$UPDATED"
```

`summarize` reads the appropriate shape per path mode.

## Outputs

- Test logs per repo
- `tests_passed`, `criteria_results` in walker state

## Outgoing edges

- **`criteria_satisfied`** → `commit-push`. Tests pass; criteria met or noted-incomplete. This is the normal path — take it autonomously.
- **`blocked`** → `terminal`. A hard, unresolvable test failure on a single branch unit (forgejo-issue / sprintmd). Genuine wall — surface the failing output for the user.

Record exactly one:

```bash
# Tests pass — proceed to commit + push (the normal, autonomous path):
scripts/walk.sh transition --state "$STATE" --from validate_success --to commit_push --condition criteria_satisfied

# Hard test failure the agent can't resolve (single branch unit only):
scripts/walk.sh transition --state "$STATE" --from validate_success --to terminal --condition blocked
```

## Notes

- **Tests fail → still walk Success Criteria.** Failing tests are themselves a Success Criterion failure (typically). Surface both clearly.
- **"Ship without" isn't always wrong.** Some criteria are aspirational ("perf regression suite green"); the user may have valid reasons to ship and address later.
- **A hard test failure is the one real wall.** Try to fix it first (that's the job). Only if it's genuinely unresolvable do you stop — and only on a single branch unit; in a forgejo-walk, record it and move to the next issue. Never commit code over a known-failing test on the affected issue.
