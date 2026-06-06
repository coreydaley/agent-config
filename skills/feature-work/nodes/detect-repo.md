# Node: detect-repo

Build the repo manifest, resolve each repo's default branch, and confirm the `feature/<slug>` branch name. The result drives `verify-worktree`, `implement`, and `commit-push`. This flow commits to a **feature branch** cut from each repo's default branch — never to the default branch itself.

## Inputs

- `feature_branch`, `subissue_repos`, `context_dir`, `subissue_ids` from walker state

```bash
STATE="<path>"
FEATURE_BRANCH=$(scripts/walk.sh get --state "$STATE" --key feature_branch)
SUBISSUE_REPOS=$(scripts/walk.sh get --state "$STATE" --key subissue_repos)
```

## Repository manifest

The repos the feature touches are the union of the repos its **sub-issues** touch — already computed as `subissue_repos` in `load-context` (from each sub-issue body's Files section). Collapse the per-sub-issue map into a deduplicated repo list:

### Resolution order

1. **`subissue_repos`** (preferred) — the per-sub-issue → repos map from `load-context`. Union the values, dedupe `<org>/<repo>`. Single entry → single-repo. Multiple → multi-repo.
2. **Feature issue body** — if `subissue_repos` is empty (no Files sections), fall back to any Forgejo repo URLs / `<org>/<repo>` refs in the feature body.
3. **The feature issue's own repo** — last resort: the repo the feature issue lives in (`<owner>/<repo>` from `feature_ref`). Most features are single-repo; this is the common case.

The **primary** repo is the feature issue's own repo when it's in the manifest; otherwise the alphabetically-first `<org>/<repo>`. `commit-push` orders by primary-first.

## Default branch (per repo)

The feature branch is **cut from each repo's default branch**, so resolve and store the default per repo (`main` vs `master` can differ). Resolve via the Forgejo API (authoritative) with a local fallback:

```bash
TOKEN=$(awk '/name: homelab/{f=1} f&&/token:/{print $2; exit}' "$HOME/Library/Application Support/tea/config.yml")
BASE=https://mac-mini.example:3000/api/v1

# Per repo:
DEFAULT_BRANCH=$(curl -sk -H "Authorization: token $TOKEN" \
  "$BASE/repos/<org>/<repo>" | jq -r '.default_branch')
# Local fallback if the API is unreachable:
#   git -C <bare> symbolic-ref --short refs/remotes/origin/HEAD | sed 's#^origin/##'
```

Store the resolved default in each `repos` entry as `default_branch` (the **base** the feature branch is cut from). The feature branch name is shared across repos: `feature_branch` (resolved in `resolve-target`).

## Persist results

```bash
scripts/walk.sh set --state "$STATE" --key repo_mode      --value "<single|multi>"
scripts/walk.sh set --state "$STATE" --key repos          --value "<JSON list of {org, repo, primary, default_branch} entries>"
scripts/walk.sh set --state "$STATE" --key feature_branch --value "<feature/<slug>>"  # carried through unchanged
```

`repos` example:

```json
[
  {"org": "acme", "repo": "web-app", "primary": true,  "default_branch": "main"},
  {"org": "acme", "repo": "api",     "primary": false, "default_branch": "main"}
]
```

Each repo's feature branch is `feature/<slug>` (one name for the whole feature), cut from that repo's `default_branch`.

## Outputs

- `repo_mode`, `repos` (with per-repo `default_branch`), `feature_branch` in walker state

## Outgoing edges

- → `verify-worktree` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from detect_repo --to verify_worktree
```

## Notes

- **The sub-issue Files sections are what make cwd-independence work.** Without them, the skill has to infer repo intent from cwd. With them, the skill knows where to operate before any worktree work happens.
- **For multi-repo with no explicit order**, default to alphabetical by `org/repo`; the feature issue's own repo is primary if present. `commit-push` commits in that order.
- **One feature branch name across all repos.** `feature/<slug>` is shared; only the base (`default_branch`) differs per repo.
