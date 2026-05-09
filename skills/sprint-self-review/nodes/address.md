# Node: address

The work-doing node. For each new finding in this iteration's REVIEW.md, dedup against the ledger, locate the right worktree(s) from the manifest, apply the fix there, verify it (tests/lint in that worktree), and update the ledger. Findings the agent can't resolve get marked for escalation and routed via `decide`.

## Inputs

- `$ITER_DIR/REVIEW.md` (this iteration's findings, each tagged with `Repo:`)
- `$FINDINGS` (rolling per-sprint ledger across all runs)
- `worktree_paths` (from walker state — maps each repo to its worktree path)
- The local checkouts (one per repo)

```bash
# The walker passes $STATE on every transition; derive everything else
# from it.
SESSION_DIR=$(dirname "$(dirname "$STATE")")
ITER_DIR=$(scripts/walk.sh get --state "$STATE" --key iter_dir)
FINDINGS=$(scripts/walk.sh get --state "$STATE" --key findings_path)
WORKTREE_PATHS=$(scripts/walk.sh get --state "$STATE" --key worktree_paths)
```

## Test/lint detection per worktree

Detect once per worktree per session, cache as `test_lint_<org>-<repo>` in walker state. Order:

1. **Project doc** — if the worktree has `CLAUDE.md` or `AGENTS.md`, read it. Look for canonical commands (most repos document them).
2. **Manifest heuristics** — fall back to:
   - `go.mod` → `go test ./...`, `go vet ./...`, `golangci-lint run` (if `.golangci.yml` exists or the binary is on PATH)
   - `package.json` → `npm test`, `npm run lint` (only if those scripts exist)
   - `pyproject.toml` / `pytest.ini` → `pytest`, `ruff check`, `mypy` (if configured)
   - `Makefile` with `test:` / `lint:` targets → `make test`, `make lint`
3. **No detection** — surface to the user once per worktree, ask for the canonical command, cache the answer.

## Per-finding loop

For each new finding (SR-NNN) in this iteration's REVIEW.md, in REVIEW.md order:

### 1. Dedup against the ledger

Look for existing ledger entries (LR-NNN) where:

- `Repo:` matches (single-repo finding compares to single-repo ledger entries; cross-repo finding compares to cross-repo entries with the same repo set)
- `File:Line` matches exactly (for cross-repo findings, both file:line pairs match)
- Issue text Jaccard similarity > ~0.6 over normalized tokens (lowercase, drop punctuation)

Outcomes:

- **Match found, ledger entry was `fixed`** → regression. Update the ledger entry: status to `*regression after iter-<prior>*`, append current iter to `Seen in:`, reopen checkbox. Process this finding (apply a fresh fix attempt) but flag it as a regression in ADDRESSED.md.
- **Match found, ledger entry was `won't-fix` / `deferred` / `skipped`** → user already decided. Append current iter to `Seen in:`, leave decision in place, skip processing.
- **Match found, ledger entry was `escalated, awaiting user`** → still awaiting. Append current iter to `Seen in:`, route this finding to escalation again via decide → escalate.
- **Ambiguous match** (two or more candidates score similarly) → mark this finding as `pending-dedup-check`, route to escalation. Don't process until the user resolves.
- **No match** → new ledger entry, next `LR-NNN` ID, status `*open*`, populate `Repo:` + `File:Line:` + remaining fields from the SR-NNN.

### 2. Locate the worktree(s) for this finding

```bash
# Single-repo finding:
WT=$(echo "$WORKTREE_PATHS" | jq -r ".[\"$REPO\"]")

# Cross-repo finding (multiple repos in Repo:):
# Resolve each separately. The fix may need to touch both worktrees in one
# atomic step (verify=run tests in both before commit-or-revert).
```

### 3. Apply the fix

For findings the agent can confidently fix:

- Use `Edit` (preferred) or `Write` to apply the change inside the appropriate worktree(s). Edits are scoped to file paths under `$WT`.
- For findings requiring user judgment (ambiguous diagnosis, design choice, can't determine root cause from the diff alone): mark the ledger entry status as `*escalated, awaiting user*` and skip applying. Decide will route to escalate.

For **cross-repo findings**: the fix may require coordinated edits in two worktrees (e.g., rename a function in repo B and update its caller in repo A). Apply both edits before running tests anywhere — partial application leaves both repos broken. If the second edit can't be made cleanly, revert the first via `git -C "$WT" checkout -- <files>` and escalate the finding as `*escalated: cross-repo fix could not be applied atomically*`.

### 4. Verify the fix

After applying:

- Run the detected test command(s) **inside each affected worktree**, scoped to the touched files when possible. Use `( cd "$WT" && <test cmd> )` so cwd stays correct.
- Run the linter on touched files in each affected worktree.

For **cross-repo fixes**, the verification has three possible outcomes per worktree:

| Per-worktree outcome | Per-worktree call |
|---|---|
| Tests pass + lint clean | ✅ pass |
| Tests fail or lint flags an issue | ❌ fail |
| Tests can't be detected/run (no `CLAUDE.md` / `AGENTS.md` / manifest match, and the user can't be prompted) | ⚠ inconclusive |

Aggregation rule for the cross-repo finding as a whole:

- **All worktrees ✅** → commit in every affected worktree.
- **Any worktree ❌** → revert **every** affected worktree (preserve no half-applied state), mark the finding `*escalated: fix failed verification in <repo>*`, continue.
- **Any worktree ⚠ (with no ❌)** → **revert all affected worktrees** (`git -C "$WT" checkout -- <files>`) and mark the finding `*escalated: cannot verify cross-repo fix in <repo>*`. The user resolves manually and re-runs.

  **Why revert, not "leave in place":** the prior version of this rule said "leave the user's workspace with proposed edits in place" so the user could verify manually. That created a worse problem: `compute-diff` reviews `REMOTE_BASE..HEAD` (committed work only), so the uncommitted edits *disappear from the next iteration's review* while the worktree stays dirty. Reviewers re-flag the finding as if it weren't fixed, the user sees confusing inconsistency. Reverting keeps the working tree clean and the finding visible-as-open in the ledger; the user takes over with a coherent state.

For single-repo fixes the rule is the same shape: pass → commit; fail → revert + escalate; inconclusive → revert + escalate (uniform "don't leave dirty state" principle).

### 5. Commit per worktree on success

If verification passes:

```bash
( cd "$WT" && git add <touched files> && \
  git commit -m "fix: <issue summary>" )
```

**Don't reference internal LR/SR/CR/CX IDs in the commit message.** Per the ID Suppression Rule (`docs/sprints/README.md`), internal review IDs live only in `findings.md` and `ADDRESSED.md`. The commit message should be human-readable and Conventional Commit shaped, with no internal-ID prefix.

Traceability from commit → finding lives in `ADDRESSED.md` (which records `SR-NNN → LR-NNN` and the resulting commit SHA). Don't smuggle the LR ID into the commit subject as a workaround.

For cross-repo fixes, commit in each affected worktree (one commit per worktree, each with its own scoped summary). Record all SHAs in the ledger entry's `Commits:` field as `<org>/<repo>:abc1234, <org>/<repo2>:def5678`. Set status to `*fixed in iter-<N>*`.

### Comment Hygiene Rule

**Code comments rewritten or added during fixes: terse, humanlike, no AI tells.** This skill authors code via Edit/Write — same enforcement responsibility as `/sprint-work/implement.md`. Per the Comment Hygiene Rule in `docs/sprints/README.md`:

- One line by default; multi-line only when *why* genuinely needs more.
- Don't restate the code; well-named identifiers handle the *what*.
- Forbidden openings: `This function ...`, `We refactor ...`, `Note that ...`, `Importantly ...`.
- No multi-paragraph explanations of obvious code.

If a fix adds a comment longer than one line, ask whether the *why* is genuinely non-obvious — most often, the answer is "no, delete it."

### 6. Skip auto-fixes for these classes

Even when "addressable" by the agent, route to escalation instead:

- Test removals or weakenings (might be intentional)
- Public API changes (especially cross-repo: a callee signature change ripples)
- Configuration / schema changes
- Anything the finding's Suggestion field marks with words like "consider", "discuss", "may want to" — those flag user judgment
- Cross-repo findings where the fix would require renaming a public symbol

### 7. Write `$ITER_DIR/ADDRESSED.md`

Audit trail. One entry per finding processed in this iteration:

```markdown
- **SR007 → LR042** — fixed
  - Repo: org/repo-a
  - File:Line: pkg/foo/bar.go:88
  - Action: added nil guard before deref
  - Verification: `( cd <wt-a> && go test ./pkg/foo/... )` passed
  - Commit: org/repo-a:abc1234

- **SR011 → LR043** — fixed (cross-repo)
  - Repo: org/repo-a + org/repo-b
  - File:Line: org/repo-a:pkg/api.go:88 ; org/repo-b:cmd/cli/main.go:120
  - Action: widened caller signature to int64 to match callee
  - Verification: tests passed in both worktrees
  - Commits: org/repo-a:def5678, org/repo-b:ghi9012
```

Statuses to record: `fixed`, `escalated`, `dedup-pending`, `regression-detected`, `skipped (user-prior-decision)`.

### 8. Update `$FINDINGS`

The merged ledger state is the source of truth. `decide` reads it next.

## Outputs

- `$ITER_DIR/ADDRESSED.md`
- Updated `$FINDINGS` (new entries appended, existing entries updated)
- New commits in the relevant worktrees (one per fix per worktree)

## Outgoing edges

- → `decide` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from address --to decide
```

## Failure modes

- Fix attempt corrupts a working tree (partial Edit, syntax error): revert via `git -C "$WT" checkout -- <files>`, mark the finding `*escalated: fix failed verification*`, continue processing the rest.
- Test/lint command not detected and user can't be prompted: treat verification as inconclusive and mark the finding `*escalated: cannot verify fix*`. Do not commit unverified fixes.
- Multiple fixes touch the same lines and conflict: process serially, re-evaluate after each commit; if the second fix can no longer be applied cleanly, escalate it.
- Cross-repo fix succeeds in one worktree but fails verification in the other: revert both worktrees fully (you can't have one repo's commit reference a fix that doesn't exist in the other), escalate the finding.
