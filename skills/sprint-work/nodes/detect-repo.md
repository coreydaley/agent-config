# Node: detect-repo

Phase 3: build the repo manifest and resolve each repo's default branch. The result drives `verify-worktree`, `implement`, and `commit-push`. This flow commits straight to the default branch — there's no per-sprint or per-issue feature branch.

## Inputs

- `path_mode`, `context_dir`, `sprint_md_path` from walker state

```bash
STATE="<path>"
PATH_MODE=$(scripts/walk.sh get --state "$STATE" --key path_mode)
SPRINT_MD=$(scripts/walk.sh get --state "$STATE" --key sprint_md_path)
```

## Repository manifest

The **Repositories** section in SPRINT.md is the authoritative source. Format:

```markdown
## Repositories
- acme/web-app (primary)
- acme/api
```

Each entry is `<org>/<repo>` matching the Forgejo owner/repo path. The first entry (or one tagged `(primary)`) is the primary repo for ordering in `commit-push`.

### Resolution order

1. **`Repositories` section in SPRINT.md** — preferred source. Single entry → single-repo. Multiple → multi-repo.
2. **`Repositories` section in FORGEJO.md** — `/sprint-plan-to-issues/finalize.md` carries the manifest into FORGEJO.md verbatim so the Forgejo path can resolve repos without depending on SPRINT.md being reachable. Read `forgejo_md_path` from walker state (set by `load-context`) and parse its `## Repositories` section.
3. **Forgejo issue body** — for `forgejo-issue` / `forgejo-walk`, fall back to the issue's Files section and any Forgejo repo URLs in the description if neither SPRINT.md nor FORGEJO.md has a Repositories section.
4. **Files Summary in SPRINT.md** — last-resort inference for older SPRINT.md files that predate the Repositories section.

If multiple sources are present, prefer (1). If (1) is missing, log a note for `recommend-execution`'s DoR check (it'll surface as a missing-manifest warning on the next plan run) but continue with (2)/(3) for this run.

## Default branch (per repo)

Work commits to **each repo's default branch** — no feature branch. Defaults can differ per repo (`main` vs `master`), so resolve and store one per repo. Resolve via the Forgejo API (authoritative) with a local fallback:

```bash
TOKEN=$(awk '/name: homelab/{f=1} f&&/token:/{print $2; exit}' "$HOME/Library/Application Support/tea/config.yml")
BASE=https://mac-mini.example:3000/api/v1

# Per repo:
DEFAULT_BRANCH=$(curl -sk -H "Authorization: token $TOKEN" \
  "$BASE/repos/<org>/<repo>" | jq -r '.default_branch')
# Local fallback if the API is unreachable:
#   git -C <bare> symbolic-ref --short refs/remotes/origin/HEAD | sed 's#^origin/##'
```

Store the resolved default in each `repos` entry as `default_branch`. `implement` / `commit-push` use it for the per-repo commit + push target.

For display and the `--retro` handoff, also persist `branch_name` = the **primary** repo's default branch (a convenient single value; multi-repo consumers read per-repo `default_branch` from `repos`).

## Persist results

```bash
scripts/walk.sh set --state "$STATE" --key repo_mode    --value "<single|multi>"
scripts/walk.sh set --state "$STATE" --key repos        --value "<JSON list of {org, repo, primary, default_branch} entries>"
scripts/walk.sh set --state "$STATE" --key branch_name  --value "<primary repo's default branch>"
scripts/walk.sh set --state "$STATE" --key merge_order  --value "<JSON list or empty>"
```

`repos` example:

```json
[
  {"org": "acme", "repo": "web-app", "primary": true,  "default_branch": "main"},
  {"org": "acme", "repo": "api",     "primary": false, "default_branch": "main"}
]
```

## Outputs

- `repo_mode`, `repos` (with per-repo `default_branch`), `branch_name`, `merge_order` in walker state

## Outgoing edges

- → `verify-worktree` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from detect_repo --to verify_worktree
```

## Notes

- **The Repositories manifest is what makes cwd-independence work.** Without it, the skill has to infer repo intent from cwd or file paths. With it, the skill knows where to operate before any worktree work happens.
- **For multi-repo with no explicit merge order**, default to alphabetical by `org/repo`. `commit-push` commits in that order.
- **Don't pick a primary** silently when SPRINT.md doesn't tag one. Default to alphabetical-first and note it in walker state for `summarize` to surface.
- **No feature branch, no `.branch` sidecar.** This flow commits to the default branch; there's nothing branch-specific to persist across runs.
