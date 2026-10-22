# agent-config

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

My personal [Claude Code](https://claude.ai/code) configuration — instructions, skills, commands, and subagents — version-controlled and symlinked into `~/.claude/`. Shared in case it's useful; it's tuned to my own setup, so read before you borrow.

> **Security notice:** The contents of this repository flow directly into Claude's system prompt. Review all files before use, and never commit secrets or credentials. Pre-commit and pre-push hooks run `gitleaks` and a personal-info check (see [Safety hooks](#safety-hooks)), and CI runs the same scans on every push.

> **⚠️ `settings.json` is permissive on purpose.** It allows every tool (`Bash(*)`, `Edit(*)`, `Write(*)`…) and skips the dangerous-mode prompt — it's my machine and my risk tolerance. Don't copy it as-is; start from Claude Code's defaults and allow only what you need.

## What's in here

| Path | Purpose |
|---|---|
| `CLAUDE.md` | Global instructions loaded by Claude Code on every session |
| `settings.json` | Global Claude Code settings (permissions, hooks, statusline, model, theme) — permissive, see the warning above |
| `skills/` | Skills, auto-discovered by Claude Code and invoked as `/skill-name` |
| `subagents/` | Review roles (`independent-reviewer`, `adversarial-reviewer`, …) the `pr-*` skills and `/review-design` delegate judgments to |
| `lib/` | Shared libraries for skills: the dot-graph walker, the audit runner/verifier, the role contract, and the `pr-*` family's layout, scope, and hygiene rules |
| `docs/` | The [dot-graph skill pattern](docs/DOT-GRAPH-SKILL-PATTERN.md), the [PR workflow guide](docs/PR-WORKFLOW.md), and the project-lifecycle diagram |
| `scripts/` | Setup scripts: symlinks, safety hooks, personal-info check, statusline |
| `commands/` | Custom slash commands — currently empty; everything is a skill |

## Setup

```bash
git clone https://github.com/coreydaley/agent-config.git
cd agent-config
brew install gitleaks
make all
```

`make all` symlinks this repo into `~/.claude/` and installs the safety hooks. It is idempotent — safe to run multiple times.

### What gets symlinked

```
CLAUDE.md                       → ~/.claude/CLAUDE.md
settings.json                   → ~/.claude/settings.json
commands/                       → ~/.claude/commands/
skills/                         → ~/.claude/skills/
lib/                            → ~/.claude/lib/
scripts/statusline-command.sh   → ~/.claude/statusline-command.sh
subagents/                      → ~/.claude/agents/   (review roles used by the pr-* skills)
```

Existing files at symlink destinations are backed up with a `.old` extension before replacement.

### Individual targets

```bash
make symlinks   # Create ~/.claude/ symlinks only
make hooks      # Install the safety hooks only
make help       # Show all available targets
```

## Safety hooks

This repo is public, so `make hooks` installs two layers of protection:

- **pre-commit** — blocks credential/key file types and large archives, runs `gitleaks protect --staged`, and runs `scripts/check-personal-info.py --staged` on the lines being added.
- **pre-push** — `gitleaks detect` over the full history and the personal-info check over every tracked file.

`scripts/check-personal-info.py` blocks home-network hostnames (`*.local`), private IPs, email addresses, phone numbers, and absolute home-directory paths, plus anything in a **private denylist** at `~/.config/agent-config/denylist` (created empty by `make hooks`, never committed — put names, employers, addresses, and the like there). Known-safe matches go in `.personal-info-allow`.

CI (`.github/workflows/scan.yml`) re-runs gitleaks and the generic personal-info check on every push and pull request, in case a hook was skipped.

## Skills

Skills are auto-discovered from `~/.claude/skills/` and invoked as `/skill-name` (most can also trigger automatically from context). Each has a `SKILL.md` whose frontmatter description is always in context; the body loads only when the skill runs.

### Workflow

| Skill | What it does |
|---|---|
| `/commit` | Plan logical commit groups from the working tree and write conventional commits (never amends, never force-pushes, never skips hooks) |
| `/tag` | Pick the next semantic version from conventional commits and create the tag (confirms first, never pushes) |
| `/feature-create` | Shape a fuzzy idea into a GitHub feature issue (`type/feature`) grounded in the repo README; large features are graded by a fresh reviewer before filing |
| `/feature-plan` | Plan a feature issue into self-assigned native GitHub sub-issues ordered by blocked-by dependencies, with drafts and critiques from fresh sub-agents |
| `/feature-work` | Build a feature's sub-issues on a `feature/<slug>` branch — one commit per sub-issue with `Closes #N`, pushed but never merged; ends with a punch list |
| `/issue-create` | Capture a standalone bug / enhancement / chore / docs item as a labeled GitHub issue |
| `/project-create` | Discuss a new project, then scaffold it: private GitHub repo, bare clone + worktree, README and overview |
| `/skill-creator` | Author a new skill: pick the pattern (dot-graph or CLI wrapper), scaffold, validate, hand off uncommitted |
| `/create-blog-post` | Draft a post for coreydaley.dev, get an editorial critique from a fresh sub-agent, then finalize |
| `/create-website-content` | Research and hands-on test a coreydaley.dev page (answer, help, compare, landing section), fact-check it with a fresh sub-agent, then finalize and check it in light, dark and phone widths |

### PR workflow

One issue → one branch → one PR. Every step reads and appends to the same folder, and nothing is posted, pushed, or opened without a gate you answer. Full guide: [`docs/PR-WORKFLOW.md`](docs/PR-WORKFLOW.md).

```
/pr-plan → /pr-build → /pr-review → /pr-fix → (human review → /pr-fix) → /pr-polish → you merge
```

| Skill | What it does |
|---|---|
| `/pr-plan` | Turn an issue, PR, markdown file, or sentence into an approved PLAN.md with a scope contract; M+ plans get an adversarial pass first |
| `/pr-build` | Execute an approved PLAN.md: one commit and targeted test per task, plan-delivery and hygiene checks, then a draft PR once you approve the body |
| `/pr-review` | Multi-role review of a PR or local branch: independent and adversarial reviewers in parallel, synthesis, devil's advocate, adjudication |
| `/pr-fix` | Triage review findings or PR threads against the plan's scope, apply only approved fixes, gate the push, draft replies |
| `/pr-address` | `/pr-fix` pointed at everything on a PR: human and bot threads, reviews, failing checks |
| `/pr-polish` | Final pre-merge pass: rewrite the body to the final state, resolve addressed threads, slim comments, tidy history or propose the squash message |
| `/review-design` | Adversarial review of a design's claims against the code, with a defense pass and a Build / Rework / Don't build verdict |

`/pr-plan` sizes the work and picks the ceremony: XS/S plans go straight to you, M/L get an adversarial pass, and XL or multi-architecture work is pointed at `/review-design` before anything is built. The family reads GitHub issues but never creates, edits, labels, or closes them; deferred findings go to the plan's Follow-ups. Use the `feature-*` skills instead when a feature decomposes into many sub-issues on one branch.

### Review roles

The `pr-*` skills and `/review-design` never grade their own work. Each judgment runs in a fresh subagent from `subagents/` with a fixed stance, so two reviewers from the same model don't just agree with each other. Contract and briefing rules: [`lib/agent-roles.md`](lib/agent-roles.md).

| Role | Stance |
|---|---|
| `independent-reviewer` | Senior maintainer: correctness, design fit, tests, conventions |
| `adversarial-reviewer` | Hostile: failure modes, security, concurrency, edge inputs; runs in parallel with the independent reviewer |
| `synthesizer` | Neutral editor: dedupes and calibrates severity, adds nothing |
| `devils-advocate` | Attacks the synthesis, triage, or plan: false positives, misses, miscalibration |
| `adjudicator` | Rules on each challenge; burden of proof on the challenger |
| `defender` | Steelmans a design against attacks, concedes what holds (`/review-design`) |
| `verifier` | Literal checks: plan delivery, scope triage, threads addressed, hygiene sweeps |

All roles run on Fable, read-only against the code, and write only the artifact their brief names.

### Audits

29 audit skills, each a 5-phase dot-graph run — independent review, synthesis, devil's-advocate challenge, report, and a hard artifact gate (`lib/audit-verify.sh`) so an audit can't "finish" without writing its report. Findings are anchored to named principles (OWASP/CWE, WCAG, Apple HIG, App Store Review Guidelines, …).

- **General / web:** `audit-architecture`, `audit-design`, `audit-web-security`, `audit-web-accessibility-human`, `audit-web-accessibility-agent`, `audit-web-responsive`, `audit-web-seo`
- **Apple, cross-platform:** `audit-apple-accessibility`, `-adaptivity`, `-app-store-review`, `-architecture`, `-build-release`, `-deeplinks-continuity`, `-design`, `-extensions`, `-localization`, `-networking`, `-notifications`, `-observability`, `-performance`, `-persistence`, `-privacy`, `-security`, `-storekit`, `-testing`
- **Apple, per platform:** `audit-apple-ios`, `-macos`, `-watchos`, `-visionos`

### Tools

| Skill | What it does |
|---|---|
| `gh` | GitHub via the `gh` CLI — cloning/forking (bare clone + worktrees), issues, PRs, releases, CI |
| `orbstack` | OrbStack — Linux machines, Docker, Kubernetes |
| `xcuitest-on-mini` | Run `xcodebuild test` on a Mac mini over SSH so UI tests don't take over your screen (set `XCUITEST_ON_MINI_HOST`) |

Most multi-phase skills (`commit`, `feature-*`, `pr-*` (except the `pr-address` wrapper), `review-design`, `issue-create`, `project-create`, `skill-creator`, `create-blog-post`, `create-website-content`, and every `audit-*`) are built on the [dot-graph skill pattern](docs/DOT-GRAPH-SKILL-PATTERN.md): the workflow lives in a `graph.dot` with per-node prose under `nodes/`, walked deterministically by `lib/graph_walker.py`. Drift between routing and prose is structurally impossible.

### Audit output

Each audit run gets its own timestamped folder under `~/Reports/<org>/<repo>/audits/` (org/repo derived from `upstream` remote, falling back to `origin`):

```
~/Reports/<org>/<repo>/audits/
└── YYYY-MM-DDTHH-MM-SS-<audit-id>/      # one folder per run; <audit-id> = the skill name without the audit- prefix, e.g. web-security, apple-privacy
    ├── claude.md                       ← review sub-agent's findings
    ├── synthesis.md                    ← consolidated findings
    ├── devils-advocate.md              ← devil's-advocate sub-agent challenge pass
    └── REPORT.md                       ← final findings report
```

The report is a reference document. To act on findings, capture them as a feature with `/feature-create` (or fold them into an existing feature issue), then `/feature-plan` and `/feature-work`.

## Feature and PR workflow output

All feature, PR, and audit artifacts live under `~/Reports/<org>/<repo>/`, derived from the source repo (`upstream` remote, falling back to `origin`). Nothing is written into the project repo itself. The **durable** record of a feature is its GitHub issue + native sub-issues + the commits that close them; the local files are ephemeral working copies.

```
~/Reports/<org>/<repo>/
├── features/
│   └── YYYY-MM-DDTHH-MM-SS/                         # one folder per feature session
│       ├── FEATURE.md                               # /feature-create working draft (issue body)
│       ├── .feature.md                              # /feature-plan: cached feature issue body
│       ├── intent.md                                # /feature-plan
│       ├── draft-a.md, draft-b.md                   # /feature-plan: independent drafts
│       ├── draft-a-critique.md, draft-b-critique.md # /feature-plan: symmetric critiques
│       ├── merge-notes.md                           # /feature-plan: merge synthesis
│       ├── devils-advocate.md, security-review.md   # /feature-plan: review lenses
│       └── PLAN.md                                  # /feature-plan working plan (sub-issues are durable)
├── prs/
│   └── <branch-key>/                                # one folder per branch (fix/gh-123-x → fix-gh-123-x; pr-<N> for others' PRs)
│       ├── PLAN.md  source.md  orient.md            # /pr-plan: the scope contract and what it was built from
│       ├── plan-attack.md                           # /pr-plan: adversarial pass and rulings (M+ only)
│       ├── pr-body.md  verify.md  sweep.md          # /pr-build: PR body as opened, plan-delivery and hygiene checks
│       ├── reviews/<TS>/                            # /pr-review: review-*.md, synthesis.md, devils-advocate.md, adjudication.md, REVIEW.md
│       ├── fixes/<TS>/                              # /pr-fix: TRIAGE.md, ADDRESSED.md
│       └── polish/<TS>/                             # /pr-polish: PROPOSALS.md
├── designs/
│   └── <slug>/<TS>/                                 # /review-design: claim ledger, attacks, synthesis, defense.md, REVIEW.md
└── audits/
    └── YYYY-MM-DDTHH-MM-SS-<lens>/                   # one folder per audit run
        └── claude.md  synthesis.md  devils-advocate.md  REPORT.md
```

`/feature-work` produces no per-run report folder — its artifacts are the commits on each repo's `feature/<slug>` branch and the updated (still-open) sub-issues; its walker state lives under `$TMPDIR/.claude-walker/feature-work/`.

## Disclaimer

This repository contains AI-generated content. Review all configurations and instructions before use. The creators assume no liability for problems caused by using resources from this repository. To report a security issue privately, use GitHub's private vulnerability reporting on this repo.
