# Node: create

The skill's only mutation. Runs top-to-bottom; surface any error verbatim and
stop rather than continuing in a broken state.

## Inputs

```bash
SLUG=$(scripts/walk.sh get --state "$STATE" --key slug)
TITLE=$(scripts/walk.sh get --state "$STATE" --key title)
REPO_DESC=$(scripts/walk.sh get --state "$STATE" --key repo_description)
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
TOKEN=$(awk '/name: homelab/{f=1} f&&/token:/{print $2; exit}' \
  "$HOME/Library/Application Support/tea/config.yml")
BASE=https://mac-mini.example:3000/api/v1
ORG=projects
CLONE_ROOT="$HOME/Code/mac-mini.example/$ORG/$SLUG"
```

## Steps

### 1. Create the Forgejo repo

```bash
curl -sk -X POST -H "Authorization: token $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"$SLUG\",\"description\":\"$REPO_DESC\",\"private\":false,\"auto_init\":false}" \
  "$BASE/orgs/$ORG/repos"
```

Bail on error — if the repo already exists or org is wrong, surface it and stop.

### 2. Bare clone

```bash
git clone --bare "https://mac-mini.example:3000/$ORG/$SLUG.git" "$CLONE_ROOT/.bare"
echo "gitdir: ./.bare" > "$CLONE_ROOT/.git"
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
git add README.md .gitignore
git commit -m "chore: initial project scaffold

Co-authored-by: Claude <noreply@anthropic.com>"
git push -u origin HEAD:main
```

### 4. Set default branch to main

```bash
curl -sk -X PATCH -H "Authorization: token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"default_branch":"main"}' \
  "$BASE/repos/$ORG/$SLUG"
```

### 5. Create wiki Overview page

```bash
curl -sk -X POST -H "Authorization: token $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Overview\",\"content_base64\":\"$(base64 < "$SESSION_DIR/Overview.md")\"}" \
  "$BASE/repos/$ORG/$SLUG/wiki/new"
```

### 6. Persist results

```bash
REPO_URL="https://mac-mini.example:3000/$ORG/$SLUG"
scripts/walk.sh set --state "$STATE" --key repo_url    --value "$REPO_URL"
scripts/walk.sh set --state "$STATE" --key clone_path  --value "$CLONE_ROOT"
scripts/walk.sh set --state "$STATE" --key create_status --value "created"
```

## Outgoing edges

- → `handoff` (always — on any failure, surface verbatim and halt before transitioning)

```bash
scripts/walk.sh transition --state "$STATE" --from create --to handoff
```
