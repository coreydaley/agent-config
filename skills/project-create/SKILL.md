---
name: project-create
description: >-
  Guided back-and-forth discussion to shape a new project, then scaffold it in
  one shot: creates a private GitHub repo under `coreydaley` (via the `gh` CLI),
  bare-clones it to the standard local path, creates the `main` worktree,
  commits a README, an empty .gitignore, and a docs/Overview.md capturing the
  discussion output, then pushes. Two outcomes only — cancel (nothing created)
  or approve (full scaffold). Invoke via /project-create.
argument-hint: "[--help]"
disable-model-invocation: false
---

# Project Create

Guided discussion that shapes a new project and scaffolds it end-to-end.
Walks the graph in `graph.dot`, executing each node's prose from
`nodes/<id>.md`, until it reaches the terminal node.

Two outcomes:
- **Cancel** at any point → `terminal`, nothing touched.
- **Approve** at `ask-create` → full scaffold: GitHub repo, bare clone,
  main worktree, README, .gitignore, docs/Overview.md, push.

The creation step is the only mutation in the skill.

## Help mode

If `--help` or `-h` is in the arguments, print and stop:

```
/project-create — discuss and scaffold a new project.

What it does
  Shapes the project through conversation (slug, title, description, scope,
  known hard parts, open questions), drafts an Overview doc + repo
  description for review, then on approval:
    - Creates the private GitHub repo coreydaley/<slug> (via gh)
    - Bare-clones it to ~/Code/github.com/coreydaley/<slug>/
    - Creates the main worktree
    - Commits README.md + .gitignore + docs/Overview.md and pushes

Usage
  /project-create        # interactive, no args
  /project-create --help

Output (on approval)
  GitHub repo:   https://github.com/coreydaley/<slug>
  Overview doc:  ~/Code/github.com/coreydaley/<slug>/main/docs/Overview.md
  Local clone:   ~/Code/github.com/coreydaley/<slug>/

Next step (printed, not run)
  /feature-create   →  capture your first feature
```

## State machine

Eight nodes:

- **`init`** — init walker state.
- **`discuss`** — shape the project: slug, title, description, scope, known
  hard parts, open questions. Senior-peer tone, one question at a time.
- **`ask-wrap-up`** *(decision)* — draft it / keep going / cancel.
- **`draft`** — assemble Overview.md + repo description; render inline.
- **`ask-create`** *(decision)* — scaffold it / revise / cancel.
- **`create`** — the only mutation: GitHub repo + bare clone + worktree +
  README + .gitignore + docs/Overview.md + push.
- **`handoff`** — print URLs + next step.
- **`terminal`** — sink.

Edge conditions:
- `wrap_up_signaled`, `user_cancel` (from `discuss`)
- `user_wrap_up`, `user_continue`, `user_cancel` (from `ask-wrap-up`)
- `user_create`, `user_revise`, `user_cancel` (from `ask-create`)

## Walker semantics

Enforced by `scripts/walk.sh` wrapping `lib/graph_walker.py`. Read
`graph.dot` before starting. Never bypass the walker.

1. Start at `init` — call `scripts/walk.sh init` to create state file.
2. Read `nodes/<current>.md` for instructions.
3. Do the work. Evaluate outgoing edge conditions.
4. Record the transition with `scripts/walk.sh transition --from <id> --to <id> [--condition <label>]`.
5. Repeat until `terminal`.

## Transport

GitHub via the `gh` CLI (authenticated via `gh auth`, HTTPS). Repos are created
under `coreydaley` (private by default). Git operations run in the local shell.
Cross-ref the `gh` skill.

## Artifacts

```
$TMPDIR/.claude-walker/project-create/<TS>/
  Overview.md          # committed to the repo at docs/Overview.md
  README.md            # committed to the repo
  .walk-state.json     # walker state
```

## ARGUMENTS

$ARGUMENTS
