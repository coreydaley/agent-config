# Node: ask-create

The only mutation gate. Show what will be created, confirm before touching anything.

## Steps

Print a summary of what will happen:

```
Ready to scaffold this project?

  Repo:      projects/<slug>  on mac-mini.example
  Clone:     ~/Code/mac-mini.example/projects/<slug>/  (bare)
  Worktree:  ~/Code/mac-mini.example/projects/<slug>/main/
  Files:     README.md, .gitignore
  Wiki:      Overview page

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
