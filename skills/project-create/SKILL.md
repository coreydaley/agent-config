---
name: project-create
description: >-
  Guided back-and-forth discussion to shape a new project, then scaffold it in
  one shot: creates a Forgejo repo under the `projects` org, bare-clones it to
  the standard local path, creates the `main` worktree, commits a README and
  empty .gitignore, pushes, and creates a wiki Overview page capturing the
  discussion output. Two outcomes only — cancel (nothing created) or approve
  (full scaffold). Invoke via /project-create.
argument-hint: "[--help]"
disable-model-invocation: false
---

# Project Create

Guided discussion that shapes a new project and scaffolds it end-to-end.
Walks the graph in `graph.dot`, executing each node's prose from
`nodes/<id>.md`, until it reaches the terminal node.

Two outcomes:
- **Cancel** at any point → `terminal`, nothing touched.
- **Approve** at `ask-create` → full scaffold: Forgejo repo, bare clone,
  main worktree, README, .gitignore, push, wiki Overview.

The creation step is the only mutation in the skill.

## Help mode

If `--help` or `-h` is in the arguments, print and stop:

```
/project-create — discuss and scaffold a new project.

What it does
  Shapes the project through conversation (slug, title, description, scope,
  known hard parts, open questions), drafts a wiki Overview doc + repo
  description for review, then on approval:
    - Creates the Forgejo repo under projects/<slug>
    - Bare-clones it to ~/Code/mac-mini.example/projects/<slug>/
    - Creates the main worktree
    - Commits README.md + .gitignore and pushes
    - Creates the wiki Overview page

Usage
  /project-create        # interactive, no args
  /project-create --help

Output (on approval)
  Forgejo repo:  https://mac-mini.example:3000/projects/<slug>
  Wiki Overview: https://mac-mini.example:3000/projects/<slug>/wiki/Overview
  Local clone:   ~/Code/mac-mini.example/projects/<slug>/

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
- **`create`** — the only mutation: Forgejo repo + bare clone + worktree +
  README + .gitignore + push + wiki Overview.
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

Forgejo at `https://mac-mini.example:3000` via `curl -sk` (self-signed
TLS) and the `tea` CLI (login alias `homelab`). Token extracted from the tea
config in `create` node. Git operations run in the local shell.

## Artifacts

```
$TMPDIR/.claude-walker/project-create/<TS>/
  Overview.md          # wiki page draft (ephemeral; wiki is canonical)
  README.md            # committed to the repo
  .walk-state.json     # walker state
```

## ARGUMENTS

$ARGUMENTS
