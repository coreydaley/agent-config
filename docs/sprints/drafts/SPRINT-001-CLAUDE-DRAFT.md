# Sprint 001: Agent-Config Repository Revamp

## Overview

This sprint is a ground-up redesign of the `agent-config` repository to correctly handle the fundamental differences between how each AI CLI agent (Claude, Codex, Copilot, Gemini) reads configuration from the local filesystem. The original implementation assumed all agents behave identically — same file formats, same directory names, same paths — which is incorrect.

The goal is not to fight these differences but to build an architecture that embraces them: a shared base layer of configuration content flows into per-agent build steps, each of which produces the right artifacts in the right format for that agent, then places them in the right locations via symlinks.

The core generate+symlink pattern already in place is the right model. This sprint keeps it, sharpens it with per-agent routing rules, adds format conversion where needed, and ensures the entire pipeline is coherent and documented.

## Use Cases

1. **New user setup**: Clone the repo, run `make all`, and all four agents (Claude, Codex, Copilot, Gemini) are immediately configured with shared base instructions and any agent-specific content.
2. **Add a shared instruction**: Edit `agents/_GLOBAL.md`, run `make generate`, and all four agent config files are regenerated with the update.
3. **Add a Claude-only skill**: Drop a `SKILL.md` into `skills/my-skill/`, run `make symlink-skills` — it appears in `~/.claude/skills/` and `~/.copilot/skills/` automatically (the agents that support the `skills/` convention).
4. **Add a command**: Write a markdown command in `commands/my-cmd.md`. It appears in `~/.claude/commands/` and `~/.codex/prompts/` automatically. A TOML conversion is generated for Gemini in `build/gemini-commands/my-cmd.toml`.
5. **Agent-specific instruction**: Edit `agents/claude/_CLAUDE.md` and run `make generate` — only Claude's merged file is updated.

## Architecture

```
agent-config/
├── agents/
│   ├── _GLOBAL.md              # Shared instructions for all agents
│   ├── _GLOBAL_LB.md           # (optional) global line-break variant
│   ├── claude/
│   │   ├── _CLAUDE.md          # Claude-specific instructions (appended to _GLOBAL)
│   │   └── CLAUDE.md           # Generated: _GLOBAL + _CLAUDE  [symlinked to ~/.claude/CLAUDE.md]
│   ├── codex/
│   │   ├── _CODEX.md           # Codex-specific instructions
│   │   └── CODEX.md            # Generated: _GLOBAL + _CODEX   [symlinked to ~/.codex/AGENTS.md]
│   ├── copilot/
│   │   ├── _COPILOT.md         # Copilot-specific instructions
│   │   └── COPILOT.md          # Generated: _GLOBAL + _COPILOT [symlinked to ~/.copilot/copilot-instructions.md]
│   └── gemini/
│       ├── _GEMINI.md          # Gemini-specific instructions
│       └── GEMINI.md           # Generated: _GLOBAL + _GEMINI  [symlinked to ~/.gemini/GEMINI.md]
│
├── skills/                     # Shared skills (SKILL.md format)
│   ├── .system/                # System skills (not symlinked to agents)
│   ├── ledger/                 # Sprint ledger skill
│   ├── frontend-design/        # Frontend design skill
│   ├── mcp-builder/            # MCP server builder skill
│   └── skill-creator/          # Skill authoring skill
│       [symlinked: ~/.claude/skills/, ~/.copilot/skills/]
│       [NOT symlinked: codex (no standard global path), gemini (uses @imports)]
│
├── commands/                   # Shared commands in Markdown format
│   ├── commit.md
│   ├── tag.md
│   ├── sprint.md
│   └── superplan.md
│       [symlinked: ~/.claude/commands/, ~/.codex/prompts/]
│       [NOT symlinked: copilot (unsupported), gemini (wrong format)]
│
├── subagents/                  # Shared subagent definitions
│   (future: .md for Claude/Codex, .agent.md for Copilot)
│       [symlinked: ~/.claude/agents/, ~/.copilot/agents/]
│       [NOT symlinked: codex (no native subagents), gemini (format TBD)]
│
├── prompts/                    # Ad-hoc prompts (not symlinked; for reference)
│
├── build/                      # Generated artifacts (gitignored)
│   └── gemini-commands/        # Auto-converted .toml files for Gemini
│       ├── commit.toml
│       ├── tag.toml
│       └── ...
│
├── scripts/
│   ├── utils.sh                # Shared symlink utilities
│   ├── generate-agent-files.sh # Merges _GLOBAL + _<AGENT> → <AGENT>.md
│   ├── generate-gemini-commands.sh  # NEW: converts commands/*.md → build/gemini-commands/*.toml
│   ├── symlink-agents.sh       # Symlinks agent config files
│   ├── symlink-skills.sh       # Symlinks skills/ (Claude, Copilot only)
│   ├── symlink-commands.sh     # Symlinks commands/ (Claude→commands/, Codex→prompts/)
│   ├── symlink-subagents.sh    # Symlinks subagents/ (Claude, Copilot only)
│   └── symlink-gemini-commands.sh  # NEW: symlinks build/gemini-commands/ → ~/.gemini/commands/
│
├── docs/
│   └── sprints/                # Sprint planning documents
│       ├── README.md
│       ├── ledger.tsv
│       └── SPRINT-NNN.md
│
├── Makefile
├── README.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
└── CHANGELOG.md
```

### Data Flow

```
_GLOBAL.md ─┬─► cat ─► CLAUDE.md  ─► ~/.claude/CLAUDE.md
_CLAUDE.md ─┘

_GLOBAL.md ─┬─► cat ─► CODEX.md   ─► ~/.codex/AGENTS.md
_CODEX.md  ─┘

_GLOBAL.md ──┬─► cat ─► COPILOT.md ─► ~/.copilot/copilot-instructions.md
_COPILOT.md ─┘

_GLOBAL.md ─┬─► cat ─► GEMINI.md  ─► ~/.gemini/GEMINI.md
_GEMINI.md ─┘

skills/    ─────────────────────────► ~/.claude/skills/
                                    ► ~/.copilot/skills/

commands/  ─────────────────────────► ~/.claude/commands/
           ─────────────────────────► ~/.codex/prompts/
           ─► md→toml conversion ──► build/gemini-commands/
                                    ► ~/.gemini/commands/

subagents/ ─────────────────────────► ~/.claude/agents/
           ─────────────────────────► ~/.copilot/agents/
```

### Agent Capability Matrix

| Feature | Claude | Codex | Copilot | Gemini |
|---|---|---|---|---|
| Agent config file | `~/.claude/CLAUDE.md` | `~/.codex/AGENTS.md` | `~/.copilot/copilot-instructions.md` | `~/.gemini/GEMINI.md` |
| Skills directory | `~/.claude/skills/` | `config.toml` registered | `~/.copilot/skills/` | @imports in GEMINI.md |
| Commands directory | `~/.claude/commands/` | `~/.codex/prompts/` | not supported | `~/.gemini/commands/` (.toml) |
| Subagents directory | `~/.claude/agents/` | not supported | `~/.copilot/agents/` | `~/.gemini/agents/` |
| Command format | Markdown | Markdown | — | TOML |
| Subagent format | `.md` + YAML frontmatter | — | `.agent.md` + YAML frontmatter | `.md` + YAML frontmatter (needs `tools:`) |

## Implementation Plan

### Phase 1: Repository Cleanup and Structure (~15%)

**Goal**: Establish correct directory structure, fix `.gitignore`, create `build/` dir, set up sprint infrastructure.

**Files:**
- `.gitignore` — add `build/` directory
- `docs/sprints/README.md` — document sprint conventions
- `docs/sprints/ledger.tsv` — initialize empty ledger
- `Makefile` — add `generate-gemini-commands` and `symlink-gemini-commands` targets

**Tasks:**
- [ ] Add `build/` to `.gitignore`
- [ ] Create `docs/sprints/README.md` with sprint conventions
- [ ] Initialize `docs/sprints/ledger.tsv`
- [ ] Update Makefile with new targets

### Phase 2: Agent Config Content (~20%)

**Goal**: Write meaningful content for `_GLOBAL.md` and each agent-specific file.

**Files:**
- `agents/_GLOBAL.md` — shared instructions applicable to all agents
- `agents/claude/_CLAUDE.md` — Claude-specific conventions (tools, memory, hooks awareness)
- `agents/codex/_CODEX.md` — Codex-specific conventions (AGENTS.md sections, sandbox awareness)
- `agents/copilot/_COPILOT.md` — Copilot-specific conventions (PR-focused, GitHub integration)
- `agents/gemini/_GEMINI.md` — Gemini-specific conventions (Google ecosystem, @import usage)

**Tasks:**
- [ ] Write `_GLOBAL.md` with shared conventions (commit style, code conventions, disclaimer)
- [ ] Write `_CLAUDE.md` with Claude-specific guidance
- [ ] Write `_CODEX.md` with Codex-specific guidance
- [ ] Write `_COPILOT.md` with Copilot-specific guidance
- [ ] Write `_GEMINI.md` with Gemini-specific guidance and @import references to skills
- [ ] Run `make generate` and verify all four merged files

### Phase 3: Fix Symlink Scripts (~20%)

**Goal**: Ensure every symlink script routes correctly per-agent and skips unsupported features cleanly.

**Files:**
- `scripts/symlink-agents.sh` — already fixed (Codex → `AGENTS.md`)
- `scripts/symlink-skills.sh` — fix: only Claude and Copilot; add note for Codex/Gemini
- `scripts/symlink-commands.sh` — already fixed (Claude → `commands/`, Codex → `prompts/`, others excluded)
- `scripts/symlink-subagents.sh` — fix: only Claude and Copilot; exclude Codex and Gemini; fix source to `subagents/`

**Tasks:**
- [ ] Fix `symlink-skills.sh`: remove Codex and Gemini from skills loop
- [ ] Fix `symlink-subagents.sh`: remove Codex and Gemini; change source from `agents/` to `subagents/`
- [ ] Add `ensure_dir` helper to `utils.sh` that creates `~/.agent/` if it doesn't exist before symlinking
- [ ] Verify all four scripts produce correct results with `make all`

### Phase 4: Gemini Command Conversion (~20%)

**Goal**: Implement Markdown → TOML conversion for Gemini commands.

**Files:**
- `scripts/generate-gemini-commands.sh` — NEW: reads `commands/*.md`, strips YAML frontmatter, converts to TOML
- `scripts/symlink-gemini-commands.sh` — NEW: symlinks `build/gemini-commands/` → `~/.gemini/commands/`
- `build/gemini-commands/` — gitignored generated output

**Conversion rules:**
- YAML frontmatter `description:` field → TOML `description = "..."`
- Markdown body → TOML `prompt = """..."""`
- Frontmatter fields `disable-model-invocation` and `allowed-tools` are Claude-specific; strip them for Gemini

**Tasks:**
- [ ] Write `scripts/generate-gemini-commands.sh` using `awk`/`sed` for YAML→TOML extraction
- [ ] Write `scripts/symlink-gemini-commands.sh`
- [ ] Add `generate-gemini-commands` target to Makefile (runs before `symlink-gemini-commands`)
- [ ] Test conversion with existing commands (commit.md, tag.md, sprint.md, superplan.md)

### Phase 5: Documentation (~15%)

**Goal**: Update README, agents/README, and add a compatibility table.

**Files:**
- `README.md` — full rewrite of Setup/Usage sections; add capability matrix table
- `agents/README.md` — update to reflect correct symlink targets and agent differences
- `docs/sprints/README.md` — sprint planning conventions

**Tasks:**
- [ ] Rewrite `README.md` Setup section with correct per-agent paths
- [ ] Add agent capability matrix table to `README.md`
- [ ] Add "What's not supported" section per agent
- [ ] Update `agents/README.md` to reflect all four agents and correct symlink targets
- [ ] Write `docs/sprints/README.md`

### Phase 6: Sprint Infrastructure (~10%)

**Goal**: Set up the ledger and sprint tooling so future sprints can be tracked.

**Files:**
- `docs/sprints/ledger.tsv`
- `docs/sprints/README.md`
- `skills/ledger/scripts/ledger.py` (already exists)

**Tasks:**
- [ ] Verify ledger.py path resolution works from project root
- [ ] Initialize `docs/sprints/ledger.tsv` with SPRINT-001 entry
- [ ] Run `/ledger sync` to confirm the ledger skill works end-to-end

## Files Summary

| File | Action | Purpose |
|---|---|---|
| `.gitignore` | Modify | Add `build/` |
| `agents/_GLOBAL.md` | Write | Shared agent instructions |
| `agents/claude/_CLAUDE.md` | Write | Claude-specific instructions |
| `agents/codex/_CODEX.md` | Write | Codex-specific instructions |
| `agents/copilot/_COPILOT.md` | Write | Copilot-specific instructions |
| `agents/gemini/_GEMINI.md` | Write | Gemini-specific instructions |
| `scripts/symlink-skills.sh` | Modify | Restrict to Claude + Copilot |
| `scripts/symlink-subagents.sh` | Modify | Restrict to Claude + Copilot; fix source dir |
| `scripts/generate-gemini-commands.sh` | Create | md→toml conversion |
| `scripts/symlink-gemini-commands.sh` | Create | Symlink Gemini commands |
| `Makefile` | Modify | Add new targets |
| `README.md` | Modify | Per-agent paths, capability matrix |
| `agents/README.md` | Modify | Correct symlink targets |
| `docs/sprints/README.md` | Create | Sprint conventions |
| `docs/sprints/ledger.tsv` | Create | Sprint ledger |

## Definition of Done

- [ ] `make all` runs without errors from a clean state
- [ ] `~/.claude/CLAUDE.md` is a symlink to `agents/claude/CLAUDE.md` and contains non-empty content
- [ ] `~/.codex/AGENTS.md` is a symlink to `agents/codex/CODEX.md`
- [ ] `~/.copilot/copilot-instructions.md` is a symlink to `agents/copilot/COPILOT.md`
- [ ] `~/.gemini/GEMINI.md` is a symlink to `agents/gemini/GEMINI.md`
- [ ] `~/.claude/skills/` → `skills/`; `~/.copilot/skills/` → `skills/`
- [ ] `~/.codex/skills/` does NOT exist (not created by this repo)
- [ ] `~/.gemini/skills/` does NOT exist (not created by this repo)
- [ ] `~/.claude/commands/` → `commands/`; `~/.codex/prompts/` → `commands/`
- [ ] `~/.copilot/commands/` does NOT exist (not created by this repo)
- [ ] `~/.gemini/commands/` → `build/gemini-commands/` and contains `.toml` files
- [ ] `~/.claude/agents/` → `subagents/`; `~/.copilot/agents/` → `subagents/`
- [ ] `~/.codex/agents/` does NOT exist (not created by this repo)
- [ ] `_GLOBAL.md` contains at least one meaningful shared instruction
- [ ] All four agent-specific `_<AGENT>.md` files contain at least a stub of agent-specific content
- [ ] README.md contains the agent capability matrix
- [ ] `docs/sprints/ledger.tsv` exists and contains SPRINT-001

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Gemini TOML conversion breaks on complex markdown | Medium | Medium | Test all 4 existing commands; keep conversion simple (strip frontmatter, wrap body) |
| `~/.agent/` directories don't exist on user's machine | High | Medium | Add `mkdir -p` before symlinking in `utils.sh` or each script |
| Codex global skills path is undocumented | Medium | Low | Skip for now; document the manual `config.toml` approach in README |
| Content written for `_GLOBAL.md` is too verbose and confuses agents | Medium | High | Keep instructions terse; test with each agent |
| Subagent format mismatch between Claude and Copilot | Medium | Medium | Defer agent-specific subagent support to a future sprint; keep `subagents/` empty for now |

## Security Considerations

- Scripts write to user's home directory; backup behavior prevents data loss
- TOML conversion uses shell string manipulation; no eval or arbitrary code execution
- Agent instruction files become part of each agent's system prompt; review content for prompt injection risks before populating
- Symlinks point to this repo's files; anyone who can write to the repo can influence agent behavior

## Dependencies

- No prior sprints
- Requires Bash 3.2+, standard Unix utilities (tr, cat, awk, sed, ln, mv, rm)
- Requires the user to have at least one CLI agent installed to verify symlinks load

## Open Questions

1. Should the Gemini command conversion happen at `make` time (in `build/`) or should we maintain a hand-authored `commands-gemini/` with `.toml` source files?
2. Should we include Codex global skills via `config.toml` manipulation, or simply document the manual step?
3. Subagent format differences (`.md` vs `.agent.md` for Copilot) — shared `subagents/` dir or per-agent `subagents/<agent>/`?
4. Should `_GLOBAL.md` content be written in Sprint 001 or deferred to allow the user to fill in their own preferences?
