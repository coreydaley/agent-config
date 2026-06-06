# Node: draft

Assemble the Overview wiki doc and repo description from the discussion.
Render everything inline for review. Nothing is created yet.

## Inputs

```bash
SLUG=$(scripts/walk.sh get --state "$STATE" --key slug)
TITLE=$(scripts/walk.sh get --state "$STATE" --key title)
DESC=$(scripts/walk.sh get --state "$STATE" --key description)
SCOPE=$(scripts/walk.sh get --state "$STATE" --key scope)
HARD_PARTS=$(scripts/walk.sh get --state "$STATE" --key hard_parts)
OPEN_QS=$(scripts/walk.sh get --state "$STATE" --key open_qs)
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
```

## Steps

### 1. Repo description (one line)

Tight, plain text — shown in Forgejo repo listings. Max ~120 chars.
Persist: `scripts/walk.sh set --state "$STATE" --key repo_description --value "<text>"`

### 2. Overview wiki doc

Write `$SESSION_DIR/Overview.md`:

```markdown
# <Title>

<2-3 paragraph narrative: what this is, who it's for, why it's worth building.
Conversational, not formal. This is the north star you'll refer back to.>

## Scope

<What's in for now. What's explicitly out.>

## Known Hard Parts

<Anything technically uncertain or risky.>

## Open Questions

<Genuinely undecided things. Delete this section if there are none.>
```

### 3. README.md stub

Write `$SESSION_DIR/README.md`:

```markdown
# <Title>

<repo description — same one-liner as above>
```

### 4. Render inline

Print the repo description and full Overview.md to the user for review.

## Outgoing edges

- → `ask-create` (always)

```bash
scripts/walk.sh transition --state "$STATE" --from draft --to ask_create
```
