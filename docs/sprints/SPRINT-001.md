# Sprint 001: Agent-Config Repository Revamp

## Overview

This sprint converts `agent-config` from a uniform-loop model to a capability-routed model. The original implementation assumed all AI CLI agents (Claude, Codex, Copilot, Gemini) accept configuration from the same paths in the same formats — they do not. Each agent reads different filenames, from different directories, in different file formats, with different feature support.

The generate+symlink architecture is correct and is preserved. What changes is that every script and Makefile target now routes by agent capability rather than iterating all agents uniformly. Unsupported features are skipped explicitly with logged output rather than silently miswired.

This is the foundational sprint for the repository. All subsequent work builds on the correct architecture established here.

## Guiding Principles

- Route by agent capabilities, not by agent name alone
- Preserve the current mental model: source in repo → generated artifacts in repo → symlinks into agent homes
- Skip unsupported features explicitly and log why (no silent no-ops)
- Bash 3.2+ compatibility; no non-standard runtime dependencies
- `make all` must be idempotent: repeated runs produce the same outcome without errors
- Generated artifacts for format conversions go to `build/` (gitignored); all other generated files stay in-place

## Agent Capability Matrix

| Feature | Claude | Codex | Copilot | Gemini |
|---|---|---|---|---|
| **Config file** | `~/.claude/CLAUDE.md` | `~/.codex/AGENTS.md` | `~/.copilot/copilot-instructions.md` | `~/.gemini/GEMINI.md` |
| **Config format** | Markdown | Markdown (AGENTS.md sections) | Markdown | Markdown |
| **Skills directory** | `~/.claude/skills/` | ❌ no standard global path | `~/.copilot/skills/` | ❌ no `skills/` convention |
| **Commands directory** | `~/.claude/commands/` (.md) | `~/.codex/prompts/` (.md) | ❌ not supported | `~/.gemini/commands/` (.toml) |
| **Subagents directory** | `~/.claude/agents/` (.md) | ❌ not supported | `~/.copilot/agents/` (.agent.md) | `~/.gemini/agents/` (.md + tools: field) |
| **Command format** | Markdown | Markdown | — | TOML (auto-converted) |

## Architecture

```
agent-config/
├── agents/
│   ├── _GLOBAL.md              # Shared instructions for all agents
│   ├── claude/
│   │   ├── _CLAUDE.md          # Claude-specific additions
│   │   └── CLAUDE.md           # Generated (_GLOBAL + _CLAUDE) → symlink → ~/.claude/CLAUDE.md
│   ├── codex/
│   │   ├── _CODEX.md           # Codex-specific additions
│   │   └── CODEX.md            # Generated (_GLOBAL + _CODEX)  → symlink → ~/.codex/AGENTS.md
│   ├── copilot/
│   │   ├── _COPILOT.md         # Copilot-specific additions
│   │   └── COPILOT.md          # Generated (_GLOBAL + _COPILOT) → symlink → ~/.copilot/copilot-instructions.md
│   └── gemini/
│       ├── _GEMINI.md          # Gemini-specific additions
│       └── GEMINI.md           # Generated (_GLOBAL + _GEMINI)  → symlink → ~/.gemini/GEMINI.md
│
├── skills/                     # Shared skills (SKILL.md format)
│   [symlinked to: ~/.claude/skills/, ~/.copilot/skills/]
│   [skipped for: codex (no standard path), gemini (uses @imports)]
│
├── commands/                   # Shared commands (Markdown source of truth)
│   [symlinked to: ~/.claude/commands/, ~/.codex/prompts/]
│   [auto-converted to TOML → build/gemini-commands/ → ~/.gemini/commands/]
│   [skipped for: copilot (feature not supported)]
│
├── subagents/                  # Shared subagent definitions (superset frontmatter)
│   [symlinked to: ~/.claude/agents/, ~/.gemini/agents/]
│   [P1: .agent.md conversion → ~/.copilot/agents/]
│   [skipped for: codex (not supported)]
│
├── build/                      # Generated artifacts — gitignored
│   └── gemini-commands/        # Auto-converted .toml files for Gemini
│
├── scripts/
│   ├── utils.sh                # Shared helpers (create_symlink, ensure_dir)
│   ├── generate-agent-files.sh # Merges _GLOBAL + _<AGENT> → <AGENT>.md
│   ├── generate-gemini-commands.sh  # NEW: commands/*.md → build/gemini-commands/*.toml
│   ├── symlink-agents.sh       # Agent config symlinks (per-agent filename routing)
│   ├── symlink-skills.sh       # Skills symlinks (Claude + Copilot only)
│   ├── symlink-commands.sh     # Command symlinks (Claude + Codex + Gemini)
│   └── symlink-subagents.sh    # Subagent symlinks (Claude + Gemini; Copilot in P1)
│
├── Makefile
├── README.md
└── .gitignore
```

### Data Flow

```
_GLOBAL.md ─┬─► CLAUDE.md  ─► symlink ─► ~/.claude/CLAUDE.md
_CLAUDE.md ─┘

_GLOBAL.md ─┬─► CODEX.md   ─► symlink ─► ~/.codex/AGENTS.md
_CODEX.md  ─┘

_GLOBAL.md ──┬─► COPILOT.md ─► symlink ─► ~/.copilot/copilot-instructions.md
_COPILOT.md ─┘

_GLOBAL.md ─┬─► GEMINI.md  ─► symlink ─► ~/.gemini/GEMINI.md
_GEMINI.md ─┘

skills/    ─────────────────────────────► ~/.claude/skills/
                                        ► ~/.copilot/skills/
                              (skipped)   codex, gemini

commands/  ─────────────────────────────► ~/.claude/commands/
           ─────────────────────────────► ~/.codex/prompts/
           ─► md→toml conversion ───────► build/gemini-commands/ ─► ~/.gemini/commands/
                              (skipped)   copilot

subagents/ ─────────────────────────────► ~/.claude/agents/
           ─────────────────────────────► ~/.gemini/agents/
           ─► P1: .agent.md conversion ─► ~/.copilot/agents/
                              (skipped)   codex
```

## P0: Must Ship

### P0-A: Agent Config Generation and Symlinks

**Goal**: All four agents receive a correctly named, non-empty config file at the correct path.

**Files:**
- `agents/_GLOBAL.md` — write minimal shared content stub
- `agents/claude/_CLAUDE.md` — write Claude-specific stub
- `agents/codex/_CODEX.md` — write Codex-specific stub
- `agents/copilot/_COPILOT.md` — write Copilot-specific stub
- `agents/gemini/_GEMINI.md` — write Gemini-specific stub
- `scripts/generate-agent-files.sh` — add error on missing source files; add `gemini`
- `scripts/symlink-agents.sh` — verify all four targets; add `mkdir -p` for agent home dirs

**Tasks:**
- [ ] Write minimal (non-empty) stub content for `_GLOBAL.md` — shared behavior conventions, commit style, disclaimer
- [ ] Write `_CLAUDE.md` stub — Claude tools awareness, memory, hooks
- [ ] Write `_CODEX.md` stub — Codex sandbox awareness, AGENTS.md section guidance
- [ ] Write `_COPILOT.md` stub — Copilot PR focus, GitHub integration context
- [ ] Write `_GEMINI.md` stub — Gemini Google ecosystem context, @import usage note
- [ ] Update `generate-agent-files.sh`: fail explicitly if `_GLOBAL.md` or `_<AGENT>.md` is missing
- [ ] Update `symlink-agents.sh`: add `ensure_dir` call before each symlink to create `~/.<agent>/` if absent
- [ ] Run `make generate && make symlink-agents` and verify all four symlinks resolve to non-empty files

**Acceptance:**
- `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, `~/.copilot/copilot-instructions.md`, `~/.gemini/GEMINI.md` all exist, are symlinks to the correct source, and contain non-empty content

### P0-B: Skills Routing Fix

**Goal**: Skills only symlink to agents with a supported `skills/` directory convention.

**Files:**
- `scripts/symlink-skills.sh` — restrict to Claude and Copilot; emit skip messages for Codex and Gemini

**Tasks:**
- [ ] Remove Codex and Gemini from the skills loop
- [ ] Add explicit `echo "Skipping skills for codex: no standard global skills directory"` and equivalent for Gemini
- [ ] Verify `~/.claude/skills/` and `~/.copilot/skills/` are created; `~/.codex/skills/` and `~/.gemini/skills/` are not

### P0-C: Commands Routing Fix + Gemini Conversion Pipeline

**Goal**: Commands reach the correct path per agent; Gemini receives TOML-format files auto-converted from Markdown source.

**Files:**
- `scripts/symlink-commands.sh` — already corrected (Claude→commands/, Codex→prompts/, Copilot removed); add Gemini
- `scripts/generate-gemini-commands.sh` — NEW: reads `commands/*.md`, strips YAML frontmatter, outputs `.toml` to `build/gemini-commands/`
- `scripts/symlink-gemini-commands.sh` — NEW: symlinks `build/gemini-commands/` → `~/.gemini/commands/`
- `.gitignore` — add `build/`
- `Makefile` — add `generate-gemini-commands` and `symlink-gemini-commands` targets

**Conversion spec** (`commands/*.md` → `build/gemini-commands/*.toml`):
```
# Input: YAML frontmatter + Markdown body
---
description: Short description here
disable-model-invocation: true    ← strip (Claude-specific)
allowed-tools: Bash(git *)        ← strip (Claude-specific)
---
# Command body...

# Output: TOML
description = "Short description here"
prompt = """
# Command body...
"""
```

**Conversion constraints** (scope the awk parser to what we know works):
- Only single-line YAML values are supported; multiline YAML frontmatter values are not handled
- `description:` must exist and be a single-line string; conversion fails loudly if absent
- Only `description:` is extracted; all other frontmatter fields are stripped
- The entire Markdown body (after closing `---`) becomes the TOML `prompt` value verbatim
- Embedded TOML syntax or triple-quoted strings in the body are a known limitation; document it

**Tasks:**
- [ ] Write `scripts/generate-gemini-commands.sh` using `awk` to extract `description` from frontmatter and command body as TOML prompt
- [ ] Write `scripts/symlink-gemini-commands.sh`
- [ ] Add `build/` to `.gitignore`
- [ ] Add `generate-gemini-commands` Makefile target (runs as part of `generate`)
- [ ] Add `symlink-gemini-commands` Makefile target (runs as part of `symlinks`)
- [ ] Add `generate-gemini-commands` to the `generate` Makefile target group
- [ ] Add `symlink-gemini-commands` to the `symlinks` Makefile target group
- [ ] Test conversion for all four existing commands: `commit.md`, `tag.md`, `sprint.md`, `superplan.md`
- [ ] Verify `~/.gemini/commands/` points to `build/gemini-commands/` and contains `.toml` files

### P0-D: Subagents Routing Fix

**Goal**: Subagents symlink from the correct source (`subagents/`, not `agents/`) to the correct agents.

**Files:**
- `scripts/symlink-subagents.sh` — fix source to `subagents/`; route to Claude and Gemini; skip Codex; defer Copilot

**Tasks:**
- [ ] Change symlink source from `$ROOT_DIR/agents` to `$ROOT_DIR/subagents`
- [ ] Remove Codex from loop; add explicit skip message
- [ ] Keep Gemini in loop (`~/.gemini/agents/`) — symlink the shared dir; document `tools:` frontmatter requirement
- [ ] For Copilot: emit skip message noting P1 `.agent.md` conversion step is pending
- [ ] Verify `~/.claude/agents/` → `subagents/`; `~/.gemini/agents/` → `subagents/`

### P0-E: Documentation Update

**Goal**: README and agents README accurately reflect the capability matrix and correct paths.

**Files:**
- `README.md` — update Setup section and add capability matrix table
- `agents/README.md` — update to reflect all four agents and correct symlink targets

**Tasks:**
- [ ] Add capability matrix table to `README.md`
- [ ] Update Setup section to reference per-agent differences
- [ ] Add "What's not supported per agent" callout in `README.md`
- [ ] Update `agents/README.md` symlink target table (`~/.codex/AGENTS.md`, not `CODEX.md`)

### P0-F: utils.sh Hardening

**Files:**
- `scripts/utils.sh` — add `ensure_dir` function

**Tasks:**
- [ ] Add `ensure_dir()` that creates a directory if it doesn't exist: `mkdir -p "$1"`
- [ ] Use `ensure_dir` in all symlink scripts before the symlink creation step

## P1: Ship If Capacity Allows

### P1-A: Codex Skills via config.toml

**Goal**: Register this repo's skills with Codex by appending `[[skills.config]]` entries to `~/.codex/config.toml`.

**Files:**
- `scripts/configure-codex-skills.sh` — NEW: reads skills from `skills/` and appends TOML entries to `~/.codex/config.toml` (does not overwrite; appends if entry not already present)
- `Makefile` — add optional `configure-codex-skills` target

**Notes:** This script modifies a user config file. It must be idempotent (check for duplicate entries before writing), and must be a separate explicit target (`make configure-codex-skills`), not part of `make all`. It must back up `~/.codex/config.toml` to `~/.codex/config.toml.old` before making any changes.

### P1-B: Copilot Subagent Conversion

**Goal**: Convert `subagents/*.md` to `.agent.md` format for Copilot.

**Files:**
- `scripts/generate-copilot-subagents.sh` — NEW: copies `subagents/*.md` to `build/copilot-agents/*.agent.md`
- `scripts/symlink-copilot-subagents.sh` — NEW: symlinks `build/copilot-agents/` → `~/.copilot/agents/`

**Notes:** Copilot reads `~/.copilot/agents/*.agent.md`. Files need the `.agent.md` extension. Since Claude ignores unknown frontmatter fields, the superset format in `subagents/*.md` (with `tools:` field) is compatible with both; only the extension needs changing for Copilot.

### P1-C: Dry-Run Mode

Add `--dry-run` flag to all symlink scripts that prints what would be done without making changes.

## Deferred (Not This Sprint)

- Sprint ledger `ledger.tsv` initialization (being bootstrapped by the superplan process itself)
- Rich agent instruction content authoring (stubs only in Sprint 001)
- Migration of in-place generated files to a `generated/` tree
- Multi-OS portability beyond macOS/Linux

## Files Summary

| File | Action | Purpose |
|---|---|---|
| `agents/_GLOBAL.md` | Write | Shared agent instructions stub |
| `agents/claude/_CLAUDE.md` | Write | Claude-specific stub |
| `agents/codex/_CODEX.md` | Write | Codex-specific stub |
| `agents/copilot/_COPILOT.md` | Write | Copilot-specific stub |
| `agents/gemini/_GEMINI.md` | Write | Gemini-specific stub |
| `scripts/generate-agent-files.sh` | Modify | Fail on missing sources |
| `scripts/symlink-agents.sh` | Modify | Add `ensure_dir`; all four agents |
| `scripts/symlink-skills.sh` | Modify | Claude + Copilot only; skip Codex + Gemini |
| `scripts/symlink-commands.sh` | Modify | Add Gemini target |
| `scripts/symlink-subagents.sh` | Modify | Fix source; Claude + Gemini; skip Codex; defer Copilot |
| `scripts/utils.sh` | Modify | Add `ensure_dir()` |
| `scripts/generate-gemini-commands.sh` | Create | md→toml conversion |
| `scripts/symlink-gemini-commands.sh` | Create | Symlink Gemini commands |
| `Makefile` | Modify | New targets for Gemini commands |
| `.gitignore` | Modify | Add `build/` |
| `README.md` | Modify | Capability matrix, correct paths |
| `agents/README.md` | Modify | Correct symlink targets |

## Definition of Done

### P0 Acceptance Criteria

- [ ] `make all` succeeds from a clean state with no errors
- [ ] `make all` run a second time produces the same outcome (idempotent)
- [ ] `~/.claude/CLAUDE.md` → `agents/claude/CLAUDE.md` (non-empty)
- [ ] `~/.codex/AGENTS.md` → `agents/codex/CODEX.md` (non-empty)
- [ ] `~/.copilot/copilot-instructions.md` → `agents/copilot/COPILOT.md` (non-empty)
- [ ] `~/.gemini/GEMINI.md` → `agents/gemini/GEMINI.md` (non-empty)
- [ ] `~/.claude/skills/` → `skills/`
- [ ] `~/.copilot/skills/` → `skills/`
- [ ] `~/.codex/skills/` is NOT a symlink from this repo (Codex manages this directory itself)
- [ ] `~/.gemini/skills/` does NOT exist (not created by this repo)
- [ ] `~/.claude/commands/` → `commands/`
- [ ] `~/.codex/prompts/` → `commands/`
- [ ] `~/.gemini/commands/` → `build/gemini-commands/` (contains `.toml` files)
- [ ] `~/.copilot/commands/` does NOT exist (not created by this repo)
- [ ] `~/.claude/agents/` → `subagents/`
- [ ] `~/.gemini/agents/` → `subagents/`
- [ ] `~/.codex/agents/` does NOT exist
- [ ] Scripts emit explicit skip messages for unsupported features (not silent)
- [ ] `generate-agent-files.sh` fails with a clear error if source files are missing
- [ ] `README.md` contains the agent capability matrix
- [ ] Each converted `.toml` file is manually inspected to confirm `description` and `prompt` fields are present and correct for all four existing commands
- [ ] Post-conversion check: converted `.toml` files do not contain unbalanced `"""` sequences (run `grep -c '"""' build/gemini-commands/*.toml` and verify even counts)
- [ ] Claude Code is launched and confirms it loads `CLAUDE.md` (behavioral validation, at minimum for Claude)
- [ ] Capability matrix table in README cites the doc version/date for each agent's official documentation
- [ ] README includes a security callout warning that repo contents flow directly into agent system prompts and should be reviewed before use

## Execution Order

1. `utils.sh`: add `ensure_dir`
2. Agent source files: write minimal stubs
3. `generate-agent-files.sh`: harden; run `make generate`
4. `symlink-agents.sh`: harden; run `make symlink-agents`
5. `symlink-skills.sh`: fix routing; run `make symlink-skills`
6. `symlink-subagents.sh`: fix source + routing; run `make symlink-subagents`
7. `generate-gemini-commands.sh`: implement and test (inspect converted .toml files manually)
8. `symlink-commands.sh` + `symlink-gemini-commands.sh`: wire up; run `make symlink-commands`
9. Makefile: add new targets; run `make all` end-to-end
10. Behavioral validation: launch Claude Code and confirm it loads `CLAUDE.md`; inspect `~/.gemini/commands/` .toml files
11. Docs: update README + agents/README (after behavior is confirmed, not before)
12. Final: run `make all` twice to verify idempotency

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Gemini TOML conversion breaks on complex markdown | Medium | Medium | Test all 4 existing commands; lock conversion spec with fixtures |
| `~/.agent/` dirs don't exist on a fresh machine | High | Medium | `ensure_dir` in `utils.sh` called before every symlink |
| Codex `config.toml` modification causes unexpected behavior | Medium | High | P1-A is a separate explicit `make` target; never runs as part of `make all` |
| Content stubs are so minimal they don't smoke-test the pipeline | Low | Low | Require at least one non-whitespace line in each source file |
| Gemini subagent format incompatibility breaks Gemini agent loading | Low | Medium | Symlink only; add README note on required `tools:` frontmatter field |

## Security Considerations

- All scripts write to `~/.<agent>/` directories; backup behavior in `utils.sh` prevents data loss
- TOML conversion uses `awk` string manipulation with no `eval` or shell injection surface
- Agent instruction files become part of each agent's system prompt — review `_GLOBAL.md` content for unintended instructions before populating
- P1-A (`configure-codex-skills.sh`) appends to `~/.codex/config.toml`; must be idempotent and must not corrupt existing entries
- Symlinks point into this repo; anyone with write access to the repo can influence all four agents' behavior

## Open Questions Resolved

| Question | Answer |
|---|---|
| Gemini commands: build-time or parallel source? | Auto-convert at build time |
| Subagents: single dir or per-agent dirs? | Single dir, superset frontmatter |
| Agent file content in Sprint 001? | Minimal stubs (non-empty, smoke-test-ready) |
| Codex skills? | P1: optional `configure-codex-skills.sh`; not part of `make all` |
| Gemini subagents? | Symlink in P0, format docs only; .agent.md conversion in P1 |
