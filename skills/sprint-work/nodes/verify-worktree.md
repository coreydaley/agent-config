# Node: verify-worktree

Phase 4: for each repo in the manifest, find or create a worktree **on that repo's default branch** — this flow commits straight to the default branch, no feature branch. Cwd-independent — the skill operates on absolute paths from the manifest, not on the user's current directory.

## Inputs

- `repo_mode`, `repos` (each entry carries `default_branch`, set by `detect-repo`) from walker state

```bash
STATE="<path>"
REPO_MODE=$(scripts/walk.sh get --state "$STATE" --key repo_mode)
REPOS=$(scripts/walk.sh get --state "$STATE" --key repos)
```

The same default-branch worktree per repo serves the whole run, including every issue of a `forgejo-walk` (all issues commit to the default branch).

## Path conventions

- **Bare clone:** `~/Code/mac-mini.example/<org>/<repo>/`
  (the Forgejo host dir, per the user's `~/Code/<host>/<org>/<repo>/` convention)
- **Worktree (default branch):** `~/Code/mac-mini.example/<org>/<repo>/<default-branch>/`
  - Created via `git -C <bare> worktree add <default-branch>` (git defaults the dir to `./<default-branch>`).

## Per-repo flow

For each entry in `$REPOS`, with `$BRANCH` = that repo's `default_branch`:

```bash
ORG=<org>; REPO=<repo>
BARE="$HOME/Code/mac-mini.example/$ORG/$REPO"
```

### Step 1: bare clone exists?

```bash
if [ ! -d "$BARE" ]; then
  echo "Repo $ORG/$REPO not cloned at $BARE"
  echo "Clone first: git clone --bare ssh://git@mac-mini.example:2222/$ORG/$REPO.git $BARE"
  ROUTE_TO_TERMINAL=true
fi
```

If the user wants to clone now, they bail out, do it, and re-run. This skill doesn't auto-clone.

### Step 2: layout classification (three valid layouts)

Three valid clone layouts to detect:

```bash
IS_BARE=$(git -C "$BARE" rev-parse --is-bare-repository 2>/dev/null)
HAS_UPSTREAM=$(git -C "$BARE" remote get-url upstream 2>/dev/null && echo true || echo false)
```

**Layout A — bare clone with sibling worktrees** (`IS_BARE=true`): the standard bare-clone-with-worktrees workflow. Use steps 3-4 (worktree-list lookup, create with explicit path).

**Layout B — sandbox-style regular clone** (`IS_BARE=false` AND `HAS_UPSTREAM=false`): the clone IS the workspace. Skip worktree creation:

```bash
scripts/walk.sh set --state "$STATE" --key "worktree_paths.$ORG/$REPO" --value "$BARE"

# Auto-stash any pre-existing uncommitted changes — labeled and fully
# recoverable — so the skill's commit stays clean. Don't prompt, don't discard.
DIRTY=$(git -C "$BARE" status --porcelain)
if [ -n "$DIRTY" ]; then
  git -C "$BARE" stash push -u -m "sprint-work auto-stash $(git -C "$BARE" rev-parse --short HEAD)"
  echo "Stashed pre-existing uncommitted changes at $BARE (recover: git -C $BARE stash pop)."
fi

# Ensure the workspace is on the default branch ($BRANCH). It always exists,
# so just check it out — never -B (that would reset the branch pointer).
CUR=$(git -C "$BARE" branch --show-current)
if [ "$CUR" != "$BRANCH" ]; then
  git -C "$BARE" checkout "$BRANCH"
fi
```

**Layout C — non-bare clone with upstream** (`IS_BARE=false` AND `HAS_UPSTREAM=true`): a developer doing fork-with-upstream workflow without bare-clone setup. Same handling as Layout B: the clone IS the workspace; switch the working tree to `$BRANCH` rather than creating a sibling worktree.

```bash
scripts/walk.sh set --state "$STATE" --key "worktree_paths.$ORG/$REPO" --value "$BARE"

# Auto-stash any pre-existing uncommitted changes — labeled and fully
# recoverable — so the skill's commit stays clean. Don't prompt, don't discard.
DIRTY=$(git -C "$BARE" status --porcelain)
if [ -n "$DIRTY" ]; then
  git -C "$BARE" stash push -u -m "sprint-work auto-stash $(git -C "$BARE" rev-parse --short HEAD)"
  echo "Stashed pre-existing uncommitted changes at $BARE (recover: git -C $BARE stash pop)."
fi

# Ensure the workspace is on the default branch ($BRANCH). It always exists,
# so just check it out — never -B (that would reset the branch pointer).
CUR=$(git -C "$BARE" branch --show-current)
if [ "$CUR" != "$BRANCH" ]; then
  git -C "$BARE" checkout "$BRANCH"
fi
```

For Layouts B and C, the bare-clone path *is* the workspace; only Layout A uses a sibling worktree path.

### Step 3: existing worktree(s) for the branch?

```bash
git -C "$BARE" worktree list --porcelain \
  | awk -v b="refs/heads/$BRANCH" '
      /^worktree /{p=$2}
      $0=="branch "b{print p}'
```

- **Zero results** → step 4 (create automatically).
- **One result** → **validate state** (see below) and use it. No prompt.
- **Multiple results** → use the one whose checked-out branch matches `$BRANCH` (the default). If still ambiguous, use the first valid one and note it. No prompt.

### Validate existing worktree

Before storing a reused worktree path, sanity-check it. Stale state from a prior crash silently rolls into the implementation phase otherwise — but handle it automatically, don't prompt:

```bash
# Confirm the worktree is on the right branch (worktree-list can show one
# branch while a different one is checked out after manual git ops). If it's
# off, switch it back to the default branch ($BRANCH always exists).
ACTUAL=$(git -C "$WT" branch --show-current)
if [ "$ACTUAL" != "$BRANCH" ]; then
  git -C "$WT" checkout "$BRANCH"
fi

# Auto-stash any pre-existing uncommitted changes (labeled, recoverable)
# so the skill's commit stays clean. Don't prompt, don't discard.
DIRTY=$(git -C "$WT" status --porcelain)
if [ -n "$DIRTY" ]; then
  git -C "$WT" stash push -u -m "sprint-work auto-stash $(git -C "$WT" rev-parse --short HEAD)"
  echo "Stashed pre-existing uncommitted changes at $WT (recover: git -C $WT stash pop)."
fi
```

### Step 4: create the worktree automatically (if none existed)

No prompt — create it. Resolve the base ref first, then create with an **explicit path argument** to avoid git interpreting slash-bearing branches as paths and to avoid silently creating from local HEAD (which may be on the wrong base):

```bash
  # Resolve the intended base. Try upstream first (source-of-truth in
  # our workflow), then origin. Fetch so the local ref is current.
  # Forgejo default branch via the API (tea has no repo-view field for it):
  TOKEN=$(awk '/name: homelab/{f=1} f&&/token:/{print $2; exit}' "$HOME/Library/Application Support/tea/config.yml")
  DEFAULT_BASE=$(curl -sk -H "Authorization: token $TOKEN" \
    "https://mac-mini.example:3000/api/v1/repos/$ORG/$REPO" \
    | jq -r '.default_branch')

  if git -C "$BARE" rev-parse --verify "upstream/$DEFAULT_BASE" >/dev/null 2>&1; then
    git -C "$BARE" fetch upstream "$DEFAULT_BASE":refs/remotes/upstream/$DEFAULT_BASE 2>/dev/null
    BASE_REF="upstream/$DEFAULT_BASE"
  elif git -C "$BARE" rev-parse --verify "origin/$DEFAULT_BASE" >/dev/null 2>&1; then
    git -C "$BARE" fetch origin "$DEFAULT_BASE":refs/remotes/origin/$DEFAULT_BASE 2>/dev/null
    BASE_REF="origin/$DEFAULT_BASE"
  else
    bail "Cannot resolve base $DEFAULT_BASE for $ORG/$REPO. Tried upstream/$DEFAULT_BASE, origin/$DEFAULT_BASE."
  fi

  # Check whether the branch already exists. If yes, just check it out at
  # the worktree path. If no, create from $BASE_REF.
  if git -C "$BARE" rev-parse --verify "refs/heads/$BRANCH" >/dev/null 2>&1; then
    git -C "$BARE" worktree add "$BARE/$BRANCH" "$BRANCH"
  elif git -C "$BARE" rev-parse --verify "refs/remotes/upstream/$BRANCH" >/dev/null 2>&1 \
       || git -C "$BARE" rev-parse --verify "refs/remotes/origin/$BRANCH" >/dev/null 2>&1; then
    # Track the existing remote branch
    git -C "$BARE" worktree add "$BARE/$BRANCH" "$BRANCH"
  else
    # Brand-new branch — create from the resolved base
    git -C "$BARE" worktree add -b "$BRANCH" "$BARE/$BRANCH" "$BASE_REF"
  fi
  ```

Store the resulting path.

If `git worktree add` fails (branch in use elsewhere, conflicting paths), surface the error verbatim and route to terminal via `worktree_missing` — that's a genuine wall (the user must resolve it), not a routine prompt.

## Multi-repo

Iterate over all repos in the manifest, resolving each repo's default-branch worktree automatically. No prompts. If any repo's bare clone is missing or its `git worktree add` fails, route to terminal via `worktree_missing` with the offending repo named — don't leave the sprint half-set-up.

## Outputs

```bash
scripts/walk.sh set --state "$STATE" --key worktree_paths --value "<JSON: org/repo → absolute path>"
```

`worktree_paths` is fully populated here for every repo in the manifest — including `forgejo-walk`, where all issues reuse these same default-branch worktrees.

## Outgoing edges

- **`worktree_ok`** → `detect-inflight`. Every repo in the manifest has a workable default-branch path (existing worktree reused, new worktree auto-created, or sandbox repo's checkout dir).
- **`worktree_missing`** → `terminal`. A genuine wall: the bare clone is missing, or `git worktree add` failed. Diagnostics already printed.

Record exactly one:

```bash
# Ready:
scripts/walk.sh transition --state "$STATE" --from verify_worktree --to detect_inflight --condition worktree_ok

# Bail (genuine wall — bare clone missing or worktree add failed):
scripts/walk.sh transition --state "$STATE" --from verify_worktree --to terminal --condition worktree_missing
```

## Notes

- **Cwd-independent.** This node never reads `pwd` to locate work. Everything resolves through `$BARE` paths derived from the manifest.
- **Auto-create, don't prompt.** Resolving and creating the default-branch worktree is mechanical and idempotent — do it without asking. The only thing that stops the run here is a genuine wall: the bare clone isn't on disk (the user must clone it first), or `git worktree add` errors.
- **Each repo uses its own default branch.** Defaults can differ (`main` vs `master`); `$BRANCH` per repo comes from that repo's `default_branch` in `repos`. No feature branch is created.
- **For `forgejo-walk`**, this node still resolves every repo's default-branch worktree up front; the per-issue loop in `implement` reuses them, committing one commit per issue to the default branch.
