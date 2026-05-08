# Skill Design Principles

Reference material for `skill-creator`. Skills that follow these principles age well; skills that violate them rot fast. Read this in `discuss-skill` (to set freedom expectations) and again in `write-graph`/`write-cli-wrapper` (to keep authoring honest).

## Context is a scarce resource

Every skill description Claude loads displaces something else. Skills share the context window with: the system prompt, conversation history, other skills' metadata, file contents, tool results, and the actual user request.

**Default assumption: Claude is already smart.** Only add context Claude doesn't already have or can't easily derive. For each paragraph in `SKILL.md`, ask: would a competent engineer need this stated explicitly, or can they infer it? If the answer is "infer it," cut the paragraph.

This isn't a license to be cryptic. Procedural knowledge that's genuinely non-obvious — the order of operations for an irreversible step, a subtle invariant, a hidden constraint — earns its space. Generic prose that any model could produce does not.

## Degrees of freedom

Match the level of specificity to the task's fragility. Think of Claude as exploring a path: a narrow bridge with cliffs needs guardrails; an open field allows many routes.

| Freedom | When to use | What the skill provides |
|---|---|---|
| **Low** | Operations are fragile, side effects are destructive, or consistency is critical | Specific scripts with few parameters; exact command sequences |
| **Medium** | A preferred pattern exists; some variation is acceptable | Pseudocode, parameterized scripts, named templates |
| **High** | Many valid approaches; decisions depend on context | Prose instructions, heuristics, principles |

Most skills are mixed: high freedom in the planning/discussion phases (the user shapes the work), low freedom at the destructive boundary (the commit, the push, the deletion). The dot-graph pattern lets a single skill mix these naturally — discussion nodes carry prose, action nodes carry scripts.

## Progressive disclosure

Skills load in layers. Each layer has a budget.

| Layer | What it is | Budget |
|---|---|---|
| 1 | `name` + `description` (frontmatter) | ~100 words; always in context |
| 2 | `SKILL.md` body | <500 lines; loaded when the skill triggers |
| 3 | `references/` and `nodes/` | Loaded on demand by Claude as needed |

A skill that puts everything in `SKILL.md` makes Layer 2 expensive every time it triggers, even when the work doesn't need the deeper material. A skill that pushes detail into `references/` keeps Layer 2 lean and lets Layer 3 load only when relevant.

**Rules of thumb:**

- Keep `SKILL.md` body to the essentials. If it's pushing 500 lines, push variants/details into `references/`.
- For graph-driven skills, the per-node `nodes/<id>.md` files are Layer 3 — they load only when the walker arrives at that node. Use them aggressively for node-specific procedure.
- One reference per topic. Avoid `references/foo/bar/baz.md` — keep references one level deep so Claude can see the full reference set from `SKILL.md` at a glance.

## Description quality

The `description` field is the only thing Claude reads to decide when a skill triggers. Bad descriptions fail to fire when needed; good ones include both *what* the skill does and *when* to use it.

A bad description (too generic, no triggers):
```yaml
description: GitHub operations.
```

A good description (verbs + concrete trigger phrases):
```yaml
description: |
  Use this skill when the user asks to work with GitHub. Covers cloning
  and forking repos, configuring remotes, adding worktrees, plus all `gh`
  CLI operations (creating or reviewing PRs, managing issues, checking
  CI/CD status, viewing repo info, managing releases). Trigger phrases
  include "github", "clone", "fork", "set up the repo", "add worktree",
  "open a PR", "create issue", "check CI", "merge PR", "list issues",
  "gh pr", "gh issue", "gh repo", "gh run".
```

The triggers list is load-bearing. Without it, the description still tells Claude what the skill does, but not when to fire it.

## What to leave out of a skill

A skill should contain only what a downstream Claude instance needs to do the job. Do not write:

- `README.md` — meta-documentation belongs in repo `docs/`, not in the skill
- `CHANGELOG.md` — version history is git's job
- `INSTALLATION_GUIDE.md` — setup belongs in the repo `README.md` or `docs/`
- `QUICK_REFERENCE.md` — that's what `references/` is for, named by topic

Skills are operational artifacts. Auxiliary documentation around them is clutter that displaces useful context.

## Anatomy of a skill

Every skill has `SKILL.md`. Most skills add at least one of `scripts/`, `references/`, or `assets/`. Graph-driven skills add `graph.dot` + `nodes/`.

```
skill-name/
├── SKILL.md                  # required: frontmatter + body
├── graph.dot                 # graph-driven only
├── graph.svg                 # graph-driven only (rendered)
├── nodes/                    # graph-driven only: per-node prose
│   └── <id>.md
├── scripts/                  # optional: deterministic code
│   └── walk.sh / render.sh / validate.py (graph-driven)
├── references/               # optional: docs loaded on demand
│   └── <topic>.md
└── assets/                   # optional: files used in skill output
    └── <template>.<ext>
```

| Subdir | Purpose | When to include |
|---|---|---|
| `scripts/` | Executable code that Claude runs | Deterministic operations, repetitive code, fragile sequences |
| `references/` | Docs Claude reads on demand | Schemas, command tables, framework-specific patterns |
| `assets/` | Files used in skill output | Templates, icons, fonts, boilerplate that gets copied |

Scripts and assets differ in trust model: scripts may run, assets get embedded in output. Don't conflate them.

## Iteration is the workflow

Skills are not designed-then-frozen artifacts. They evolve. The iteration cycle:

1. Use the skill on real tasks.
2. Notice friction: surprising failures, repeated corrections, gaps the user has to fill in.
3. Identify whether the fix belongs in `SKILL.md`, `nodes/<id>.md`, `references/`, or scripts.
4. Update and re-test.

The dot-graph pattern shines here: changes to a node's prose are localized to one file, and the walker enforces routing so structural changes can't silently break the contract.

CLI-wrapper skills iterate primarily through the `description` (when does it trigger?) and the command examples (what does the user actually need?). Graph-driven skills iterate through node prose and, occasionally, topology adjustments — adding a missing gate, splitting an overgrown node, adding a back-edge for a previously-unmodeled retry path.

## When the dot-graph pattern doesn't fit

The pattern earns its overhead when a skill has 5+ phases, user-input gates, loops, conditional branches, or per-run artifacts. It's overkill when:

- The skill is a thin CLI wrapper (`gh`, `gws`, `linear`). Cheat sheet, not state machine.
- The skill is a single-prompt formatter (the user pipes content in, skill returns content out).
- The work is open-ended chat with no discrete phases.

A useful test: if you'd be tempted to write `SKILL.md` as a flowchart anyway, the dot-graph pattern fits. If `SKILL.md` would be a list of independent commands, leave it procedural.
