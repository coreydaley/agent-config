# Node: ask-create

The only mutation gate. Show what will be created, confirm before touching anything.

## Steps

Print a summary of what will happen:

```
Ready to scaffold this project?

  Repo:      coreydaley/<slug>  on GitHub (private)
  Clone:     ~/Code/github.com/coreydaley/<slug>/  (bare)
  Worktree:  ~/Code/github.com/coreydaley/<slug>/main/
  Files:     README.md, .gitignore, docs/Overview.md

  1. Scaffold it  — create everything above.
  2. Revise       — back to the discussion.
  3. Cancel       — do nothing.
```

Default conservative: prefer **Revise** when ambiguous. Scaffolding is reversible
but noisy to undo; one more exchange is cheap.

## Outgoing edges

- **`user_create`** → `create`
- **`user_revise`** → `discuss`
- **`user_cancel`** → `terminal`

```bash
scripts/walk.sh transition --state "$STATE" --from ask_create --to create   --condition user_create
scripts/walk.sh transition --state "$STATE" --from ask_create --to discuss  --condition user_revise
scripts/walk.sh transition --state "$STATE" --from ask_create --to terminal --condition user_cancel
```
