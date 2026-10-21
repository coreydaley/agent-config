# Node: init

Work out where the findings come from, which PR and branch this is, where the code lives, what the plan says, and which commit regime the PR is in. Set paths, initialize walker state.

## Inputs

- `$ARGUMENTS`: one of a REVIEW.md path, a TRIAGE.md path, a PR number or URL, or nothing. Plus `--source humans|bots|all` (PR mode, default `all`), `--no-ci` (PR mode, checks are on by default), and `--help`.
- Current git checkout

## Steps

1. **`--help` anywhere** → print the help blurb from SKILL.md verbatim and stop.

2. **Session model.** This phase runs on Opus. Read the current session with the `get_session` tool (session `self`) and check `model`. A `model` that doesn't start with `claude-opus-` → stop before creating any state. Name the model the session is on and tell the user to switch to Opus in the model picker and re-run. A skill can read its session's model but not change it. Planning (`/pr-plan`) may run on any model. This phase doesn't.

3. **Source mode** from the argument:

   | Argument | Mode | Findings come from |
   |---|---|---|
   | path ending `REVIEW.md` | `review` | the /pr-review artifact |
   | path ending `TRIAGE.md` | `resume` | an approved triage from an earlier /pr-fix run that stopped before apply |
   | PR number or URL | `pr` | unresolved threads and review bodies on that PR, from humans and bots (`--source` narrows it), plus failing checks (`--no-ci` drops them) |
   | nothing | auto: the newest `reviews/*/REVIEW.md` under the plan dir if one exists, else `pr` against the current branch's PR |

   Exactly one source per run. Never merge REVIEW.md findings with live PR threads.

   In `pr` mode, parse the flags:
   - `--source humans` → only human threads and reviews. `--source bots` → only bot threads and reviews (Copilot, CodeRabbit, linters, our own posted `/pr-review`). `--source all` → both. Default `all`. Anything else → bail naming the value.
   - Failing checks from `gh pr checks` load as findings by default, so a PR URL means "everything that needs addressing": human threads, bot threads, and red checks. `--no-ci` drops the checks when the run is only about comments.
   - Either flag outside `pr` mode → bail, "`--source` and `--no-ci` apply to PR sources."

   A bot is any author whose login ends in `[bot]`, plus `github-actions`, `dependabot`, `renovate`, `copilot`, `coderabbitai`. Our own posted `/pr-review` comments are also bot findings here (they carry the `*(via Claude Code)*` tag and our login).

4. **Repo, branch, PR.** Must be in a git checkout. `<org>/<repo>` from `upstream`, else `origin`. Branch: current branch, or the PR's `headRefName` when a PR was passed. PR: `gh pr view <N-or-branch> --json number,url,headRefName,headRefOid,isDraft,author,reviews,comments,reviewThreads`. No PR is fine in `review` mode (local fixes before push). `pr` mode with no PR → bail.

   The PR must be ours: `.author.login` equals `gh api user -q .login`. Someone else's PR → bail, "pr-fix applies fixes to our own PRs. For reviewing theirs, /pr-review."

5. **Worktree.** The branch's worktree must already exist (pr-build made it, or the user did):
   ```bash
   WT=$(git -C "$ROOT" worktree list --porcelain | awk -v b="refs/heads/$BRANCH" '/^worktree /{p=$2} $0=="branch "b{print p}')
   ```
   Regular clone: the clone itself, and it must have `$BRANCH` checked out. Not found → bail with the `git worktree add` command. A `pr-review-<N>/` path is never a fix target. Dirty tree → show it and ask keep / stash / cancel (`AskUserQuestion` is fine here).

   Confirm `$WT`'s HEAD matches the PR's `headRefOid` when a PR exists. Local ahead of the PR is fine (say so). Local *behind* the PR (someone pushed) → bail, "pull first."

6. **Plan.** `KEY` is the branch with `/` → `-`, and the plan directory comes from the shared resolver rather than a hand-built path (see `lib/pr-artifacts.md`):

   ```bash
   REPORTS_BASE=$(python3 "$HOME/.claude/lib/paths.py" reports-base) || exit 1
   KEY=$(echo "$BRANCH" | tr '/' '-')
   PLAN_DIR="$REPORTS_BASE/prs/$KEY"
   ```

   If `PLAN.md` exists there, it's the scope anchor. If not, note `plan_available=false`. triage falls back to the PR body and the GitHub issues it links (`Closes #N`, `Refs #N`) and says the triage is weaker for it.

7. **Review regime.** A human has reviewed if any review or comment on the PR has an author that isn't us and isn't a bot (`[bot]` suffix, `github-actions`, `dependabot`, `renovate`, `copilot`, `coderabbitai`). Record `human_review_started`. Before human review, fix-ups squash into the commits they amend. After, history is append-only (`lib/pr-discipline.md` § PR Pre-Review Procedure). This one flag drives how apply commits and what push offers.

8. **Paths and state.**
   ```bash
   TS=$(date +%Y-%m-%dT%H-%M-%S)
   FIX_DIR="$PLAN_DIR/fixes/$TS"
   mkdir -p "$FIX_DIR"
   STATE="$PLAN_DIR/.walk-state.fix.json"
   scripts/walk.sh init --state "$STATE"
   scripts/walk.sh set --state "$STATE" --key mode                 --value "<review|pr|resume>"
   scripts/walk.sh set --state "$STATE" --key source_filter        --value "<humans|bots|all>"   # pr mode
   scripts/walk.sh set --state "$STATE" --key include_ci           --value "<true|false>"
   scripts/walk.sh set --state "$STATE" --key source_path          --value "<REVIEW.md or TRIAGE.md path, or empty>"
   scripts/walk.sh set --state "$STATE" --key repo                 --value "$ORG_REPO"
   scripts/walk.sh set --state "$STATE" --key branch               --value "$BRANCH"
   scripts/walk.sh set --state "$STATE" --key worktree             --value "$WT"
   scripts/walk.sh set --state "$STATE" --key plan_dir             --value "$PLAN_DIR"
   scripts/walk.sh set --state "$STATE" --key plan_available       --value "<true|false>"
   scripts/walk.sh set --state "$STATE" --key fix_dir              --value "$FIX_DIR"
   scripts/walk.sh set --state "$STATE" --key pr_number            --value "<N or empty>"
   scripts/walk.sh set --state "$STATE" --key pr_url               --value "<url or empty>"
   scripts/walk.sh set --state "$STATE" --key human_review_started --value "<true|false>"
   scripts/walk.sh set --state "$STATE" --key base_ref             --value "<upstream/<default> or origin/<default>, freshly fetched>"
   ```
   `<remote>` is `upstream` when that remote exists (origin is then the fork), else `origin`. Fetch the base first (`git -C "$WT" fetch <remote> <default> --quiet`) so merge-base math later isn't against a stale fork default.

9. **Opening lines:** mode and source, PR and branch, whether a plan anchors the triage, and the regime in one sentence: "No human review yet, fixes will squash into their original commits" or "Human review started (first comment from a reviewer on <date>), fixes land as new commits."

## Outputs

- `$FIX_DIR/` exists
- `$PLAN_DIR/.walk-state.fix.json` with the keys above

## Outgoing edges

- → `load-findings` (always, single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from init --to load_findings
```

## Failure modes

- Session not on Opus → bail before anything else, naming the model.
- Not in a checkout, PR not ours, worktree missing, local behind remote → bail before creating anything.
- `gh` unauthenticated: `pr` mode bails. `review` mode with no PR continues with `human_review_started=false` and says GitHub wasn't consulted.
- Two REVIEW.md files with the same newest timestamp → ask which.
