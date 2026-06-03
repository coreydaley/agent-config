# agent-config

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/coreydaley/agent-config)](https://github.com/coreydaley/agent-config/issues)

A personal configuration repository for [Claude Code](https://claude.ai/code) — managing instructions, skills, commands, and subagents in one place, version-controlled and symlinked into `~/.claude/`.

> **Security notice:** The contents of this repository flow directly into Claude's system prompt. Review all files before use, and never commit secrets or credentials. A `gitleaks` pre-commit hook is included to help catch leaks before they happen.

## What's in here

| Path | Purpose |
|---|---|
| `CLAUDE.md` | Global instructions loaded by Claude Code on every session |
| `settings.json` | Global Claude Code settings (permissions, hooks, statusline, model, theme) |
| `commands/` | Custom slash commands (invoke with `/command-name`) |
| `skills/` | Reusable skill modules auto-discovered by Claude Code |
| `subagents/` | Specialized agents Claude can delegate work to |
| `lib/` | Shared Python libraries imported by skills and commands |
| `docs/` | Workflow documentation |
| `scripts/` | Setup scripts |

## Setup

```bash
git clone https://github.com/coreydaley/agent-config.git
cd agent-config
brew install gitleaks
make all
```

`make all` creates symlinks into `~/.claude/` and installs the gitleaks pre-commit hook. It is idempotent — safe to run multiple times.

### What gets symlinked

```
CLAUDE.md       → ~/.claude/CLAUDE.md
settings.json   → ~/.claude/settings.json
commands/       → ~/.claude/commands/
skills/         → ~/.claude/skills/
subagents/      → ~/.claude/agents/
lib/            → ~/.claude/lib/
```

Existing files at symlink destinations are backed up with a `.old` extension before replacement.

### Individual targets

```bash
make symlinks   # Create ~/.claude/ symlinks only
make hooks      # Install gitleaks pre-commit hook only
make help       # Show all available targets
```

## Commands

Invoke with `/command-name` in Claude Code. Commands with `disable-model-invocation` must be called explicitly; others may also trigger automatically based on context.

| Command | Description |
|---|---|
| `/commit` | Analyze uncommitted changes and create grouped conventional commits |
| `/tag` | Analyze commits since last tag and propose the next semantic version |
| `/project-create-prd` | Guided, Socratic authoring (or revision) of a project's PRD; publishes it to the repo's Forgejo wiki |
| `/sprint-seed` | Pre-plan exploratory discussion; produces a `SEED.md` (auto-reads the repo's PRD to ground candidates) |
| `/sprint-plan` | Multi-agent collaborative sprint planning |
| `/sprint-plan-to-issues` | Decompose an existing sprint milestone into one Forgejo issue per task |
| `/sprint-work` | Execute a planned sprint end-to-end, autonomously — one commit per issue on the default branch (no PRs) |
| `/review-pr-simple` | Single-agent PR review → `REVIEW.md` |
| `/review-pr-comprehensive` | Dual-agent PR review (Claude + Codex) → `REVIEW.md` |
| `/review-address-feedback` | Walk through review feedback and apply fixes |
| `/polish-pull-request` | Final-pass PR cleanup before merge |
| **Audits** (all 5-phase dual-agent dot-graph skills — structurally gated $AUDIT_DIR / codex / verify via `lib/audit-*.sh`) | |
| `/audit-architecture` | Platform-agnostic architecture review — findings anchored to named principles + migration cost |
| `/audit-design` | Platform-agnostic UI/UX review — HIG promoted to priority 2 on Swift projects |
| `/audit-web-accessibility-human` | Web accessibility (WCAG 2.1/2.2) review |
| `/audit-web-responsive` | Web responsive design review (viewport, breakpoints, touch targets) |
| `/audit-web-security` | Backend/web/IaC/CI/agent-config security review (gitleaks + semgrep + dep scanners + trivy + actionlint, OWASP/CWE-anchored) |
| `/audit-apple-accessibility` | Apple HIG accessibility (SwiftUI/UIKit/AppKit/WatchKit) review |
| `/audit-apple-adaptivity` | Size classes + iPad multitasking + visionOS windowing + AX5 Dynamic Type layout (Apple-native analogue of `/audit-web-responsive`) |
| `/audit-apple-app-store-review` | Full App Store Review Guidelines walk — preempts rejection reasons before submission |
| `/audit-apple-architecture` | SwiftUI state ownership + `@MainActor` isolation + `Sendable` + structured concurrency + Swift Package modularization |
| `/audit-apple-design` | Apple HIG-anchored design (SF Symbols, materials, dark mode, navigation, animation) |
| `/audit-apple-localization` | String Catalogs + pluralization + RTL + locale-aware formatters |
| `/audit-apple-performance` | Launch time + SwiftUI body invalidation + main-thread blocking + retain cycles + memory + energy (Instruments-anchored) |
| `/audit-apple-persistence` | SwiftData / Core Data / GRDB + CloudKit sync + migration safety + threading |
| `/audit-apple-privacy` | Privacy Manifest + ATT + required-reason APIs + SDK privacy declarations (preempts App Review rejection) |
| `/audit-apple-security` | Apple-platform threat model (Keychain, ATS, entitlements, StoreKit, CloudKit, WKWebView, code signing) |
| `/audit-apple-testing` | XCTest vs Swift Testing + XCUITest critical-flow coverage + Preview coverage + snapshot strategy |
| `/skill-creator` | Author a new skill (graph-driven or cli-wrapper) end-to-end with topology approval and validation |
| `/create-task` | Create a new task note in the Obsidian vault |
| `/create-knowledge` | Create a new knowledge note in the Obsidian vault |
| `/create-draft` | Create a new draft note in the Obsidian vault |
| `/create-read-later` | Add a URL to the Read Later list in the Obsidian vault |
| `/create-blog-post` | AI-powered blog post creation workflow |
| `/sandbox-script` | Create a new standalone script in the sandbox |
| `/sandbox-project` | Create a new project directory in the sandbox |
| `/hsplit` | Split the current tmux pane horizontally (left/right) |
| `/vsplit` | Split the current tmux pane vertically (top/bottom) |

## Skills

Skills are auto-discovered from `~/.claude/skills/`. Each skill has a `SKILL.md` with YAML frontmatter describing when it applies. Skill descriptions are always loaded into context; skill bodies load only when triggered.

| Skill | Description |
|---|---|
| `gh` | Clone/fork/worktree setup plus `gh` CLI operations — issues, PRs, releases, CI |
| `gws` | Google Workspace operations — Gmail, Calendar, Drive, Docs, Sheets, Tasks |
| `obsidian` | Obsidian vault operations via the `obsidian` CLI |
| `orbstack` | OrbStack management — Linux machines, Docker, Kubernetes |
| `project-create-prd` | Guided authoring/revision of a project's PRD; auto-detects create vs revise, publishes to the repo's Forgejo wiki |
| `sprint-seed` | Pre-plan exploratory discussion; shapes fuzzy ideas into a `SEED.md` (grounds candidates in the repo's PRD) |
| `sprint-plan` | Multi-agent collaborative planning with strict orchestrator/worker separation |
| `sprint-plan-to-issues` | Decompose an existing sprint milestone into one Forgejo issue per task (self-assigned, priority-labeled, dependency-linked) |
| `sprint-work` | Execute a planned sprint end-to-end (autonomous) from a Forgejo milestone — one commit per issue, no PRs; auto-writes the retro when the milestone empties |
| `review-pr-simple` | Single-agent PR review → `REVIEW.md` |
| `review-pr-comprehensive` | Dual-agent PR review (Claude + Codex, synthesis, devil's advocate) → `REVIEW.md` |
| `review-address-feedback` | Walk through PR review feedback and apply fixes; supports live PR comments or a local `REVIEW.md` |
| `polish-pull-request` | Final-pass PR cleanup — title, body, cross-links, stale thread resolution |
| `commit` | Analyze changes and create grouped conventional commits with sprint-aware co-author trailers |
| `frontend-design` | Production-grade UI component creation |
| `generate-post-image` | Hugo blog post image generation via DALL-E 3 |
| `skill-creator` | Walks the user through authoring a new skill: discusses scope, picks pattern (graph-driven or cli-wrapper), scaffolds, validates, hands off uncommitted |

Most multi-phase skills (`commit`, `polish-pull-request`, `review-*`, `sprint-*`) are built on the [dot-graph skill pattern](docs/DOT-GRAPH-SKILL-PATTERN.md): the workflow lives in a `graph.dot` with per-node prose under `nodes/`, walked deterministically by `lib/graph_walker.py`. Drift between routing and prose is structurally impossible.

## Subagents

Subagents are specialized agents Claude delegates work to via the Agent tool, when one is needed. None are currently shipped — the prior `audit-*` subagents were migrated to dot-graph skills (see Commands table above) because prose-only enforcement failed silently in too many ways. The `subagents/` directory is preserved as the symlink target at `~/.claude/agents/` for future use.

### Audit output

Each audit run gets its own timestamped folder under `~/Reports/<org>/<repo>/audits/` (org/repo derived from `upstream` remote, falling back to `origin`):

```
~/Reports/<org>/<repo>/audits/
└── YYYY-MM-DDTHH-MM-SS-<audit-id>/      # one folder per run; <audit-id> = architecture | design | test-coverage | web-accessibility | web-responsive | web-security | apple-accessibility | apple-adaptivity | apple-app-store-review | apple-architecture | apple-design | apple-localization | apple-performance | apple-persistence | apple-privacy | apple-security | apple-testing
    ├── claude.md                       ← Claude's independent review
    ├── codex.md                        ← Codex's independent review
    ├── synthesis.md                    ← unified findings
    ├── devils-advocate.md              ← Codex challenge pass
    └── REPORT.md                       ← final findings report
```

The report is a reference document. To act on findings, run `/sprint-plan` and pass the `REPORT.md` path as the seed.

## Sprint workflow output

All sprint, review, and audit artifacts live under `~/Reports/<org>/<repo>/`, derived from the source repo (`upstream` remote, falling back to `origin`). Nothing is written into the project repo itself. See [`docs/sprints/README.md`](docs/sprints/README.md) for the full lifecycle and artifact map.

Files marked `*` are only created when the corresponding optional phase ran.

```
~/Reports/<org>/<repo>/
├── sprints/
│   └── YYYY-MM-DDTHH-MM-SS/                         # one folder per planning session
│       ├── SEED.md                                   * (/sprint-seed handoff)
│       ├── intent.md
│       ├── claude-draft.md                           # orch-side draft (always)
│       ├── codex-draft.md                            * (Phase 5b — opposite-side draft)
│       ├── claude-draft-codex-critique.md            * (Phase 6a)
│       ├── codex-draft-claude-critique.md            * (Phase 6b)
│       ├── merge-notes.md                            * (Phase 7 — Merge mode only)
│       ├── devils-advocate.md                        * (Phase 8a)
│       ├── security-review.md                        * (Phase 8b)
│       ├── architecture-review.md                    * (Phase 8c)
│       ├── test-strategy-review.md                   * (Phase 8d)
│       ├── observability-review.md                   * (Phase 8e)
│       ├── performance-review.md                     * (Phase 8f)
│       ├── breaking-change-review.md                 * (Phase 8g)
│       ├── SPRINT.md                                 # the approved plan
│       ├── FORGEJO.md                                * (/sprint-plan-to-issues handoff)
│       └── RETRO.md                                  * (/sprint-work --retro)
├── pr-reviews/
│   └── pr-N/
│       ├── YYYY-MM-DDTHH-MM-SS/                      # one folder per review run (/review-pr-*)
│       │   └── REVIEW.md  diff.patch  ...
│       └── YYYY-MM-DDTHH-MM-SS-addressed/            # one folder per /review-address-feedback run
│           └── ADDRESSED.md
└── audits/
    └── YYYY-MM-DDTHH-MM-SS-<lens>/                   # one folder per audit run
        └── claude.md  codex.md  synthesis.md  devils-advocate.md  REPORT.md
```

## Disclaimer

This repository contains AI-generated content. Review all configurations and instructions before use. The creators assume no liability for problems caused by using resources from this repository. See [SECURITY.md](SECURITY.md) for details.
