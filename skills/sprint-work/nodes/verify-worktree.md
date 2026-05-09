# Node: verify-worktree

Phase 4: for each repo in the manifest, find or create a worktree on the sprint's branch. Cwd-independent — the skill operates on absolute paths from the manifest, not on the user's current directory.

## Inputs

- `repo_mode`, `repos`, `branch_name`, `issue_branches` from walker state

```bash
STATE="<path>"
REPO_MODE=$(scripts/walk.sh get --state "$STATE" --key repo_mode)
REPOS=$(scripts/walk.sh get --state "$STATE" --key repos)
BRANCH_NAME=$(scripts/walk.sh get --state "$STATE" --key branch_name)
```

For `linear-walk`, the per-issue branch resolution happens inside `implement`'s iteration. This node still runs to verify the bare clones exist for every repo in the milestone scope.

## Path conventions

- **Bare clone:** `~/Code/github.com/<org>/<repo>/`
- **Worktree (per branch):** `~/Code/github.com/<org>/<repo>/<branch>/`
  - Created via `git -C <bare> worktree add <branch>` (no explicit path; git defaults to `./<branch>`)
  - For multi-segment branches (e.g., `coreydaley/proj-1148-foo`), git creates the nested dir naturally.

## Per-repo flow

For each entry in `$REPOS`, with `$BRANCH` resolved (`branch_name` for sprintmd / single-issue; deferred for `linear-walk`):

```bash
ORG=<org>; REPO=<repo>
BARE="$HOME/Code/github.com/$ORG/$REPO"
```

### Step 1: bare clone exists?

```bash
if [ ! -d "$BARE" ]; then
  echo "Repo $ORG/$REPO not cloned at $BARE"
  echo "Clone first: gh repo clone $ORG/$REPO $BARE -- --bare"
  ROUTE_TO_TERMINAL=true
fi
```

If the user wants to clone now, they bail out, do it, and re-run. This skill doesn't auto-clone.

### Step 2: layout classification (three valid layouts)

Match `/sprint-self-review`'s detection — same three valid layouts:

```bash
IS_BARE=$(git -C "$BARE" rev-parse --is-bare-repository 2>/dev/null)
HAS_UPSTREAM=$(git -C "$BARE" remote get-url upstream 2>/dev/null && echo true || echo false)
```

**Layout A — bare clone with sibling worktrees** (`IS_BARE=true`): the standard bare-clone-with-worktrees workflow. Use steps 3-4 (worktree-list lookup, create with explicit path).

**Layout B — sandbox-style regular clone** (`IS_BARE=false` AND `HAS_UPSTREAM=false`): the clone IS the workspace. Skip worktree creation:

```bash
scripts/walk.sh set --state "$STATE" --key "worktree_paths.$ORG/$REPO" --value "$BARE"

# Validate state before any branch switch — symmetric with Layout A's
# existing-worktree validation. A user with uncommitted work in a
# sandbox-style repo should see the dirty state before we initiate
# a checkout that could refuse or overwrite.
DIRTY=$(git -C "$BARE" status --porcelain)
if [ -n "$DIRTY" ]; then
  echo "Working tree at $BARE has uncommitted changes:"
  echo "$DIRTY"
  # AskUserQuestion: stash / cancel
  # On 'stash': git -C "$BARE" stash push -u -m "/sprint-work auto-stash <TS>"
  # On 'cancel': route to terminal
fi

CUR=$(git -C "$BARE" branch --show-current)
if [ "$CUR" != "$BRANCH" ]; then
  # Ask: switch to $BRANCH in $BARE? (yes / cancel)
  # On yes:
  #   - If $BRANCH already exists locally:  git -C "$BARE" checkout "$BRANCH"
  #     (Don't use -B. -B *resets* the branch pointer to current HEAD,
  #      destroying any commits the user has on that branch from prior work.)
  #   - If $BRANCH doesn't exist:  resolve base ref (upstream/origin), then
  #     git -C "$BARE" checkout -b "$BRANCH" "<resolved-base>"
  # On cancel: route to terminal
  :
fi
```

**Layout C — non-bare clone with upstream** (`IS_BARE=false` AND `HAS_UPSTREAM=true`): a developer doing fork-with-upstream workflow without bare-clone setup. Same handling as Layout B: the clone IS the workspace; switch the working tree to `$BRANCH` rather than creating a sibling worktree.

```bash
scripts/walk.sh set --state "$STATE" --key "worktree_paths.$ORG/$REPO" --value "$BARE"

# Validate state before any branch switch — symmetric with Layout A's
# existing-worktree validation. A user with uncommitted work in a
# sandbox-style repo should see the dirty state before we initiate
# a checkout that could refuse or overwrite.
DIRTY=$(git -C "$BARE" status --porcelain)
if [ -n "$DIRTY" ]; then
  echo "Working tree at $BARE has uncommitted changes:"
  echo "$DIRTY"
  # AskUserQuestion: stash / cancel
  # On 'stash': git -C "$BARE" stash push -u -m "/sprint-work auto-stash <TS>"
  # On 'cancel': route to terminal
fi

CUR=$(git -C "$BARE" branch --show-current)
if [ "$CUR" != "$BRANCH" ]; then
  # Ask: switch to $BRANCH in $BARE? (yes / cancel)
  # On yes:
  #   - If $BRANCH already exists locally:  git -C "$BARE" checkout "$BRANCH"
  #     (Don't use -B. -B *resets* the branch pointer to current HEAD,
  #      destroying any commits the user has on that branch from prior work.)
  #   - If $BRANCH doesn't exist:  resolve base ref (upstream/origin), then
  #     git -C "$BARE" checkout -b "$BRANCH" "<resolved-base>"
  # On cancel: route to terminal
  :
fi
```

For Layouts B and C, the bare-clone path *is* the workspace; only Layout A uses a sibling worktree path. This matches `/sprint-self-review`'s init logic exactly so both skills land worktree paths in the same place.

### Step 3: existing worktree(s) for the branch?

```bash
git -C "$BARE" worktree list --porcelain \
  | awk -v b="refs/heads/$BRANCH" '
      /^worktree /{p=$2}
      $0=="branch "b{print p}'
```

- **Zero results** → step 4 (create).
- **One result** → confirm with user: "Use existing worktree at `<path>`? (yes / cancel)". On yes, **validate state before storing** (see "Validate existing worktree" below). On valid, store and continue.
- **Multiple results** → prompt: "Found N worktrees for `<branch>`. Pick one or cancel." On pick, validate, store and continue. On cancel, route to terminal.

### Validate existing worktree

Before storing a reused worktree path, sanity-check it. Stale state from a prior crash silently rolls into the implementation phase otherwise:

```bash
# Confirm the worktree is on the right branch (worktree-list can show one
# branch while a different one is checked out after manual git ops):
ACTUAL=$(git -C "$WT" branch --show-current)
if [ "$ACTUAL" != "$BRANCH" ]; then
  bail "Worktree at $WT is on branch '$ACTUAL', expected '$BRANCH'. Resolve manually and re-run."
fi

# Confirm the working tree is clean. Uncommitted changes from a prior
# crash or interrupted run should surface for user decision before the
# implementation phase layers on top.
DIRTY=$(git -C "$WT" status --porcelain)
if [ -n "$DIRTY" ]; then
  echo "Worktree at $WT has uncommitted changes:"
  echo "$DIRTY"
  # AskUserQuestion: keep / stash / cancel
  # On 'keep': proceed with dirty state in place (user's call)
  # On 'stash': git -C "$WT" stash push -u -m "/sprint-work auto-stash $TS"
  # On 'cancel': route to terminal
fi
```

### Step 4: create the worktree (if none existed and user approves)

```bash
# Ask first:
#   "No worktree for <branch> in <org>/<repo>.
#    Create at <BARE>/<BRANCH>? (yes / no / cancel)"
```

- **yes** → resolve the base ref first, then create with **explicit path argument** to avoid git interpreting slash-bearing branches as paths and to avoid silently creating from local HEAD (which may be on the wrong base):

  ```bash
  # Resolve the intended base. Try upstream first (source-of-truth in
  # our workflow), then origin. Fetch so the local ref is current.
  DEFAULT_BASE=$(gh repo view "$ORG/$REPO" --json defaultBranchRef \
    -q '.defaultBranchRef.name')

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
- **no** → user wants to handle it manually. Print the explicit command they should run: `git -C $BARE worktree add "$BARE/$BRANCH" "$BRANCH"`, then route to terminal.
- **cancel** → route to terminal.

If `git worktree add` fails (branch in use elsewhere, conflicting paths), surface the error verbatim and route to terminal — don't try to recover automatically.

## Multi-repo

Iterate over all repos in the manifest. Batch the prompts where it makes sense (e.g., "Create worktree for `<branch>` in *both* `org/repo-a` *and* `org/repo-b`? (yes / pick per repo / cancel)") to reduce round-trips, but always honor a per-repo "no" or "cancel."

If the user cancels at any repo, route to terminal — don't leave the sprint half-set-up.

## Outputs

```bash
scripts/walk.sh set --state "$STATE" --key worktree_paths --value "<JSON: org/repo → absolute path>"
```

For `linear-walk`, `worktree_paths` may stay empty here; `implement` populates it per-issue.

## Outgoing edges

- **`worktree_ok`** → `detect-inflight`. Every repo in the manifest has a workable path (existing worktree confirmed, new worktree created with approval, or sandbox repo's checkout dir).
- **`worktree_missing`** → `terminal`. User cancelled, the bare clone is missing, or `git worktree add` failed. Diagnostics already printed.

Record exactly one:

```bash
# Ready:
scripts/walk.sh transition --state "$STATE" --from verify_worktree --to detect_inflight --condition worktree_ok

# Bail (user cancelled or unrecoverable):
scripts/walk.sh transition --state "$STATE" --from verify_worktree --to terminal --condition worktree_missing
```

## Notes

- **Cwd-independent.** This node never reads `pwd` to locate work. Everything resolves through `$BARE` paths derived from the manifest.
- **Ask before create.** The user always approves create-or-select. The skill performs the mechanical step; the user owns the decision. (Earlier the skill only printed instructions; the policy now is "ask, then act," which still preserves user control.)
- **Branch name carries across repos.** For a single branch unit (one Linear issue or one SPRINT.md sprint), the same `<branch>` is used in every repo. That's the tracking property — find this change set anywhere by its branch name.
- **For `linear-walk`**, this node is preflight: confirm bare clones exist, surface sandbox detection, but the per-issue worktree creation happens inside `implement`'s iteration so each issue gets its own branch unit.
