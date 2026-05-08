# Claude Code Instructions

## Response Style

- Be concise. Skip preamble, affirmations, and summaries of what you're about to do.
- No meta-commentary ("I'll now...", "Let me..."). Just act.
- Explain *why* only when the reason isn't obvious from context.
- Prefer code over prose when demonstrating a concept.
- Don't narrate tool use steps. Complete the task, report the result.
- Answer direct questions directly before any elaboration.

## About the User

- **Languages**: Go (primary), Python (secondary)
- **Stack**: Kubernetes, cloud-native infrastructure, containerization (Docker Desktop)
- **Databases**: SQLite for small/POC projects, PostgreSQL for production-grade work
- **Background**: 20+ years; deep OpenShift/Red Hat platform engineering experience; ISC2 CC certified; security-first mindset — flag security implications proactively
- **Testing**: Unit, integration, and e2e tests are a priority — always include appropriate test coverage
- **AI focus**: Agentic workflows and AI-assisted development — treat as a peer, not a beginner
- **Tooling preferences**: Skills over MCP; free/open source always preferred over proprietary; small focused tools over monolithic platforms; local-first where applicable
- **Design philosophy**: Declarative and explicit over hidden logic; iteration over perfection — propose and refine rather than over-engineering upfront
- **Approach**: Open source contributor; values understanding *why* not just *what*

## Commit Style

Use Conventional Commits for all git commits:

```
<type>(<scope>): <short summary>
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `style`, `ci`

- Summary: imperative mood, lowercase, no trailing period, max 72 chars
- Always include a `Co-authored-by:` trailer identifying the AI agent

## Code Conventions

- Prefer editing existing files over creating new ones
- Avoid over-engineering; implement only what is needed
- Do not add comments unless the logic is non-obvious
- Never commit secrets, credentials, or `.env` files

## Tools

Claude Code has access to file system tools (Read, Write, Edit, Glob, Grep), Bash, and browser tools. Use dedicated tools (Read, Edit, Glob) in preference to Bash equivalents.

## Memory

CLAUDE.md files are loaded hierarchically: `~/.claude/CLAUDE.md` (global) → project root → subdirectories. More specific files take precedence.

## Agent Config

Lives at `~/Code/github.com/coreydaley/agent-config/` (public GitHub repo: `coreydaley/agent-config`).
Contains CLAUDE.md, commands, lib, skills, and subagents — all symlinked into `~/.claude/` via `make all`.

## Skills

Skills in `~/.claude/skills/` are auto-discovered. Each skill has a `SKILL.md` with YAML frontmatter describing when it applies.

## Commands

Custom slash commands live in `~/.claude/commands/`. Invoke with `/command-name`.

## Lib

Shared Python libraries live in `~/.claude/lib/` (symlinked from `agent-config/lib/`). Scripts under `skills/` and `commands/` import from here to share schemas and utilities without duplication. Scripts add the lib path via:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".claude" / "lib"))
from sprint_ledger import SprintEntry, SprintLedger, get_ledger_path  # etc.
```

Currently:
- `sprint_ledger.py` — shared data model and display helpers for the sprint ledger, used by the `sprints` skill and the `commit` skill.
- `commit.py` — shared helpers for the `commit` skill.
- `graph_walker.py` — generic graph walker used by all dot-graph skills (see `docs/DOT-GRAPH-SKILL-PATTERN.md`). Reads a skill's `graph.dot`, validates transitions against the graph, and persists per-run state to a JSON file. Skills wrap it via their own `scripts/walk.sh`.
- `codex-invocation.md` — canonical pattern for `codex exec` invocations used in parallel-delegation nodes (sprint-plan, review-pr-comprehensive, sprint-self-review, audit-* subagents).
- `external-content-handling.md` — copy-paste boilerplate that skills fetching untrusted external content (Linear, GitHub, web pages, etc.) include verbatim in their `SKILL.md`.
- `test_sprint_ledger.py` — unit tests for `sprint_ledger.py`.

## Skill patterns

Skills with multi-phase workflows (review pipelines, sprint planning, address-feedback loops) use the **dot-graph skill pattern**: the flow is a `graph.dot` with per-node markdown sidecars under `nodes/`, walked deterministically by `lib/graph_walker.py`. The graph is the source of truth — drift between prose and routing is structurally impossible. Reference: [`docs/DOT-GRAPH-SKILL-PATTERN.md`](docs/DOT-GRAPH-SKILL-PATTERN.md).

Skills currently on this pattern: `commit`, `polish-pull-request`, `review-address-feedback`, `review-pr-comprehensive`, `review-pr-simple`, `sprint-plan`, `sprint-plan-to-linear`, `sprint-seed`, `sprint-self-review`, `sprint-work`. CLI-wrapper skills (`gh`, `gws`, `linear`, `obsidian`, `orbstack`) are not on this pattern — they're cheat sheets for one-shot operations with no internal state machine.

## Sprint workflow

End-to-end lifecycle for planning, executing, reviewing, and shipping work — including the SPRINT.md vs. Linear execution paths, the self-review cycle, and the artifact layout under `~/Reports/<org>/<repo>/`. See [`docs/sprints/README.md`](docs/sprints/README.md).

All sprint, review, and audit artifacts live under `~/Reports/<org>/<repo>/` (derived from `upstream` remote, falling back to `origin`). Nothing is written into the project repo.

## Subagents

Subagent definitions in `~/.claude/agents/` can be delegated work via the Agent tool.

## Obsidian Vault

The vault lives at `~/Vault/` (symlinked from iCloud for backup). Refer to it as "the vault." Use the `obsidian` skill for all vault operations.

### Vault structure

The vault has top-level folders for `Ideas/`, `Knowledge/`, `Projects/`, `Drafts/`, `Tasks/`, and `Templates/`. Each folder has a corresponding `.base` file at the vault root that provides the table/board views for that folder.

### Project file naming convention

Each project lives in its own folder under `Projects/`. The hub document for a project is named `<ProjectName>.md` (matching the folder name), **not** `README.md`. This is so that the Projects base view's `file.name` column displays the actual project name rather than a sea of identical "README" rows.

Sub-files within a project folder follow the pattern `<ProjectName> — <aspect>.md` (em-dash separator) so they remain visually grouped and attributable to the project in listings. For example, within `Projects/QuorumForge/`, the hub is `QuorumForge.md` and sub-files might be `QuorumForge — demo scenario.md`, `QuorumForge — agent personas.md`, etc. If a project accumulates many sub-files, they can be moved into a sub-folder (e.g. `Projects/QuorumForge/notes/`) but the hub stays at `Projects/QuorumForge/QuorumForge.md`.

Links like `[[QuorumForge]]` from other notes resolve unambiguously to the hub file under this convention.

## Dotfiles

Lives at `~/Code/github.com/coreydaley/dotfiles/` (private GitHub repo: `coreydaley/dotfiles`).
Contains shell, git, ghostty, starship, and VSCode configs — symlinked to their system destinations via `make all`.

## Sandbox

Lives at `~/Code/github.com/coreydaley/sandbox/` (private GitHub repo: `coreydaley/sandbox`).
Scripts go in `scripts/`, experiments and POCs go in `projects/<n>/`. Run `make all` after cloning to install git hooks.

## Git

**NEVER commit or push git changes unless explicitly instructed to do so.** This is an absolute rule with no exceptions — do not commit "just to save progress", do not push after committing, do not assume that completing a task implies permission to commit. Always wait for an explicit instruction like "commit this" or "go ahead and push".

**Always clone repositories bare and use git worktrees.** When cloning a repo, use `git clone --bare <url> <dir>` and manage branches as worktrees via `git worktree add`.

**Organize repositories under `~/Code/<host>/<org>/<repo>/`.** For example, `~/Code/github.com/coreydaley/dotfiles/`. Always clone into this structure regardless of the host or org.

**For forked repositories, always configure the upstream remote.** After cloning a fork, add the original repo as `upstream` via `git remote add upstream <original-url>`.
