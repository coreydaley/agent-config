# Node: verify-merged

`--retro` mode: confirm the sprint's PRs have actually merged before writing a retrospective. **Iterates over every repo in the manifest** (multi-repo aware) and aggregates results. User can override "write retro anyway" if any check is inconclusive.

## Inputs

- `path_mode`, `session_dir`, `repos`, `branch_name`, `issue_branches`, `issue_ids` from walker state
- `$SESSION_DIR/SPRINT.md` (for the Repositories manifest) and `$SESSION_DIR/LINEAR.md` (if present)

```bash
STATE="<path>"
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
PATH_MODE=$(scripts/walk.sh get --state "$STATE" --key path_mode)
REPOS=$(scripts/walk.sh get --state "$STATE" --key repos)
BRANCH=$(scripts/walk.sh get --state "$STATE" --key branch_name)         # used by linear-issue and sprintmd
ISSUE_BRANCHES=$(scripts/walk.sh get --state "$STATE" --key issue_branches) # JSON list of per-issue branches; linear-walk only
ISSUE_IDS=$(scripts/walk.sh get --state "$STATE" --key issue_ids)        # JSON list, kept for legacy bookkeeping
```

## Steps

### 1. Locate the sprint's PRs (per-repo)

For each repo in the manifest, run a per-repo PR query. The skill is cwd-independent — never assume `gh pr list` is targeting the right repo by default. **Always search by branch (`--head`)**, not by Linear ID title prefix — `gh pr list --search "<ID> in:title"` matches every PR with that ID in the title (including unrelated old attempts), corrupting the merged-status aggregation.

```bash
PRS_FOUND=()

if [ "$PATH_MODE" = "linear-walk" ]; then
  # Build the expected (issue, repo, branch) matrix from the canonical
  # issue_repos mapping that load-context computed once. Don't re-parse
  # LINEAR.md or issue bodies here — that risks divergent normalization.
  #
  # ISSUE_REPOS:    {<issue_id>: [<org>/<repo>, ...]}  (from load-context)
  # ISSUE_BRANCHES: {<issue_id>: <branchName>}         (from detect-repo)
  ISSUE_REPOS=$(scripts/walk.sh get --state "$STATE" --key issue_repos)

  EXPECTED_MATRIX=$(jq -nc --argjson ir "$ISSUE_REPOS" --argjson ib "$ISSUE_BRANCHES" '
    [$ir | to_entries[] as $e | $e.value[] as $repo
       | {issue_id: $e.key, org_repo: $repo, branch: $ib[$e.key]}]
  ')

  # Query only the expected cells.
  echo "$EXPECTED_MATRIX" | jq -c '.[]' | while read -r cell; do
    ISSUE_ID=$(echo "$cell" | jq -r '.issue_id')
    ORG_REPO=$(echo "$cell" | jq -r '.org_repo')
    BRANCH_PER_ISSUE=$(echo "$cell" | jq -r '.branch')
    gh pr list --repo "$ORG_REPO" --head "$BRANCH_PER_ISSUE" --state all \
      --json number,state,merged,url,headRefName -q '.[]'
  done
else
  # linear-issue and sprintmd: one branch across the manifest's repos.
  for ORG_REPO in $(echo "$REPOS" | jq -r '.[] | .org + "/" + .repo'); do
    gh pr list --repo "$ORG_REPO" --head "$BRANCH" --state all \
      --json number,state,merged,url,headRefName -q '.[]'
  done
fi
```

The branch is the more specific identifier than a Linear ID in title. linear-walk's per-(issue, repo) matrix prevents false "no PR found" warnings on repos an issue never touched.

If no PR surfaces for an **expected** cell, treat as an unmerged warning requiring user confirmation. Cells outside the expected matrix are silent (issue X doesn't touch repo Y, no warning).

### 2. Aggregate merged status

For every PR found across all repos:

- **Merged** → record as good.
- **Open** → record as warning (still in flight).
- **Closed without merge** → record as flag.

The aggregation is the source of truth. Any repo with a non-merged PR triggers the user-confirmation prompt below.

### 3. Decide

- **All PRs across all repos merged** → route via `proceed` automatically. This is the happy path.
- **Any repo has open / closed-without-merge / no-PR-found** → AskUserQuestion with the specific list ("PR `<org>/<repo>#NNNN` is still open" or "No PR found in `<org>/<repo>`. Write retro anyway?") → user picks `proceed` / `cancel`. **A missing PR in a manifest repo is treated as unmerged**, not as "doesn't apply" — the manifest claimed the sprint touches that repo, so a missing PR there is a gap worth surfacing.
- **A repo's `gh pr list` failed** (auth issue, repo gone) → record per-repo error, ask user. Don't silently treat as "merged."

### 4. Persist results

```bash
scripts/walk.sh set --state "$STATE" --key merged_pr_count --value "<N>"
scripts/walk.sh set --state "$STATE" --key unmerged_warnings --value "<JSON array: per-repo status entries>"
```

`unmerged_warnings` carries the structured detail so `write-retro` can surface the gap clearly in RETRO.md.

## Outputs

- `merged_pr_count`, `unmerged_warnings` in walker state

## Outgoing edges

- **`proceed`** → `write-retro`. All merged across every repo, or user said "write retro anyway."
- **`user_cancel`** → `terminal`. User backed out at the warning prompt.

Record exactly one:

```bash
# Proceed to write the retro:
scripts/walk.sh transition --state "$STATE" --from verify_merged --to write_retro --condition proceed

# Cancel:
scripts/walk.sh transition --state "$STATE" --from verify_merged --to terminal --condition user_cancel
```

## Notes

- **Always pass `--repo <org>/<repo>` to `gh pr list`.** Never rely on cwd-derived repo defaults — the skill is cwd-independent and might be running from anywhere.
- **Default to proceed when ambiguous (no PRs found in any repo).** Retros are useful even when the artifact trail is incomplete; the user can capture lessons regardless.
- **Surface unmerged warnings clearly** in the prompt — they should appear in RETRO.md too. For multi-repo sprints, the user might have intentionally merged 2 of 3 PRs and abandoned the third; the retro should note that.
- **For `linear-walk` (multi-issue milestone):** the expected PR set is **per-issue**. Each Linear issue's body lists Files (which imply repos); the issue's expected PRs are one per repo it touches. Build an `{(issue_id, repo): expected/optional}` matrix from the per-issue Files sections. **Warn only on missing expected cells**, not on every (issue × repo) combination — silence on optional cells (issue X never touched repo Y) is correct; silence on expected cells (issue X did touch repo Y but no PR found) requires user confirmation, same as the sprintmd / linear-issue path. This restores consistency: a manifest entry with no PR is a warning everywhere; a non-manifest cross-product cell isn't.
