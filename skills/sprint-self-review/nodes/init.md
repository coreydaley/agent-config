# Node: init

Resolve the sprint, read the Repositories manifest, locate every open draft PR in scope, set up paths under the sprint session folder, and load any existing ledger.

## Inputs

- `$ARGUMENTS` — optional sprint reference, Linear ID, Linear URL, or PR number/URL, plus flags (`--max-cycles=N`, `--review-tier=high|mid`)
- Current branch / cwd (for auto-detect when no argument is passed)
- Any existing `findings.md` from prior runs on this sprint

## Steps

### 0. Parse flags from `$ARGUMENTS`

Extract these flags before target dispatch — they apply regardless of mode:

```bash
MAX_CYCLES=3                     # default
REVIEW_TIER=mid                  # default for the Claude subagent reviewer
TARGET=""                        # what's left after flag extraction

for arg in $ARGUMENTS; do
  case "$arg" in
    --max-cycles=*)   MAX_CYCLES="${arg#*=}" ;;
    --review-tier=*)  REVIEW_TIER="${arg#*=}" ;;
    --help|-h)        # already handled by SKILL.md; bail
                      ;;
    *)                TARGET="$arg" ;;
  esac
done
```

Validate explicitly:

```bash
case "$REVIEW_TIER" in
  high|mid) ;;
  *) bail "--review-tier must be 'high' or 'mid', got: '$REVIEW_TIER'" ;;
esac

# Positive integer (1 or greater). Reject 0, negatives, non-numerics.
[[ "$MAX_CYCLES" =~ ^[1-9][0-9]*$ ]] \
  || bail "--max-cycles must be a positive integer, got: '$MAX_CYCLES'"
```

Without these, `--max-cycles=0` would persist 0 and `decide.md` would route to `iter_cap` immediately on iter 1 (cycles_in_run=1 ≥ max_cycles=0). `--max-cycles=abc` would silently coerce to 0 in bash arithmetic. Either case looks like a real iteration cap to the user; the input was bogus.

These are persisted to walker state in step 6, where `independent-reviews` reads `review_tier` to pick the Claude subagent's model (`mid → sonnet`, `high → opus`) and `decide` reads `max_cycles` for the loop-cap check.

### 1. Resolve the target → session folder

Apply this dispatch:

```
If $ARGUMENTS is empty:
  branch=$(git branch --show-current 2>/dev/null)
  if branch matches /[A-Z]+-\d+/i:
    → Linear ID, dispatch as /sprints --path <ID>
  elif cwd resolves to a worktree under ~/Code/github.com/<org>/<repo>/:
    → search ~/Reports/.../sprints/*/SPRINT.md whose Repositories manifest
       lists <org>/<repo> AND whose branch matches the worktree's branch
  else:
    → error: "Pass a sprint target or run from a sprint worktree."

Elif $ARGUMENTS matches /^[A-Z]+-\d+$/i or a Linear URL:
  → Search for the issue's home sprint. /sprints --path <ID> only matches
    sessions by timestamp/title — it WON'T find a sprint whose LINEAR.md
    lists the issue. Search LINEAR.md mappings directly:
      from sprint_ledger import discover_reports_roots
      for root in discover_reports_roots():
          for linear_md in root.glob("sprints/*/LINEAR.md"):
              if "<ID>" appears in the "Issues created" table of linear_md:
                  candidates.append((linear_md.parent, root))
    Tie-break:
      1. Prefer sprints whose ledger status is in_progress (per /sprints
         --list --status=in_progress --root <each>).
      2. Then most-recent session timestamp (lexicographic on basename).
      3. If still tied, AskUserQuestion with the candidates.
    If no LINEAR.md matches, fall back to /sprints --path <ID> in case the
    user named a sprint after the issue. If still no match, error per
    step 1's refuse-to-operate prose.

Elif $ARGUMENTS is a sprint query (timestamp prefix / title fragment):
  → /sprints --path <query> to resolve $SESSION_DIR.

Elif $ARGUMENTS is a numeric PR (single-PR back-compat shortcut) or PR URL:
  → gh pr view <pr> to get headRefName, baseRefName, repository.

  **Fast path: cwd-derived root first.** If cwd resolves to
  `~/Code/github.com/<org>/<repo>/...`, check `~/Reports/<org>/<repo>/sprints/`
  before fanning out across all roots. Most invocations come from inside the
  relevant worktree; the cwd-implied root is right ~95% of the time and the
  fast-path is O(N sprints) instead of O(roots × sprints × files).

    cwd_org_repo = parse(cwd)
    if cwd_org_repo:
        candidates += search(~/Reports/<cwd_org_repo>/sprints/, headRefName)
        if candidates: skip multi-root scan (or run it only on no match)

  **Slow path: full multi-root scan.** Falls through if no cwd match, or if
  cwd isn't under ~/Code/github.com/:

      from sprint_ledger import discover_reports_roots
      for root in discover_reports_roots():
          for session_dir in root.glob("sprints/*"):
              # SPRINT.md path: .branch sidecar matches PR's headRefName
              if (session_dir / ".branch").exists():
                  if (session_dir / ".branch").read_text().strip() == headRefName:
                      candidate (session_dir, "sprintmd")
              # linear-walk path: LINEAR.md "Issues created" table has
              # an issue whose branchName matches headRefName
              if (session_dir / "LINEAR.md").exists():
                  if any issue's branchName matches headRefName in linear_md:
                      candidate (session_dir, "linear-walk", issue_id)
              # SPRINT.md fallback (older sprints without .branch):
              if not matched and (session_dir / "SPRINT.md").exists():
                  if Repositories manifest lists this PR's repo AND
                     any branch reference in SPRINT.md matches headRefName:
                      candidate (session_dir, "sprintmd")
    A match has BOTH:
      - Repositories manifest lists this PR's repo
      - branch_name matches headRefName (read from session's .branch sidecar
        or the SPRINT.md's branch reference)
    Tie-breaking when multiple sprints match — apply in order:
      1. **Prefer in_progress.** For each candidate session folder's root,
         derive root = dirname(dirname(session_dir)) and run:
            /sprints --list --status=in_progress --root <root>
         Filter candidates to those that appear in the in_progress list of
         their respective root's ledger.
      2. **Most-recent timestamp.** Among the remaining candidates, pick the
         one with the largest <TS> in its session folder name (lexicographic
         sort works since <TS> is YYYY-MM-DDTHH-MM-SS).
      3. **User picks.** If still tied (e.g., two sprints both in_progress
         with identical timestamps — extremely rare), AskUserQuestion with
         the full candidate list, including each sprint's ledger title and
         root, so the user can disambiguate.
```

If no SPRINT.md matches the PR-shortcut search, **refuse to operate** rather than entering a degraded fallback mode:

```
No sprint found for PR <repo>#<N> (branch: <headRefName>). /sprint-self-review
is sprint-scoped — it needs a SPRINT.md with a Repositories manifest. If this
PR was opened outside the sprint workflow, use /review-pr-simple <PR-url> or
/review-pr-comprehensive <PR-url> instead. If the sprint exists but isn't
linked, run /sprint-work first to populate the manifest, or pass a sprint
reference (LINEAR-ID or sprint query) to this skill.
```

The earlier "degraded mode" with synthetic single-repo manifest is gone — it would either pollute `~/Reports/<org>/<repo>/sprints/` with not-actually-a-sprint folders or reintroduce the per-PR `pr-reviews/` layout we just retired. Better to fail fast and route the user to a skill that genuinely operates per-PR.

Hold `SESSION_DIR` as a local shell variable for now — walker state isn't initialized until step 5. Persisting to `$STATE` happens in step 6 once `$STATE` exists.

```bash
SESSION_DIR=<resolved path>
```

### 2. Read the Repositories manifest

Parse the `## Repositories` section from `$SESSION_DIR/SPRINT.md`. Format:

```markdown
## Repositories
- acme/web-app (primary)
- acme/api
```

Build `repos` as a list of `{org, repo, primary}`. If the section is missing, error: "SPRINT.md at $SESSION_DIR has no Repositories manifest. /sprint-plan should populate it; re-plan or add the section manually." (No degraded fallback — see step 1's refuse-to-operate behavior.)

**For linear-issue mode (single Linear issue, not the full sprint):** narrow `repos` to the issue's actual touched repos, not the full sprint manifest. The full manifest covers the milestone; a single issue may only touch one or two of those repos. Resolving worktrees for unrelated repos on the issue's branch will fail because those branches don't exist in repos the issue never touched.

```bash
if [ "$path_mode" = "linear-issue" ]; then
  # Read issue_repos from walker state (canonical mapping computed by
  # /sprint-work/load-context.md, or parsed from LINEAR.md's
  # "Files (repos)" column for the issue).
  ISSUE_REPOS=$(jq -r --arg id "$ISSUE_ID" '.[$id][]' <<< "$ISSUE_REPOS_MAP")
  # Filter $repos to entries whose <org>/<repo> appears in $ISSUE_REPOS.
fi
```

Sprintmd and full-sprint modes use the unfiltered manifest.

**Primary repo defaulting:** if no entry has the `(primary)` tag, default to alphabetical-first by `<org>/<repo>` (matching `/sprint-work/detect-repo.md:99`). Both skills must apply the same fallback or PR cross-link ordering and "primary worktree" choices diverge between sprint-work and self-review.

### 3. Resolve the branch and worktrees per repo

The branch name is shared across every repo for one branch unit. **One self-review run = one branch unit = one issue's branch (linear-walk) or one sprint's branch (sprintmd / linear-issue).** Reject milestone-level input (a `linear-walk` produces N branches across N issues; reviewing them as one set conflates separate change units):

```
If the resolved target is a Linear milestone (linear-walk):
  bail "Milestone-level self-review isn't supported — each issue in a
  milestone has its own branch unit (per Linear's branchName) and its
  own PR set. Run /sprint-self-review <LINEAR-ID> per issue once
  /sprint-work has completed that issue. Issues in this milestone:
    CON-NNNN  <title>
    CON-NNNN  <title>
    ..."
```

For accepted targets, branch resolution proceeds:

- **Linear mode** (linear-issue, single Linear issue): use the issue's `branchName` field.
- **SPRINT.md mode**, in priority order:
  1. **`.branch` sidecar**: `$SESSION_DIR/.branch` is the durable record `/sprint-work/detect-repo.md` writes after every run. Read this first — it's the canonical answer for SPRINT.md sprints.
  2. **Current branch**: if running from a worktree under `~/Code/github.com/<org>/<repo>/` matching a manifest entry, use that worktree's branch.
  3. **Prompt**: "What is the sprint's branch name?"

For each repo in `repos`, resolve its worktree path. Mirror `/sprint-work/verify-worktree`'s detection — three valid layouts, not just two:

```bash
BARE="$HOME/Code/github.com/<org>/<repo>"
IS_BARE=$(git -C "$BARE" rev-parse --is-bare-repository 2>/dev/null)
HAS_UPSTREAM=$(git -C "$BARE" remote get-url upstream 2>/dev/null && echo true || echo false)

if [ "$IS_BARE" = "true" ]; then
  # Standard bare-clone + sibling worktree pattern
  WT="$BARE/$BRANCH"
elif [ "$IS_BARE" = "false" ] && [ "$HAS_UPSTREAM" = "false" ]; then
  # Sandbox-style regular clone (no upstream) — clone IS the workspace
  WT="$BARE"
elif [ "$IS_BARE" = "false" ] && [ "$HAS_UPSTREAM" = "true" ]; then
  # Regular non-bare clone WITH upstream — also valid (developer doing
  # normal fork-with-upstream workflow without bare-clone setup). The
  # clone IS the workspace, same as sandbox-style; the upstream remote
  # exists for fetching the source-of-truth base.
  WT="$BARE"
else
  bail "Repo $ORG/$REPO at $BARE not found or unreadable."
fi

# Verify the worktree exists and is on the right branch:
test -d "$WT" || bail "Worktree missing: $WT — run /sprint-work to create it."
[ "$(git -C "$WT" branch --show-current)" = "$BRANCH" ] \
  || bail "Worktree at $WT is not on branch $BRANCH."
```

Hold `worktree_paths` (a `{<org>/<repo>: <abs path>}` map) as a local variable. It gets persisted to walker state in step 6 once `$STATE` is initialized.

### 4. Find draft PRs per repo

For each repo:

```bash
PR_INFO=$(gh pr list --repo "<org>/<repo>" --head "$BRANCH" --state open --draft \
  --json number,baseRefName,url -q '.[0]')
```

Persist results as an **object map keyed by `<org>/<repo>`** (not a list of records — `compute-diff` reads via `jq -r ".[\"$ORG/$REPO\"].base_ref"`):

```json
{
  "acme/web-app": {"pr_number": 1234, "base_ref": "main", "url": "https://github.com/..."},
  "acme/api": {"pr_number": 5678, "base_ref": "main", "url": "https://github.com/..."}
}
```

If a repo has no open draft PR, surface a warning but continue: maybe the user opened it as ready, or hasn't pushed yet. Self-review still works on the local diff; the PR association is for the eventual ready-for-review handoff.

**Critical:** when no PR exists for a repo, `compute-diff` still needs `prs[repo].base_ref` to compute the diff. Fall back to the repo's default branch:

```bash
# When gh pr list returns no draft PR for this repo:
DEFAULT_BASE=$(gh repo view "$ORG_REPO" --json defaultBranchRef \
  -q '.defaultBranchRef.name')
# Persist as if it were a PR's base_ref so compute-diff doesn't need
# to know whether the PR existed.
PRS_ENTRY=$(jq -n --arg base "$DEFAULT_BASE" \
  '{pr_number: null, base_ref: $base, url: null}')
```

Without the fallback, `compute-diff`'s base-ref resolution chain (`prs[repo].base_ref` → upstream/origin/local) starts with an empty value and fails. The fallback ensures every entry in `prs` has a usable `base_ref` even when the PR isn't open yet.

If **every** repo lacks a draft PR, error: "No draft PRs found for branch `$BRANCH` in any of the manifest repos. Run `/sprint-work` first to open them."

### 5. Resolve report paths and initialize walker state

This is where the walker state file gets created. **All `scripts/walk.sh set --state "$STATE"` calls must come after this step.**

```bash
SELF_REVIEW_DIR="$SESSION_DIR/self-review"
mkdir -p "$SELF_REVIEW_DIR"
FINDINGS="$SELF_REVIEW_DIR/findings.md"
STATE="$SELF_REVIEW_DIR/.walk-state.json"

# Initialize the walker state file. After this, $STATE exists and persist
# calls are safe.
scripts/walk.sh init --state "$STATE"
```

### 6. Persist run-scoped state

```bash
scripts/walk.sh set --state "$STATE" --key session_dir       --value "$SESSION_DIR"
# reports_root is <root>/ given session_dir = <root>/sprints/<TS>/. Persist
# alongside session_dir so any downstream /sprints calls can pass --root
# without re-deriving via dirname-dirname.
scripts/walk.sh set --state "$STATE" --key reports_root      --value "$(dirname "$(dirname "$SESSION_DIR")")"
scripts/walk.sh set --state "$STATE" --key self_review_dir   --value "$SELF_REVIEW_DIR"
scripts/walk.sh set --state "$STATE" --key findings_path     --value "$FINDINGS"
scripts/walk.sh set --state "$STATE" --key branch            --value "$BRANCH"
scripts/walk.sh set --state "$STATE" --key repos             --value "<JSON list>"
scripts/walk.sh set --state "$STATE" --key worktree_paths    --value "<JSON: org/repo → abs path>"
scripts/walk.sh set --state "$STATE" --key prs               --value "<JSON: per-repo PR info>"
scripts/walk.sh set --state "$STATE" --key max_cycles        --value "$MAX_CYCLES"
scripts/walk.sh set --state "$STATE" --key review_tier       --value "$REVIEW_TIER"
scripts/walk.sh set --state "$STATE" --key cycles_in_run     --value 0
scripts/walk.sh set --state "$STATE" --key next_iteration    --value "$NEXT_ITER_N"
```

Subsequent nodes read these via `scripts/walk.sh get --state "$STATE" --key <name>` rather than re-deriving them.

### 7. Load the ledger

If `$FINDINGS` exists, load it. We're continuing a prior run.

### 8. Pick the next iteration number

Look for `$SELF_REVIEW_DIR/iteration-*` directories. The next iteration is `max(existing) + 1`, or `1` if none exist. Iterations number monotonically across the sprint's life — don't reset per run.

```bash
scripts/walk.sh set --state "$STATE" --key next_iteration --value "$NEXT_ITER_N"
```

### 9. Print a brief opening message

Tell the user: sprint reference (resolved session path), repos in scope, branch, draft PR URLs, iteration number, prior runs (if findings.md existed), path to findings.md.

## Outputs

- `$SELF_REVIEW_DIR/` exists
- `$SELF_REVIEW_DIR/.walk-state.json` exists with all run-scoped variables in `extra`
- `findings.md` either preserved or initialized
- The user has seen a clear summary of what's in scope before any review work runs

## Outgoing edges

- → `compute-diff` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from init --to compute_diff
```

## Failure modes

- No SPRINT.md found (PR-shortcut entry didn't match any sprint, or sprint reference points nowhere): bail with the message in step 1 directing the user to `/review-pr-simple` / `/review-pr-comprehensive` for non-sprint PRs.
- SPRINT.md found but `## Repositories` section missing: bail with "re-plan or add the section manually."
- A worktree in the manifest is missing: bail with the path and tell the user to run `/sprint-work` to create it. **Don't auto-create.**
- All repos lack draft PRs: bail with "run `/sprint-work` first."
- `gh` not authenticated: bail with "run `gh auth login` first."
