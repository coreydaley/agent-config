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

Lives at `~/Code/mac-mini.example/coreydaley/agent-config/` (source of truth: self-hosted Forgejo at `mac-mini.example`; auto-mirrored to public GitHub at `coreydaley/agent-config`).
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
from sprint_ledger import discover_reports_roots, get_reports_base  # etc.
```

Currently:
- `forgejo_sprints.py` — Forgejo-milestone-backed sprint tracking. **Both a library and a CLI** — the `sprint-*` skills call it directly (`python3 ~/.claude/lib/forgejo_sprints.py <flag>`); there is **no separate `sprints` skill** (removed — it was a thin wrapper, so the CLI was folded into this lib). **A sprint IS a Forgejo milestone** in its primary repo: open = active (`planned`/`in_progress`), closed = finished (`completed`/`skipped`); metadata (session, fine status, models, fit, participants, and the PRD section the sprint `Advances`) lives in a `## Sprint metadata` block in the milestone description. Owns the meta-block render/parse (pure, offline-tested), the `tea`/API operations, and the CLI (`--list`/`--current`/`--add`/`--get-doc`/`--append-retro`/`--set-fit`/`--complete`/…). Repo-less / cross-cutting sprints have no milestone home and aren't tracked. Replaced the on-disk `ledger.tsv`.
- `sprint_ledger.py` — retired as the sprint *tracker* (Forgejo milestones are now the source of truth). The TSV `SprintEntry`/`SprintLedger` model and `ledger.tsv` are **removed**; only the still-shared plumbing remains: `discover_reports_roots()` (repo discovery from `~/Reports/`, keyed on the `sprints/` dir, used by `forgejo_sprints.py`), `get_reports_base()` (the canonical `~/Reports/<org>/<repo>/` resolver), and the terminal color helpers used by the `commit` skill. (Filename kept for import stability; it no longer implements a ledger — a rename is a possible future cleanup.)
- `commit.py` — shared helpers for the `commit` skill.
- `graph_walker.py` — generic graph walker used by all dot-graph skills (see `docs/DOT-GRAPH-SKILL-PATTERN.md`). Reads a skill's `graph.dot`, validates transitions against the graph, and persists per-run state to a JSON file. Skills wrap it via their own `scripts/walk.sh`.
- `codex-invocation.md` — canonical pattern for `codex exec` invocations used in parallel-delegation nodes (sprint-plan, review-pr-comprehensive, and all audit-* skills via `audit-codex.sh`).
- `audit-runner.sh` — owns audit `$AUDIT_DIR` creation under `~/Reports/<org>/<repo>/audits/<TS>-<audit-name>/` and writes `MANIFEST.json`. Every audit skill's `init` node calls this; without it, no downstream node has a writable directory.
- `audit-codex.sh` — canonical `codex exec` wrapper used by every audit skill's `independent-reviews` and `devils-advocate` nodes. Owns the invocation flags AND post-run artifact verification; refuses to exit 0 unless the output file is on disk with at least one markdown table row.
- `audit-verify.sh` — the hard artifact gate every audit's `verify` node runs. Exits non-zero if any required artifact (claude.md, synthesis.md, REPORT.md) is missing or empty; the handoff message must include its output verbatim.
- `prd-runner.sh` — document-shaped analog of `audit-runner.sh` for the `audit-prd` skill. Resolves the PRD source (local markdown file, vault note, or Forgejo wiki page), fetches its content into `$AUDIT_DIR/prd-source.md`, resolves `<org>/<repo>` (wiki/in-repo file) or `prd/<slug>` (loose/vault file), and writes a MANIFEST the existing `audit-codex.sh`/`audit-verify.sh` consume unchanged.
- `external-content-handling.md` — copy-paste boilerplate that skills fetching untrusted external content (Forgejo, GitHub, web pages, etc.) include verbatim in their `SKILL.md`.
- `test_sprint_ledger.py` — unit tests for `sprint_ledger.py`.

## Skill patterns

Skills with multi-phase workflows (review pipelines, sprint planning, address-feedback loops) use the **dot-graph skill pattern**: the flow is a `graph.dot` with per-node markdown sidecars under `nodes/`, walked deterministically by `lib/graph_walker.py`. The graph is the source of truth — drift between prose and routing is structurally impossible. Reference: [`docs/DOT-GRAPH-SKILL-PATTERN.md`](docs/DOT-GRAPH-SKILL-PATTERN.md).

Skills currently on this pattern: `commit`, `polish-pull-request`, `review-address-feedback`, `review-pr-comprehensive`, `review-pr-simple`, `project-manage-prd`, `sprint-plan`, `sprint-plan-to-issues`, `sprint-seed`, `sprint-work`, all 30 `audit-*` skills (22 apple + 8 general/web). CLI-wrapper skills (`forgejo`, `gh`, `gws`, `obsidian`, `orbstack`) are not on this pattern — they're one-shot operations with no internal state machine.

## Sprint workflow

End-to-end lifecycle for planning, executing, and shipping work — including the SPRINT.md vs. Forgejo execution paths (commit-per-issue straight to the default branch, no PRs) and the artifact layout under `~/Reports/<org>/<repo>/`. See [`docs/sprints/README.md`](docs/sprints/README.md).

All sprint, review, and audit artifacts live under `~/Reports/<org>/<repo>/` (derived from `upstream` remote, falling back to `origin`). Nothing is written into the project repo.

## Subagents

Subagent definitions in `~/.claude/agents/` can be delegated work via the Agent tool.

## Multi-repo Claude integration (convention)

Multiple project repos can contribute skills, libs, commands, and agents to `~/.claude/`. Each repo owns its own contributions under a `claude-code/` subdirectory at repo root, and ships its own install script.

Layout convention per contributing repo:

```
<repo>/
├── claude-code/
│   ├── skills/          → symlinks into ~/.claude/skills/
│   ├── lib/             → symlinks into ~/.claude/lib/
│   ├── commands/        → symlinks into ~/.claude/commands/
│   ├── agents/          → symlinks into ~/.claude/agents/
│   ├── README.md        # what's here + install instructions
│   └── install.sh       # symlink + idempotent re-install
└── Makefile             # `make install` → calls claude-code/install.sh
```

Naming convention to avoid collisions across repos:
- `agent-config` owns generic verbs/topics: `audit-*`, `sprint-*`, `review-*`, `commit`, `forgejo`, `gh`, `obsidian`, `orbstack`.
- Project repos use a project prefix: `apt-*` for Agent Project Tracker, future apps follow the same pattern.
- If a collision ever occurs, last-installed wins via symlink replacement — easy to detect by listing `~/.claude/skills/`.

Each repo's `make install` is idempotent (safe to re-run after a `git pull`). Each repo also ships a `make uninstall` that removes only its own symlinks.

This pattern lets tools like Agent Project Tracker (and any future portfolio app with Claude integration) ship their skills alongside their server / CLI source, evolving together rather than across repo boundaries.

## Obsidian Vault

The vault lives at `~/Vault/` (symlinked from iCloud for backup). Refer to it as "the vault." Use the `obsidian` skill for all vault operations.

### Vault structure

The vault has top-level folders for `Ideas/`, `Knowledge/`, `Projects/`, `Drafts/`, `Tasks/`, and `Templates/`. Each folder has a corresponding `.base` file at the vault root that provides the table/board views for that folder.

### Project file naming convention

Each project lives in its own folder under `Projects/`. The hub document for a project is named `<ProjectName>.md` (matching the folder name), **not** `README.md`. This is so that the Projects base view's `file.name` column displays the actual project name rather than a sea of identical "README" rows.

Sub-files within a project folder follow the pattern `<ProjectName> — <aspect>.md` (em-dash separator) so they remain visually grouped and attributable to the project in listings. For example, within `Projects/QuorumForge/`, the hub is `QuorumForge.md` and sub-files might be `QuorumForge — demo scenario.md`, `QuorumForge — agent personas.md`, etc. If a project accumulates many sub-files, they can be moved into a sub-folder (e.g. `Projects/QuorumForge/notes/`) but the hub stays at `Projects/QuorumForge/QuorumForge.md`.

Links like `[[QuorumForge]]` from other notes resolve unambiguously to the hub file under this convention.

## Dotfiles

Lives at `~/Code/mac-mini.example/coreydaley/dotfiles/` (source of truth: self-hosted Forgejo at `mac-mini.example`; auto-mirrored to private GitHub at `coreydaley/dotfiles`).
Contains shell, git, ghostty, starship, and VSCode configs — symlinked to their system destinations via `make all`.

## Sandbox

Lives at `~/Code/mac-mini.example/coreydaley/sandbox/` (source of truth: self-hosted Forgejo at `mac-mini.example`; auto-mirrored to private GitHub at `coreydaley/sandbox`).
Scripts go in `scripts/`, experiments and POCs go in `projects/<n>/`. Run `make all` after cloning to install git hooks.

## Git

**NEVER commit or push git changes unless explicitly instructed to do so.** This is an absolute rule with no exceptions — do not commit "just to save progress", do not push after committing, do not assume that completing a task implies permission to commit. Always wait for an explicit instruction like "commit this" or "go ahead and push".

**Always clone repositories bare and use git worktrees.** When cloning a repo, use `git clone --bare <url> <dir>` and manage branches as worktrees via `git worktree add`.

**Organize repositories under `~/Code/<host>/<org>/<repo>/`.** For example, `~/Code/mac-mini.example/coreydaley/dotfiles/` (Forgejo, your default) or `~/Code/github.com/<owner>/<repo>/` (third-party GitHub clones). Always clone into this structure regardless of the host or org.

**For forked repositories, always configure the upstream remote.** After cloning a fork, add the original repo as `upstream` via `git remote add upstream <original-url>`.
