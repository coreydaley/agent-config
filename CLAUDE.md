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
Contains CLAUDE.md, commands, skills, and subagents — all symlinked into `~/.claude/` via `make all`.

## Skills

Skills in `~/.claude/skills/` are auto-discovered. Each skill has a `SKILL.md` with YAML frontmatter describing when it applies.

## Commands

Custom slash commands live in `~/.claude/commands/`. Invoke with `/command-name`.

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
