# Node: verify

Does the branch deliver the plan? Full test suite, lint or vet if the repo has one, then walk the Tests table and Scope In. Anything unmet is the user's call, not something to paper over.

## Who does this

Split. The orchestrator runs the test suite (step 1), asks the user about gaps (step 5), and does any fix-now edits. Steps 2 to 4, the judgment about whether the branch delivers the plan, run in one Agent call with `subagent_type: verifier`, briefed per `lib/agent-roles.md` § The brief: steps 2 to 4 verbatim as the contract, absolute paths to `PLAN.md`, `build-verify.log`, and `$WT` (read-only), the base ref, and the output contract: write `$PLAN_DIR/verify.md` with one section per check (each item met / not met / partly met with file:line or commit evidence) and a `## Gaps` list (kind, text), and nothing else. Fingerprint `git -C "$WT" status --porcelain` and `HEAD` before and after; a mismatch discards `verify.md`. Verify the file has all three sections and a Gaps list before reading it. The orchestrator wrote the code and would see every Scope In bullet as delivered. After fix-now edits, re-run the suite and re-delegate steps 2 to 4 rather than re-judging by hand.

## Inputs

- `worktree`, `plan_path`, `test_cmd_full`, `base_ref`, `plan_dir` from walker state
- PLAN.md Tests and Scope sections

```bash
STATE="$PLAN_DIR/.walk-state.build.json"
WT=$(scripts/walk.sh get --state "$STATE" --key worktree)
```

## Steps

1. **Full tests, lint, build.** Whatever the repo's `CLAUDE.md` or `Makefile` names as the standard gate. Typical Go: `go build ./... && go vet ./... && go test ./...`, plus `golangci-lint run` if configured. Capture everything:
   ```bash
   ( cd "$WT" && <test_cmd_full> ) > "$PLAN_DIR/build-verify.log" 2>&1
   ```
   Surface failures verbatim. Pre-existing failures on the base (confirm by checking whether the failing test touches anything in `git diff --name-only $BASE_REF...HEAD`) are noted, not fixed.

2. **Tests table walk.** For each row in PLAN.md Tests: does the test exist by that name (or an evident rename), and did it pass in step 1? Missing → note it.

3. **Scope In walk.** For each bullet: point at the commit or diff hunk that delivers it. Can't → note it.

4. **Scope Out check.** `git diff --stat $BASE_REF...HEAD`. Any file touched that the plan's Files table doesn't list is a scope question. Say which and why it was touched.

5. **Decide.** Everything green and delivered → `verified`, no prompt. Otherwise show the gaps as a short list and ask with `AskUserQuestion`:
   1. **Fix now**: go back and address them in this run (stay in this node, do the work, re-run step 1, re-evaluate).
   2. **Ship with gaps**: proceed. Each gap becomes a "Not in this PR" line in the PR body and a Follow-ups entry in PLAN.md.
   3. **Stop**: leave the branch as is. Append `<date> pr-build: stopped at verify (<gaps, one clause>)` to PLAN.md Log, then route `user_blocked`.

   A hard test failure caused by this branch can't be shipped with. Only fix now or stop.

6. **Persist:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key tests_passed --value "<true|false>"
   scripts/walk.sh set --state "$STATE" --key gaps         --value "<JSON list of {kind: test|scope|file, text}, possibly empty>"
   ```

## Outputs

- `$PLAN_DIR/build-verify.log`, `$PLAN_DIR/verify.md`
- `tests_passed`, `gaps` in walker state
- PLAN.md Follow-ups appended for shipped-with gaps

## Outgoing edges

- **`verified`** → `sweep`
- **`user_blocked`** → `terminal`

```bash
scripts/walk.sh transition --state "$STATE" --from verify --to sweep    --condition verified
scripts/walk.sh transition --state "$STATE" --from verify --to terminal --condition user_blocked
```

## Notes

- **Fix-now edits are commits too.** Same rules as implement: targeted tests, hygiene check, explicit paths, Conventional Commit. A fix-now round that touches one task's files can use that task's scope in the subject.
- **Don't run the test suite twice for no reason.** If fix-now changed nothing testable (a doc line), skip the re-run and say so.
