# Node: verify-merged

`--retro` mode: check whether the sprint's work shipped, then write the retrospective regardless (auto-proceed — no prompt). With no PRs, "shipped" means the **Forgejo issues are closed** (their `Closes #N` commits landed on the default branch) and, for the SPRINT.md path, the **default branch was pushed**. **Iterates over every issue / repo in the manifest**, records any gaps, and carries them into the retro.

## Inputs

- `path_mode`, `session_dir`, `repos`, `issue_ids` from walker state
- `$SESSION_DIR/SPRINT.md` (for the Repositories manifest) and `$SESSION_DIR/FORGEJO.md` (if present)

```bash
STATE="<path>"
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
PATH_MODE=$(scripts/walk.sh get --state "$STATE" --key path_mode)
REPOS=$(scripts/walk.sh get --state "$STATE" --key repos)
ISSUE_IDS=$(scripts/walk.sh get --state "$STATE" --key issue_ids)   # JSON list of owner/repo#n
TOKEN=$(awk '/name: homelab/{f=1} f&&/token:/{print $2; exit}' "$HOME/Library/Application Support/tea/config.yml")
BASE=https://mac-mini.example:3000/api/v1
```

## Steps

### 1. Check issue-closed status (forgejo paths)

For each issue ref `<owner>/<repo>#<n>` in `issue_ids`, read its state:

```bash
issue_state() {  # $1=owner/repo  $2=n
  curl -sk -H "Authorization: token $TOKEN" "$BASE/repos/$1/issues/$2" \
    | jq -r '.state'   # "open" | "closed"
}
```

- **`closed`** → shipped (the `Closes #N` commit landed on the default branch). Record as good.
- **`open`** → record as a warning (the commit may not have been pushed, or wasn't committed with the `Closes` trailer).

### 2. Check pushed status (SPRINT.md path, and as a cross-check)

The SPRINT.md path has no issue to read, so confirm each repo's default branch has no unpushed commits:

```bash
for ORG_REPO in $(echo "$REPOS" | jq -r '.[] | .org + "/" + .repo'); do
  WT=$(echo "$WORKTREE_PATHS" | jq -r ".[\"$ORG_REPO\"]")  # if available
  # Unpushed commits relative to the default branch's upstream:
  if git -C "$WT" rev-parse --verify '@{upstream}' >/dev/null 2>&1; then
    AHEAD=$(git -C "$WT" rev-list --count '@{upstream}..HEAD')
    [ "$AHEAD" -gt 0 ] && echo "$ORG_REPO: $AHEAD unpushed commit(s)"
  fi
done
```

Any repo with unpushed commits is a warning (work that hasn't shipped).

### 3. Aggregate

- All targeted issues `closed` (forgejo) AND no unpushed commits (sprintmd) → the happy path.
- Any open issue, unpushed commits, or query error → a gap, recorded but not blocking.

### 4. Decide — auto-proceed

Always route via `proceed`. Writing a retro is low-stakes and reversible, so don't prompt — just print any gaps inline ("Note: issue `<owner>/<repo>#NN` is still open; `<org>/<repo>` has 2 unpushed commits") and carry the structured list into `write-retro`, which records it in RETRO.md under a "What didn't ship" note. The `user_cancel` edge stays only as a safety valve for an unrecoverable error mid-check; the normal `--retro` run never stops to ask.

### 5. Persist results

```bash
scripts/walk.sh set --state "$STATE" --key closed_issue_count --value "<N>"
scripts/walk.sh set --state "$STATE" --key unshipped_warnings --value "<JSON array: per-issue/per-repo status entries>"
```

`unshipped_warnings` carries the structured detail so `write-retro` can surface the gap clearly in RETRO.md.

## Outputs

- `closed_issue_count`, `unshipped_warnings` in walker state

## Outgoing edges

- **`proceed`** → `write-retro`. Everything shipped, or user said "write retro anyway."
- **`user_cancel`** → `terminal`. Safety valve only — an unrecoverable error mid-check. The normal `--retro` run never takes this edge.

Record exactly one:

```bash
# Proceed to write the retro:
scripts/walk.sh transition --state "$STATE" --from verify_merged --to write_retro --condition proceed

# Cancel:
scripts/walk.sh transition --state "$STATE" --from verify_merged --to terminal --condition user_cancel
```

## Notes

- **Always scope the issue query to an explicit `<owner>/<repo>`** (the API path `repos/<owner>/<repo>/issues/<n>`). Never rely on cwd-derived repo defaults — the skill is cwd-independent.
- **Always proceed; never prompt.** Retros are useful even when the artifact trail is incomplete. Capture the gaps in RETRO.md rather than blocking on them.
- **Surface unshipped warnings clearly** inline and in RETRO.md. The user might have intentionally committed some issues and left others, and the retro should note that.
- **An open issue usually means the commit wasn't pushed** (or lacked the `Closes #N` trailer). Point the user at re-running `/sprint-work` for that issue, or pushing the default branch manually.
