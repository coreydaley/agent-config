# Node: create

The skill's only mutation. Runs top-to-bottom; surface any error verbatim and
stop rather than continuing in a broken state.

GitHub operations use the `gh` CLI (authenticated via `gh auth`, HTTPS). Git
operations run in the local shell. Cross-ref the `gh` skill.

## Inputs

```bash
SLUG=$(scripts/walk.sh get --state "$STATE" --key slug)
TITLE=$(scripts/walk.sh get --state "$STATE" --key title)
REPO_DESC=$(scripts/walk.sh get --state "$STATE" --key repo_description)
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
OWNER=coreydaley
CLONE_ROOT="$HOME/Code/github.com/$OWNER/$SLUG"
```

## Steps

### 1. Create the GitHub repo

```bash
gh repo create "$OWNER/$SLUG" --private --description "$REPO_DESC"
```

Default visibility is **private** (matches the user's other repos). Do NOT use
`gh`'s auto-clone — the bare clone in the next step is the canonical local copy.
Bail on error — if the repo already exists, surface it and stop.

### 2. Bare clone

```bash
git clone --bare "https://github.com/$OWNER/$SLUG.git" "$CLONE_ROOT/.bare"
echo "gitdir: ./.bare" > "$CLONE_ROOT/.git"
git -C "$CLONE_ROOT/.bare" config remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'
```

### 3. Create main worktree + initial commit

```bash
cd "$CLONE_ROOT"
git worktree add main
cd main
# README.md
cp "$SESSION_DIR/README.md" README.md
# .gitignore
touch .gitignore
# docs/Overview.md
mkdir -p docs
cp "$SESSION_DIR/Overview.md" docs/Overview.md
git add README.md .gitignore docs/Overview.md
git commit --no-gpg-sign -m "chore: initial project scaffold

Co-authored-by: Claude <noreply@anthropic.com>"
git push -u origin HEAD:main
```

### 4. Set default branch to main

```bash
gh repo edit "$OWNER/$SLUG" --default-branch main
```

### 5. Persist results

```bash
REPO_URL="https://github.com/$OWNER/$SLUG"
scripts/walk.sh set --state "$STATE" --key repo_url    --value "$REPO_URL"
scripts/walk.sh set --state "$STATE" --key clone_path  --value "$CLONE_ROOT"
scripts/walk.sh set --state "$STATE" --key create_status --value "created"
```

## Outgoing edges

- → `handoff` (always — on any failure, surface verbatim and halt before transitioning)

```bash
scripts/walk.sh transition --state "$STATE" --from create --to handoff
```
