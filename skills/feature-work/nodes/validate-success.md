# Node: validate-success

Full test suite per repo + Success Criteria walk. Auto-decides — unmet non-test criteria ship with a note; only a hard, unresolvable test failure on a single sub-issue stops the run.

## Inputs

- `repos`, `worktree_paths`, `context_dir`, `implement_results`, `active_subissue_id` from walker state

```bash
STATE="<path>"
REPOS=$(scripts/walk.sh get --state "$STATE" --key repos)
WORKTREE_PATHS=$(scripts/walk.sh get --state "$STATE" --key worktree_paths)
```

For the multi-sub-issue walk, `worktree_paths` covers the active sub-issue's repos (rotated per iteration by `implement`'s loop). validate-success treats it transparently — same code path as the single-sub-issue case.

## Steps

### 1. Run the full test suite per repo

The skill is cwd-independent. **Run every test command inside the resolved per-repo worktree** via `worktree_paths`. Never assume cwd is in any of the manifest's repos.

**Iterate the active-set's keys** (`keys(worktree_paths)`), not the full `repos` manifest. For a single sub-issue these are the same set; for the walk's per-sub-issue rotation, `worktree_paths` is the subset of repos the active sub-issue actually touches. Iterating `repos` would test against worktrees the active sub-issue doesn't touch.

```bash
TEST_LOG_DIR="${STATE%.walk-state.json}.test-logs"
mkdir -p "$TEST_LOG_DIR"

for ORG_REPO in $(echo "$WORKTREE_PATHS" | jq -r 'keys[]'); do
  WT=$(echo "$WORKTREE_PATHS" | jq -r ".[\"$ORG_REPO\"]")
  LOG="$TEST_LOG_DIR/$(echo "$ORG_REPO" | tr / -).log"

  # Detect the right command per worktree from CLAUDE.md / AGENTS.md /
  # manifest heuristics (same detection as implement.md's targeted-tests block).
  #   Go:     ( cd "$WT" && go test ./... )
  #   Python: ( cd "$WT" && pytest ) or `make test` if the Makefile defines it
  #   Node:   ( cd "$WT" && npm test ) or yarn/pnpm equivalent

  ( cd "$WT" && <test cmd> ) > "$LOG" 2>&1
done
```

Surface failures immediately.

### 2. Walk Success Criteria — auto-decide, don't prompt

For each criterion in the sub-issue body's Success Criteria:

- **Met** → confirm with a brief justification (e.g., "tests pass for the new behavior", "docs updated in `README.md`").
- **Not yet met** → **don't ask the user.** Try to satisfy it as part of the work (usually a small gap). If it can't be met this run because it's a **deferral** (subjective/visual, device, secret, App Store, judgment call), record it as deferred (it joins the punch list) and **proceed** — `commit-push` notes it in the commit body under `Deferred:` / `Known incomplete:`. The run keeps moving.

The only hard stop is a **test failure the agent can't resolve** (step 1):
- **Multi-sub-issue walk:** the per-sub-issue loop records the failing sub-issue into `feature_walk_results` and moves to the next — the walk never halts on one.
- **Single sub-issue:** there's no next sub-issue, so a hard, unresolvable test failure is a genuine wall — route to `terminal` via `blocked` with the failing output, so the user can step in.

Don't route to `blocked` for unmet *non-test* criteria or deferrals — those ship with a note, not a halt.

### 3. Persist results

**Single sub-issue:** singular fields.

```bash
scripts/walk.sh set --state "$STATE" --key tests_passed     --value "<true|false>"
scripts/walk.sh set --state "$STATE" --key criteria_results --value "<JSON: per-criterion met/ship/defer>"
```

**Multi-sub-issue walk:** namespace under the active sub-issue ref. Read existing `feature_walk_results`, merge in the active sub-issue's slice, write back:

```bash
ACTIVE=$(scripts/walk.sh get --state "$STATE" --key active_subissue_id)
EXISTING=$(scripts/walk.sh get --state "$STATE" --key feature_walk_results)
UPDATED=$(echo "$EXISTING" | jq --arg id "$ACTIVE" \
  --argjson tests "<true|false>" --argjson crit "<JSON>" \
  '.[$id] = {tests: $tests, criteria: $crit}')
scripts/walk.sh set --state "$STATE" --key feature_walk_results --value "$UPDATED"
```

`summarize` reads the appropriate shape per path.

## Outputs

- Test logs per repo
- `tests_passed`, `criteria_results` (single) or merged `feature_walk_results` (walk) in walker state

## Outgoing edges

- **`criteria_satisfied`** → `commit-push`. Tests pass; criteria met, noted-incomplete, or deferred. This is the normal path — take it autonomously.
- **`blocked`** → `terminal`. A hard, unresolvable test failure on a single sub-issue. Genuine wall — surface the failing output for the user.

Record exactly one:

```bash
# Tests pass — proceed to commit + push (the normal, autonomous path):
scripts/walk.sh transition --state "$STATE" --from validate_success --to commit_push --condition criteria_satisfied

# Hard test failure the agent can't resolve (single sub-issue only):
scripts/walk.sh transition --state "$STATE" --from validate_success --to terminal --condition blocked
```

## Notes

- **Tests fail → still walk Success Criteria.** Failing tests are themselves a Success Criterion failure (typically). Surface both clearly.
- **A deferral isn't a test failure.** Subjective/device/secret/App-Store/judgment-call gaps ship with a note and join the punch list; they never route to `blocked`.
- **A hard test failure is the one real wall.** Try to fix it first (that's the job). Only if it's genuinely unresolvable do you stop — and only on a single sub-issue; in the walk, record it and move on. Never commit code over a known-failing test on the affected sub-issue.
