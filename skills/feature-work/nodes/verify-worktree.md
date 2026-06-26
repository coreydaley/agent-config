# Node: verify-worktree

For each repo in the manifest, find or create a worktree on the **`feature/<slug>` branch**, cut from that repo's default branch. This flow commits to a feature branch — never the default branch, so the default stays stable to test against while the feature is in flight. Cwd-independent — the skill operates on absolute paths from the manifest, not on the user's current directory.

## Inputs

- `repo_mode`, `repos` (each entry carries `default_branch`, set by `detect-repo`), `feature_branch` from walker state

```bash
STATE="<path>"
REPO_MODE=$(scripts/walk.sh get --state "$STATE" --key repo_mode)
REPOS=$(scripts/walk.sh get --state "$STATE" --key repos)
FEATURE_BRANCH=$(scripts/walk.sh get --state "$STATE" --key feature_branch)   # feature/<slug>
```

The same `feature/<slug>` worktree per repo serves the whole run, including every sub-issue of the walk (all sub-issues commit to the feature branch).

## Path conventions

- **Bare clone:** `~/Code/github.com/<org>/<repo>/`
  (the GitHub host dir, per the user's `~/Code/<host>/<org>/<repo>/` convention)
- **Worktree (feature branch):** `~/Code/github.com/<org>/<repo>/<feature-slug>/`
  - The dir name is the branch's last path segment (`feature/42-foo` → dir `42-foo`); pass an explicit path to `git worktree add` so the `feature/` prefix isn't treated as a directory.

## Per-repo flow

For each entry in `$REPOS`, with `$BASE_BRANCH` = that repo's `default_branch` and `$FEATURE_BRANCH` the shared feature branch:

```bash
ORG=<org>; REPO=<repo>
BARE="$HOME/Code/github.com/$ORG/$REPO"
WT_DIR_NAME="${FEATURE_BRANCH##*/}"   # last segment, e.g. 42-foo
```

### Step 1: bare clone exists?

```bash
if [ ! -d "$BARE" ]; then
  echo "Repo $ORG/$REPO not cloned at $BARE"
  echo "Clone first: git clone --bare https://github.com/$ORG/$REPO.git $BARE"
  ROUTE_TO_TERMINAL=true
fi
```

If the user wants to clone now, they bail out, do it, and re-run. This skill doesn't auto-clone.

### Step 2: layout classification (three valid layouts)

```bash
IS_BARE=$(git -C "$BARE" rev-parse --is-bare-repository 2>/dev/null)
HAS_UPSTREAM=$(git -C "$BARE" remote get-url upstream 2>/dev/null && echo true || echo false)
```

**Layout A — bare clone with sibling worktrees** (`IS_BARE=true`): the standard bare-clone-with-worktrees workflow. Use steps 3-4 (worktree-list lookup, create the feature-branch worktree with an explicit path).

**Layout B — sandbox-style regular clone** (`IS_BARE=false` AND `HAS_UPSTREAM=false`) and **Layout C — non-bare clone with upstream** (`IS_BARE=false` AND `HAS_UPSTREAM=true`): the clone IS the workspace; there's no sibling worktree. Switch the working tree to the **feature branch** (creating it from the default branch if needed) rather than creating a sibling worktree:

```bash
scripts/walk.sh set --state "$STATE" --key "worktree_paths.$ORG/$REPO" --value "$BARE"

# Auto-stash any pre-existing uncommitted changes — labeled and fully
# recoverable — so the skill's commit stays clean. Don't prompt, don't discard.
DIRTY=$(git -C "$BARE" status --porcelain)
if [ -n "$DIRTY" ]; then
  git -C "$BARE" stash push -u -m "feature-work auto-stash $(git -C "$BARE" rev-parse --short HEAD)"
  echo "Stashed pre-existing uncommitted changes at $BARE (recover: git -C $BARE stash pop)."
fi

# Ensure the workspace is on the FEATURE branch. If it already exists, check it
# out; otherwise create it from the resolved base (the default branch).
if git -C "$BARE" rev-parse --verify "refs/heads/$FEATURE_BRANCH" >/dev/null 2>&1; then
  git -C "$BARE" checkout "$FEATURE_BRANCH"
else
  # Resolve the base (default branch) — see step 4 for BASE_REF resolution.
  git -C "$BARE" checkout -b "$FEATURE_BRANCH" "$BASE_REF"
fi
```

For Layouts B and C the bare-clone path *is* the workspace; only Layout A uses a sibling worktree path.

### Step 3: existing feature-branch worktree?

```bash
git -C "$BARE" worktree list --porcelain \
  | awk -v b="refs/heads/$FEATURE_BRANCH" '
      /^worktree /{p=$2}
      $0=="branch "b{print p}'
```

- **Zero results** → step 4 (create automatically).
- **One result** → **validate state** (below) and use it. No prompt.
- **Multiple results** → use the one whose checked-out branch matches `$FEATURE_BRANCH`. If still ambiguous, use the first valid one and note it. No prompt.

### Validate existing worktree

Before reusing a feature-branch worktree, sanity-check it (stale state from a prior crash otherwise rolls silently into implementation) — handle automatically, don't prompt:

```bash
# Confirm the worktree is on the feature branch; switch it back if it drifted.
ACTUAL=$(git -C "$WT" branch --show-current)
if [ "$ACTUAL" != "$FEATURE_BRANCH" ]; then
  git -C "$WT" checkout "$FEATURE_BRANCH"
fi

# Auto-stash any pre-existing uncommitted changes (labeled, recoverable).
DIRTY=$(git -C "$WT" status --porcelain)
if [ -n "$DIRTY" ]; then
  git -C "$WT" stash push -u -m "feature-work auto-stash $(git -C "$WT" rev-parse --short HEAD)"
  echo "Stashed pre-existing uncommitted changes at $WT (recover: git -C $WT stash pop)."
fi
```

**Reusing an existing feature-branch worktree is the resume case** — the prior run's commits are already on it, and `detect-inflight` reads them to skip already-shipped sub-issues. This is intended, not a conflict.

### Step 4: create the feature-branch worktree automatically (if none existed)

No prompt — create it. Resolve the base (the repo's default branch) first, fetch so the local ref is current, then create the feature branch worktree from it with an **explicit path argument**:

```bash
  BASE_BRANCH=$(gh repo view "$ORG/$REPO" --json defaultBranchRef --jq .defaultBranchRef.name)

  # Resolve the base ref — upstream is source-of-truth in our workflow, then origin.
  if git -C "$BARE" rev-parse --verify "upstream/$BASE_BRANCH" >/dev/null 2>&1; then
    git -C "$BARE" fetch upstream "$BASE_BRANCH":refs/remotes/upstream/$BASE_BRANCH 2>/dev/null
    BASE_REF="upstream/$BASE_BRANCH"
  elif git -C "$BARE" rev-parse --verify "origin/$BASE_BRANCH" >/dev/null 2>&1; then
    git -C "$BARE" fetch origin "$BASE_BRANCH":refs/remotes/origin/$BASE_BRANCH 2>/dev/null
    BASE_REF="origin/$BASE_BRANCH"
  else
    bail "Cannot resolve base $BASE_BRANCH for $ORG/$REPO. Tried upstream/$BASE_BRANCH, origin/$BASE_BRANCH."
  fi

  # Create (or reuse) the feature branch in its own worktree.
  if git -C "$BARE" rev-parse --verify "refs/heads/$FEATURE_BRANCH" >/dev/null 2>&1; then
    # Branch already exists (prior run / pushed earlier) — check it out at the path.
    git -C "$BARE" worktree add "$BARE/$WT_DIR_NAME" "$FEATURE_BRANCH"
  elif git -C "$BARE" rev-parse --verify "refs/remotes/origin/$FEATURE_BRANCH" >/dev/null 2>&1; then
    # Pushed in a prior session but no local branch — track the remote feature branch.
    git -C "$BARE" worktree add "$BARE/$WT_DIR_NAME" "$FEATURE_BRANCH"
  else
    # Brand-new feature branch — cut it from the default branch.
    git -C "$BARE" worktree add -b "$FEATURE_BRANCH" "$BARE/$WT_DIR_NAME" "$BASE_REF"
  fi
```

Store the resulting path.

If `git worktree add` fails (branch in use elsewhere, conflicting paths), surface the error verbatim and route to terminal via `worktree_missing` — that's a genuine wall (the user must resolve it), not a routine prompt.

## Multi-repo

Iterate over all repos in the manifest, resolving each repo's `feature/<slug>` worktree automatically. No prompts. If any repo's bare clone is missing or its `git worktree add` fails, route to terminal via `worktree_missing` with the offending repo named — don't leave the feature half-set-up.

## Outputs

```bash
scripts/walk.sh set --state "$STATE" --key worktree_paths --value "<JSON: org/repo → absolute path>"
```

`worktree_paths` is fully populated here for every repo in the manifest — including the per-sub-issue walk, where all sub-issues reuse these same feature-branch worktrees.

## Outgoing edges

- **`worktree_ok`** → `detect-inflight`. Every repo in the manifest has a workable `feature/<slug>` path (existing feature-branch worktree reused, new one cut from the default branch, or sandbox repo's checkout switched to the feature branch).
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
- **Auto-create, don't prompt.** Cutting the feature-branch worktree is mechanical and idempotent — do it without asking. The only thing that stops the run here is a genuine wall: the bare clone isn't on disk (the user must clone it first), or `git worktree add` errors.
- **One feature branch, per-repo base.** `feature/<slug>` is shared across repos; each repo cuts it from its own default branch (`main` vs `master` can differ).
- **Reusing the feature-branch worktree is the resume path.** Prior commits stay on the branch; `detect-inflight` reads them to skip already-shipped sub-issues. Never force-recreate the branch.
