# Claude Code Instructions

## Response Style

- Be concise. Skip preamble, affirmations, and summaries of what you're about to do.
- No meta-commentary ("I'll now...", "Let me..."). Just act.
- Explain *why* only when the reason isn't obvious from context.
- Prefer code over prose when demonstrating a concept.
- Don't narrate tool use steps. Complete the task, report the result.
- Answer direct questions directly before any elaboration.

## Time is money: parallelize

- If work can be done **cheaply in parallel**, do it by default: concurrent API calls in a script (a thread pool, `xargs -P`), parallel tool calls, background runs while doing other work, independent subagents. Don't take the slow sequential route because it's the first one that comes to mind.
- If the parallel route is **costly or risky** (many subagents, a big token spend, or a chance of hitting API rate limits or overloading a shared machine), ask first, and offer both options with rough time and cost for each. Don't silently default to the slow one.
- Before a long-running job, estimate how long it will take. If it's more than a few minutes, say so and offer the faster way.

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

### Apple StoreKit tests need the GUI launchd domain (any project with `SKTestSession`)

`SKTestSession`-backed StoreKit tests only work in the **logged-in GUI launchd domain**. Running `xcodebuild test` through the **Bash tool** (a non-GUI launchd domain) makes transactions come back `.unverified` with an empty `Transaction.currentEntitlements`, so every "buy → owned" entitlement test fails while "not owned" cases pass — it *looks* like a code bug but is not. They pass in **Xcode ⌘U** and on a **GUI-session runner** (e.g. the `xcuitest-on-mini` skill, which uses `launchctl asuser`). **Never trust a Bash `xcodebuild test` result for `SKTestSession` entitlement tests** — run them via ⌘U or a GUI-domain runner, and keep them serial (`@Suite(.serialized)` + a non-parallelizable test target, since the StoreKit test env is process-global per-user). A corrupt local StoreKit agent (transactions unverified even in the GUI domain) is fixed by quitting Xcode, `rm -rf ~/Library/Caches/com.apple.storekitagent`, and rebooting. Don't dismiss these reds as "environmental noise" — diagnose the domain.

## Memory

CLAUDE.md files are loaded hierarchically: `~/.claude/CLAUDE.md` (global) → project root → subdirectories. More specific files take precedence.

## Agent Config

Lives in the **agent-config** repo (`~/Code/github.com/coreydaley/agent-config/`; GitHub `coreydaley/agent-config` is the source of truth). Contains CLAUDE.md, settings.json, commands, lib, skills, and subagents — all symlinked into `~/.claude/` via `make all`. **The repo is public**: its pre-commit/pre-push hooks (`make hooks`) run gitleaks and `scripts/check-personal-info.py` (hostnames, private IPs, emails, phone numbers, home paths, plus a private denylist at `~/.config/agent-config/denylist`). Never put secrets, personal details, or machine-specific values (hostnames, usernames) in it — read them from environment variables set in the private dotfiles instead.

## Skills

Skills in `~/.claude/skills/` are auto-discovered. Each skill has a `SKILL.md` with YAML frontmatter describing when it applies.

## Commands

Custom slash commands live in `~/.claude/commands/`. Invoke with `/command-name`.

## Lib

Shared libraries live in `~/.claude/lib/` (symlinked from `agent-config/lib/`). Skills that need them add the lib path via:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".claude" / "lib"))
from graph_walker import ...  # etc.
```

Currently:
- `graph_walker.py` — generic graph walker used by all dot-graph skills (see `docs/DOT-GRAPH-SKILL-PATTERN.md`). Reads a skill's `graph.dot`, validates transitions against the graph, and persists per-run state to a JSON file. Skills wrap it via their own `scripts/walk.sh`.
- `audit-runner.sh` — owns audit `$AUDIT_DIR` creation under `~/Reports/<org>/<repo>/audits/<TS>-<audit-name>/` and writes `MANIFEST.json`. Every audit skill's `init` node calls this; without it, no downstream node has a writable directory.
- `audit-verify.sh` — the hard artifact gate every audit's `verify` node runs. Exits non-zero if any required artifact (claude.md, synthesis.md, REPORT.md) is missing or empty; the handoff message must include its output verbatim.
- `external-content-handling.md` — copy-paste boilerplate that skills fetching untrusted external content (GitHub, web pages, etc.) include verbatim in their `SKILL.md`.
- `agent-roles.md` — single-provider, multiple-role review contract: which `subagents/` role (`independent-reviewer`, `adversarial-reviewer`, `synthesizer`, `devils-advocate`, `adjudicator`, `defender`, `verifier`) judges what, and how to brief it.
- `pr-artifacts.md`, `pr-discipline.md`, `code-hygiene.md`, `paths.py` — the `pr-*` family's shared layout and PLAN.md schema, scope/sizing/ceremony rules, comment/test/commit rules, and `~/Reports/<org>/<repo>` resolver.

## Skill patterns

Skills with multi-phase workflows (review pipelines, feature planning, address-feedback loops) use the **dot-graph skill pattern**: the flow is a `graph.dot` with per-node markdown sidecars under `nodes/`, walked deterministically by `lib/graph_walker.py`. The graph is the source of truth — drift between prose and routing is structurally impossible. Reference: [`docs/DOT-GRAPH-SKILL-PATTERN.md`](docs/DOT-GRAPH-SKILL-PATTERN.md).

Skills currently on this pattern: `commit`, `pr-plan`, `pr-build`, `pr-review`, `pr-fix`, `pr-polish`, `review-design`, `feature-create`, `feature-plan`, `feature-work`, all 30 `audit-*` skills (22 apple + 8 general/web). CLI-wrapper skills (`gh`, `gws`, `obsidian`, `orbstack`) are not on this pattern — they're one-shot operations with no internal state machine.

## Feature workflow

End-to-end lifecycle for capturing, planning, and building work as a **feature** — a GitHub issue (`type/feature` label) whose body is the spec, grounded in the repo README (no PRD, no milestone). Three skills compose: `/feature-create` captures the feature issue, `/feature-plan` decomposes it into native GitHub sub-issues ordered by native blocked-by dependencies, and `/feature-work` builds those sub-issues on a `feature/<slug>` branch — one commit per sub-issue with `Closes #N`, pushed but not merged. The user merges by hand later (which fires each `Closes #N` and closes the sub-issues), then closes the feature.

## PR workflow

The single-PR track, for one issue → one branch → one PR: `/pr-plan` (approved PLAN.md) → `/pr-build` (one commit per task, draft PR) → `/pr-review` (multi-role review) → `/pr-fix` / `/pr-address` (scope-triaged fixes and replies) → `/pr-polish` (final body, threads, history). `/review-design` attacks a design before it's built. Every judgment runs in a fresh role subagent (`lib/agent-roles.md`); artifacts live under `~/Reports/<org>/<repo>/prs/<key>/`. Guide: [`docs/PR-WORKFLOW.md`](docs/PR-WORKFLOW.md).

All feature, review, and audit artifacts live under `~/Reports/<org>/<repo>/` (derived from `upstream` remote, falling back to `origin`). Nothing is written into the project repo.

## Issue triage labels & sweep convention (all projects)

Across every project (all on GitHub), issues carry three **orthogonal** label axes. Keep them distinct — never collapse one into another:

- **`priority/*`** (`p0` / `p1` / `defer`) — the audit's/filer's severity. Set at filing; don't change it during work — it's the original triage.
- **`size/*`** (`S` / `M` / `L` / `XL`) — the **effort estimate, applied at work-time, never at creation.** Size is only knowable once you've dug into the issue, so estimating it at filing is guessing. Pure information.
- **`deferred/<reason>`** — the "**parked — don't auto-pick**" decision *and why*. This is the actionable sweep gate. Reasons:
  - `deferred/needs-manual` — needs a human at the keyboard (live VoiceOver, on-device/UI testing, code-signing, App Review, anything the agent can't drive or verify).
  - `deferred/scale-gated` — premature; revisit only when a stated threshold is crossed (record the threshold in the issue).
  - `deferred/too-big` — tabled on effort; needs a dedicated push (usually pairs with `size/L`+).
  - `deferred/blocked-upstream` — waiting on a third party / dependency.

A fourth, terminal axis sits alongside these:

- **`wontfix`** (flat) — applied **at close time** to an issue we've decided NOT to do *ever* (out of scope, by design, obsolete, duplicate). It marks a *closed* issue as rejected rather than fixed, so "what did we decide against?" is filterable. Distinct from `deferred/*`, which stays **open** for later — `deferred/*` is "not now," `wontfix` is "not ever." The close comment carries the specific why.

**Why this exists:** when a sweep surfaces an issue, we dig in; if we decide *not now*, we must mark it (`size/*` and/or `deferred/<reason>`) so it doesn't look like a fresh untouched issue. Otherwise the same big/blocked issue gets re-picked and re-litigated every sweep.

**Sweep queries:**
- Active queue (what gets auto-picked): **open AND NOT `deferred/*`**.
- Set up for manual work / VoiceOver / device: query **`deferred/needs-manual`**.
- Crossed a scale threshold: query **`deferred/scale-gated`**.
- Dedicated big-ticket session: query **`deferred/too-big`** / `size/XL`.

The label set is per-repo (create the `size/*` and `deferred/*` labels on a project the first time the convention is used there). Project CLAUDE.md files may record that project's current parked list, but the convention itself lives here.

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
- The core Claude config (`agent-config`) owns generic verbs/topics: `audit-*`, `feature-*`, `review-*`, `commit`, `gh`, `obsidian`, `orbstack`.
- Project repos use a project prefix: `apt-*` for Agent Project Tracker, future apps follow the same pattern.
- If a collision ever occurs, last-installed wins via symlink replacement — easy to detect by listing `~/.claude/skills/`.

Each repo's `make install` is idempotent (safe to re-run after a `git pull`). Each repo also ships a `make uninstall` that removes only its own symlinks.

This pattern lets tools like Agent Project Tracker (and any future portfolio app with Claude integration) ship their skills alongside their server / CLI source, evolving together rather than across repo boundaries.

## Dotfiles

Lives at `~/Code/github.com/coreydaley/dotfiles/` (GitHub `coreydaley/dotfiles` is the source of truth).
Contains shell, git, ghostty, starship, and VSCode configs — symlinked to their system destinations via `make all`.

## Sandbox

Lives at `~/Code/github.com/coreydaley/sandbox/` (GitHub `coreydaley/sandbox` is the source of truth).
Scripts go in `scripts/`, experiments and POCs go in `projects/<n>/`. Run `make all` after cloning to install git hooks.

## Git

**NEVER commit or push git changes unless explicitly instructed to do so.** This is an absolute rule with no exceptions — do not commit "just to save progress", do not push after committing, do not assume that completing a task implies permission to commit. Always wait for an explicit instruction like "commit this" or "go ahead and push".

**Always clone repositories bare and use git worktrees.** When cloning a repo, use `git clone --bare <url> <dir>` and manage branches as worktrees via `git worktree add`.

**Organize repositories under `~/Code/<host>/<org>/<repo>/`.** For example, `~/Code/github.com/coreydaley/dotfiles/` (your own repos) or `~/Code/github.com/<owner>/<repo>/` (third-party GitHub clones). Always clone into this structure regardless of the host or org.

**For forked repositories, always configure the upstream remote.** After cloning a fork, add the original repo as `upstream` via `git remote add upstream <original-url>`.

**Remote protocol: HTTPS for GitHub.** GitHub remotes use **HTTPS** (`https://github.com/<owner>/<repo>.git`) — `gh auth` installs an HTTPS credential helper, so HTTPS authenticates via the gh token with no SSH key in the loop; this is GitHub's default and the consistent choice for a gh-centric workflow. All active repos (agent-config, dotfiles, sandbox, mac-mini, coreydaley-dev, purrchiver, secretstore, swift-kits) use GitHub `origin` over HTTPS and are the single source of truth.
