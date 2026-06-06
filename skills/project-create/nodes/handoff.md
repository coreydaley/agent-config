# Node: handoff

Print where everything landed. Nothing executed from here.

## Steps

```
Project scaffolded:

  Forgejo:   https://mac-mini.example:3000/projects/<slug>
  Wiki:      https://mac-mini.example:3000/projects/<slug>/wiki/Overview
  Clone:     ~/Code/mac-mini.example/projects/<slug>/
  Worktree:  ~/Code/mac-mini.example/projects/<slug>/main/

Next (nothing runs automatically):
  /feature-create   →  capture your first feature
```

No summary, no "let me know if you have questions."

## Outgoing edges

- → `terminal` (always)

```bash
scripts/walk.sh transition --state "$STATE" --from handoff --to terminal
```
