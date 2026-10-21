# Node: init

Resolve the review target (a PR, or the local branch state), decide whether it's ours or someone else's, set up paths, initialize the walker state file.

## Inputs

- `$ARGUMENTS`: optional PR number or URL, optional `--base <ref>`, optional `--own` / `--external`, optional `--canon`
- Current branch and working tree (used for target detection)

## Steps

1. **Session model.** This phase runs on Opus. Read the current session with the `get_session` tool (session `self`) and check `model`. A `model` that doesn't start with `claude-opus-` → stop before creating any state. Name the model the session is on and tell the user to switch to Opus in the model picker and re-run. A skill can read its session's model but not change it. Planning (`/pr-plan`) may run on any model. This phase doesn't.

2. **Parse arguments.** Extract an optional PR identifier (number or URL, trailing number for URLs), `--base <ref>`, `--own` or `--external` (both → bail), and `--canon`.

3. **Resolve the mode.** Deterministic, never silent:

   - **Explicit PR identifier** → `MODE=pr`. The user pointed at a PR, review it as pushed. Also the escape hatch when local is ahead but the pushed state is what should be reviewed.
   - **No PR identifier** → inspect the current branch:
     ```bash
     PR_JSON=$(gh pr view --json number,headRefOid,baseRefName,headRefName,author 2>/dev/null) || PR_JSON=""
     LOCAL_HEAD=$(git rev-parse HEAD)
     DIRTY=$(git status --porcelain)
     ```
     - No open PR → `MODE=local`.
     - Open PR, but `LOCAL_HEAD` differs from `headRefOid` **or** `DIRTY` is non-empty → `MODE=local`. What's in front of the user is the thing to review.
     - Open PR, in sync, clean → `MODE=pr`.

4. **PR mode: verify the PR exists** and fetch `author.login` and `headRefName`. Not found → "PR #N not found, or you don't have access."

5. **Resolve ownership.** Compare the PR author to us:
   ```bash
   ME=$(gh api user -q .login)
   AUTHOR=$(gh pr view "$PR_NUMBER" --json author -q .author.login)
   ```
   - `AUTHOR = ME` → `OWNERSHIP=own`.
   - Otherwise (including bots) → `OWNERSHIP=external`.
   - `--own` / `--external` override the detection. Say so when they do.
   - Local mode is always `own`. There's no PR author to compare.

   Ownership changes the tail of the run, not the review itself: own-mode intent includes the approved plan when there is one, and the next-action menu offers `/pr-fix` instead of posting. External mode offers posting with a severity floor.

6. **Local mode: resolve the base ref and branch.**
   - `BASE_REF`: `--base` if given. Else the open PR's `baseRefName`. Else the default branch (`git symbolic-ref --short refs/remotes/origin/HEAD | sed 's|^origin/||'`, falling back to `main`). `git rev-parse --verify` it or bail with a clear message.
   - `BRANCH`: `git branch --show-current`, falling back to `detached-$(git rev-parse --short HEAD)`.

7. **Resolve report paths.** Derive `<org>/<repo>` from the source repo (prefer `upstream`, fall back to `origin`). The key follows `lib/pr-artifacts.md`:
   - own, PR mode: `KEY=$(echo "$HEAD_REF_NAME" | tr '/' '-')`
   - own, local mode: `KEY=$(echo "$BRANCH" | tr '/' '-')`
   - external: `KEY=pr-$PR_NUMBER`

   ```bash
   REPORTS_BASE=$(python3 "$HOME/.claude/lib/paths.py" reports-base) || exit 1
   PLAN_DIR="$REPORTS_BASE/prs/$KEY"
   PR_BASE="$PLAN_DIR/reviews"
   REPORT_TS=$(date +%Y-%m-%dT%H-%M-%S)
   PR_DIR="$PR_BASE/$REPORT_TS"
   mkdir -p "$PR_DIR"
   ```

   `reports-base` already includes `<org>/<repo>`, resolved from the same
   remote preference, so only `prs/<key>/` gets appended. Never build it
   from `$HOME` (see `lib/pr-artifacts.md`).
   `$PLAN_DIR/PLAN.md` exists in own mode when the work went through `/pr-plan`. fetch-context reads it. (State keys keep the `pr_` names in both modes.)

8. **Initialize the walker state file:**
   ```bash
   STATE="$PR_DIR/.walk-state.review.json"
   scripts/walk.sh init --state "$STATE"
   ```

9. **Persist run-scoped state:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key mode       --value "$MODE"
   scripts/walk.sh set --state "$STATE" --key ownership  --value "$OWNERSHIP"
   scripts/walk.sh set --state "$STATE" --key canon      --value "<true|false>"
   scripts/walk.sh set --state "$STATE" --key plan_dir   --value "$PLAN_DIR"
   scripts/walk.sh set --state "$STATE" --key pr_base    --value "$PR_BASE"
   scripts/walk.sh set --state "$STATE" --key pr_dir     --value "$PR_DIR"
   scripts/walk.sh set --state "$STATE" --key report_ts  --value "$REPORT_TS"
   # PR mode only:
   scripts/walk.sh set --state "$STATE" --key pr_number  --value "$PR_NUMBER"
   scripts/walk.sh set --state "$STATE" --key pr_author  --value "$AUTHOR"
   # Local mode only:
   scripts/walk.sh set --state "$STATE" --key base_ref   --value "$BASE_REF"
   scripts/walk.sh set --state "$STATE" --key branch     --value "$BRANCH"
   ```

10. **Print a brief opening message**: the mode and why, the ownership and how it was decided, whether a plan was found, the run directory. Examples:

   > Reviewing PR #42, ours (author matches). Local HEAD matches PR head, worktree clean. Plan found at <reports-root>/.../prs/fix-gh-123-retry-budget/PLAN.md. Two reviewers, independent and adversarial (pass --canon for the eng-practices pass).

   > Reviewing PR #456 by @someone (external). Posting will be offered with a severity floor.

   > Local review: branch `fix/auth-retry` vs `main`, 3 unpushed commits ahead of PR #42, worktree dirty. Nothing will be fetched from or posted to GitHub.

## Outputs

- `$PR_DIR/` exists
- `$PR_DIR/.walk-state.review.json` with run-scoped fields in `extra` (including `mode`, `ownership`, `canon`, `plan_dir`)

## Outgoing edges

- → `fetch-context` (always, single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from init --to fetch_context
```

## Failure modes

- Session not on Opus → bail before anything else, naming the model.
- PR not found / no access (PR mode) → bail before touching any files.
- `gh` not authenticated: PR mode → bail with "run `gh auth login` first." No-argument invocation → treat as "no open PR", fall through to local mode, say why.
- `gh api user` fails → ownership can't be detected. Bail in PR mode unless `--own` or `--external` was passed.
- Base ref doesn't resolve (local mode) → bail, suggest `--base <ref>`.
- Not inside a git repository → bail.
