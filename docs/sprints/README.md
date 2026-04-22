# Sprint Skills

This directory documents three Claude Code skills that together form
a lightweight sprint workflow: plan → execute → track.

| Skill | Invoke as | Purpose |
|---|---|---|
| `sprint-plan` | `/sprint-plan` | Multi-agent collaborative planning that produces a reviewed sprint document |
| `sprint-work` | `/sprint-work` | Execute a planned sprint end-to-end and write a retrospective |
| `sprints`     | `/sprints`     | Manage the sprint ledger (`sprints.tsv`) — status, velocity, add/start/complete |

All three operate on a per-project `./docs/sprints/` directory. Sprint
plans, retrospectives, and the ledger all live there, so sprint
history travels with the repository in git.

---

## `sprint-plan` — Collaborative Multi-Agent Planning

`/sprint-plan` is the heaviest of the three skills. It orchestrates
a 9-phase workflow that turns a short seed prompt into a reviewed,
approved, and registered sprint document. The key design principle
is **strict separation of duties**: the orchestrator (the agent you
invoked) never drafts, critiques, or reviews its own work.
Generative and adversarial work is delegated to fresh workers —
either same-family subagents or opposite-family agents invoked via
`exec` — so no single context writes a plan and then judges it.

### What it does

1. **Orient** — reads `CLAUDE.md`, scans the ledger, reviews the last
   3 sprints + retros, does a prior-art check, and pre-fills
   per-phase model tier recommendations.
2. **Phase Selection** — presents a menu of optional phases (drafts,
   critiques, reviews) with enabled/disabled + tier recommendations
   informed by Orient. You can accept, edit, or override.
3. **Intent** — composes a concentrated intent document including a
   "Approaches Considered" table so both drafts start from the same
   concentrated context.
4. **Interview** — adaptive dialogue whose depth scales with the
   sprint's uncertainty (Low: 1–2 questions; High: 5–7). Every
   question has a "Skip" option.
5. **Draft (parallel)** — commissions a Claude-side draft and an
   opposite-side (Codex) draft in parallel. Each is written
   independently with no knowledge of the other.
6. **Critique (parallel, optional)** — each side critiques the
   other's draft.
7. **Merge / Promote** — synthesizes the best ideas, applies a
   simplest-viable filter, runs a sprint-sizing gate to catch
   oversized plans before review cost is spent.
8. **Reviews (parallel, optional)** — up to seven lenses, each routed
   to its expert side:
   - Devil's Advocate *(codex)*
   - Security *(claude)*
   - Architecture *(claude)*
   - Test Strategy *(codex)*
   - Observability *(claude)*
   - Performance & Scale *(codex)*
   - Breaking Change *(claude)*
9. **Finalize** — incorporates findings, runs a Definition-of-Ready
   pre-flight, proposes a feasibility spike if uncertainty is
   structurally too high, and appends a **Recommended Execution**
   section that tells you which Claude tier (`opus` / `sonnet` /
   `haiku`) to run `/sprint-work` with. After approval, the sprint
   is registered in the ledger as `SPRINT-NNN`.

### Usage

```bash
# Full interactive workflow — Orient, then a phase-selection menu
/sprint-plan <seed prompt>

# Accept all Orient recommendations and skip the menu
/sprint-plan --auto <seed prompt>

# Enable every optional phase
/sprint-plan --full <seed prompt>

# Minimum viable planning — required phases only (5a, 7, 9)
/sprint-plan --base <seed prompt>

# Force all delegated phases to High (opus / gpt-5.4) or Mid
/sprint-plan --tier=high <seed prompt>
/sprint-plan --tier=mid  <seed prompt>

# Preview only — no files written, exits after Intent
/sprint-plan --dry <seed prompt>

# Combines freely, e.g.:
/sprint-plan --full --tier=high critical auth rewrite
/sprint-plan --dry --auto add rollback guardrails

# Help
/sprint-plan --help
```

Flag precedence: `--help` trumps everything; `--base` / `--full` /
`--auto` are mutually exclusive; `--tier=` combines with any
workflow shortcut; `--dry` suppresses all side effects. Unknown
flags fail loudly.

### Artifacts produced

All files land in `./docs/sprints/` with a shared timestamp prefix:

```
./docs/sprints/
├── 2026-04-22T14-03-11-sprint-plan-intent.md
├── 2026-04-22T14-03-11-sprint-plan-claude-draft.md
├── 2026-04-22T14-03-11-sprint-plan-codex-draft.md             * optional
├── 2026-04-22T14-03-11-sprint-plan-claude-draft-codex-critique.md   * optional
├── 2026-04-22T14-03-11-sprint-plan-codex-draft-claude-critique.md   * optional
├── 2026-04-22T14-03-11-sprint-plan-merge-notes.md             * merge mode
├── 2026-04-22T14-03-11-sprint-plan-devils-advocate.md         * optional
├── 2026-04-22T14-03-11-sprint-plan-security-review.md         * optional
├── 2026-04-22T14-03-11-sprint-plan-architecture-review.md     * optional
├── 2026-04-22T14-03-11-sprint-plan-test-strategy-review.md    * optional
├── 2026-04-22T14-03-11-sprint-plan-observability-review.md    * optional
├── 2026-04-22T14-03-11-sprint-plan-performance-review.md      * optional
├── 2026-04-22T14-03-11-sprint-plan-breaking-change-review.md  * optional
└── 2026-04-22T14-03-11-sprint-plan-SPRINT-007.md              (renamed on approval)
```

---

## `sprint-work` — Execute the Next Sprint

`/sprint-work` runs a sprint planned by `/sprint-plan`. It finds the
sprint document, marks the sprint in-progress, executes the plan,
writes a retrospective, and marks the sprint completed — all in one
session.

### What it does

1. **Locate the sprint** — if you pass `NNN`, it runs that specific
   sprint; otherwise it picks up any in-progress sprint (surfacing
   its identity first), or falls back to the lowest-numbered
   `planned` sprint in the ledger.
2. **Mark in-progress** — records the Claude model family
   (`opus` / `sonnet` / `haiku`) running this session so velocity
   stats can compare recommended vs. actual model later.
3. **Execute** — works through every item in the sprint's Definition
   of Done. Finds build/test commands from `README.md`, `Makefile`,
   or the DoD itself. Fixes build and test failures.
4. **Write the retro** — captures what was underestimated, deferred,
   surprising, and what to do differently. The retro also includes a
   model-fit assessment so future `/sprint-plan` Orient phases learn
   from it. Retro file: `*-sprint-retro-SPRINT-NNN.md`.
5. **Mark completed** — updates the ledger and records the retro's
   model-fit verdict (`over_powered` / `right_sized` /
   `under_powered`).

It never pushes git changes.

### Usage

```bash
# Run the next sprint (in-progress first, else lowest planned)
/sprint-work

# Run a specific sprint
/sprint-work 007

# Print the sprint plan document and exit — no execution
/sprint-work --review
/sprint-work --review 007

# Help
/sprint-work --help
```

### Recommended flow

The final step of `/sprint-plan` writes a **Recommended Execution**
block telling you which model tier to use. The intended flow is:

```bash
/sprint-plan <seed prompt>   # produce and register the plan
# read the Recommended Execution block at the end of the sprint doc
/model sonnet                # or opus / haiku, per the recommendation
/sprint-work                 # runs the newly registered sprint
```

You can re-read the recommendation any time with
`/sprint-work --review [NNN]`.

---

## `sprints` — Sprint Ledger Manager

`/sprints` is a thin CLI wrapper over `scripts/sprints.py` that
manages `./docs/sprints/sprints.tsv` — a tab-separated ledger of
every sprint, its status, and the models associated with it. Both
`/sprint-plan` and `/sprint-work` call this skill internally to
register, start, and complete sprints, but you can also invoke it
directly at any time.

### What it does

- Tracks status (`planned`, `in_progress`, `completed`, `skipped`).
- Records the **recommended model** (set by `/sprint-plan`) and the
  **actual model** that ran the sprint (set by `/sprint-work`).
- Records the **model-fit verdict** from the retro.
- Computes velocity statistics (mean, median, rolling, by model).
- Syncs the ledger from existing sprint-plan files if you ever lose
  it or adopt the workflow mid-project.

### Usage

```bash
# Overview + velocity summary when data exists
/sprints --stats

# Show the current in-progress sprint / next planned sprint
/sprints --current
/sprints --next

# List sprints (optionally filtered)
/sprints --list
/sprints --list --status=planned

# Velocity statistics across completed sprints
/sprints --velocity

# Add / start / complete / skip a sprint
/sprints --add 007 "Add rollback guardrails" --recommended-model=sonnet --participants=claude,codex
/sprints --start 007 --model=sonnet
/sprints --complete 007
/sprints --skip 007

# Arbitrary status edit
/sprints --set-status 007 planned

# Record model-fit from the retro
/sprints --set-fit 007 right_sized        # or over_powered / under_powered

# Rebuild the ledger from existing sprint docs in ./docs/sprints/
/sprints --sync

# Help
/sprints --help
```

The ledger lives at `./docs/sprints/sprints.tsv` relative to the
current working directory — always run from the project root.

---

## How the three skills fit together

```
       ┌───────────────┐
       │ /sprint-plan  │   produces SPRINT-NNN.md + intent + drafts + reviews
       └───────┬───────┘   registers the sprint via /sprints --add
               │
               ▼
       ┌───────────────┐
       │   /sprints    │   ledger: status, models, velocity
       └───────┬───────┘
               │
               ▼
       ┌───────────────┐
       │ /sprint-work  │   executes, writes retro, marks complete
       └───────────────┘   sets --start, --set-fit, --complete via /sprints
```

Everything lives in `./docs/sprints/` inside your project, so sprint
history, retros, and the ledger travel with the repo.

---

## Setup

The skills are distributed via the `agent-config` repo at
`~/Code/github.com/coreydaley/agent-config/`. The repo's
`make all` target symlinks everything into place, but if you want
to install them manually, here is exactly what goes where.

### What to copy

| Source (in `agent-config/`) | Destination | Required? |
|---|---|---|
| `skills/sprint-plan/` | `~/.claude/skills/sprint-plan/` | Required |
| `skills/sprint-work/` | `~/.claude/skills/sprint-work/` | Required |
| `skills/sprints/`     | `~/.claude/skills/sprints/`     | Required |
| `lib/sprint_ledger.py` | `~/.claude/lib/sprint_ledger.py` | **Required — without this, `/sprints` cannot run** |

The `sprints` skill's script (`skills/sprints/scripts/sprints.py`)
imports the shared data model from `~/.claude/lib/sprint_ledger.py`
via:

```python
sys.path.insert(0, str(Path.home() / ".claude" / "lib"))
from sprint_ledger import SprintEntry, SprintLedger, get_ledger_path
```

So you must copy (or symlink) both the skill *and* the lib. Missing
either one breaks the ledger.

### Recommended: symlink from the repo

Symlinking (instead of copying) keeps everything up to date when you
`git pull` the `agent-config` repo. This mirrors what the repo's
`scripts/symlink-claude.sh` does:

```bash
AGENT_CONFIG="$HOME/Code/github.com/coreydaley/agent-config"

mkdir -p ~/.claude/skills ~/.claude/lib

ln -sf "$AGENT_CONFIG/skills/sprint-plan" ~/.claude/skills/sprint-plan
ln -sf "$AGENT_CONFIG/skills/sprint-work" ~/.claude/skills/sprint-work
ln -sf "$AGENT_CONFIG/skills/sprints"     ~/.claude/skills/sprints
ln -sf "$AGENT_CONFIG/lib/sprint_ledger.py" ~/.claude/lib/sprint_ledger.py
```

Or, from the repo root:

```bash
make symlinks   # symlinks skills/, lib/, commands/, subagents/, CLAUDE.md
# or
make all        # symlinks + git hooks
```

### Manual copy (no symlinks)

If you'd rather copy the files in:

```bash
AGENT_CONFIG="$HOME/Code/github.com/coreydaley/agent-config"

mkdir -p ~/.claude/skills ~/.claude/lib

cp -R "$AGENT_CONFIG/skills/sprint-plan" ~/.claude/skills/
cp -R "$AGENT_CONFIG/skills/sprint-work" ~/.claude/skills/
cp -R "$AGENT_CONFIG/skills/sprints"     ~/.claude/skills/
cp    "$AGENT_CONFIG/lib/sprint_ledger.py" ~/.claude/lib/
```

Re-run the copy whenever the repo updates.

### Verify the install

```bash
# The three skills should be discoverable
ls ~/.claude/skills/sprint-plan/SKILL.md
ls ~/.claude/skills/sprint-work/SKILL.md
ls ~/.claude/skills/sprints/SKILL.md

# The shared lib must be importable from the skill script
ls ~/.claude/lib/sprint_ledger.py

# In a project directory, a no-op run should work:
cd ~/some/project
/sprints --help
```

### Requirements

- Python 3 on `PATH` (the `sprints` script runs via
  `python3 ${CLAUDE_SKILL_DIR}/scripts/sprints.py`).
- A git repository with a `docs/` directory — sprint artifacts live
  in `./docs/sprints/` relative to the cwd. The directory is
  created automatically on first run.
- For the opposite-side delegation in `/sprint-plan` to work, you
  need the `codex` CLI on `PATH` when running from Claude (or the
  `claude` CLI when running from Codex). Without it, skip the
  opposite-side phases — `/sprint-plan --base` still works single-
  agent.
