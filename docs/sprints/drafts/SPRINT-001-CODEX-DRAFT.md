# SPRINT-001 Codex Draft: Agent-Config Revamp Plan

## Sprint Objective
Establish a reliable, agent-aware generate+symlink system that supports Claude, Codex, Copilot, and Gemini without assuming feature parity, while preserving existing Claude behavior and documenting exact support boundaries.

## Problem Statement
The current repository architecture is directionally correct (shared source + generated outputs + symlink installation), but implementation details treat agents as interchangeable. That causes incorrect paths, wrong formats, and unsupported feature wiring for several agents.

Sprint-001 will convert the repo from a uniform loop model to a capability-routed model.

## Guiding Principles
- Preserve the current mental model: source in repo, generated artifacts in repo, symlinks into agent homes.
- Route by capabilities, not by agent name alone.
- Skip unsupported features explicitly and log why.
- Keep Bash 3.2 compatibility and avoid non-standard runtime dependencies.
- Prefer deterministic generation outputs so `make all` is repeatable.

## Scope

### In Scope
1. Correct per-agent config generation and symlink targets.
2. Capability-aware command, skill, and subagent setup logic.
3. Gemini command conversion pipeline (Markdown command source to Gemini-compatible output format).
4. Subagent source routing fix (`subagents/` as source, not `agents/`).
5. Repo documentation updates describing exact support matrix and behavior.
6. Validation workflow proving `make all` works from clean state.

### Out of Scope
1. Rich content authoring for `_GLOBAL.md` and per-agent instruction files beyond minimum representative seed content.
2. Advanced Codex global skill registration automation via `~/.codex/config.toml` unless minimal and reliable.
3. Multi-OS portability beyond current macOS/Linux shell assumptions.
4. New product features outside setup/install architecture.

## Baseline Assessment (Current)
- `generate-agent-files.sh`: basic concat works; no format-aware generation.
- `symlink-agents.sh`: target filenames mostly corrected (Codex uses `AGENTS.md`), but generation naming still inconsistent (`CODEX.md` source naming retained internally).
- `symlink-skills.sh`: wrongly includes agents without stable `skills/` directory conventions.
- `symlink-commands.sh`: Claude/Codex only; no Gemini conversion path.
- `symlink-subagents.sh`: links wrong source (`agents/` instead of `subagents/`) and includes unsupported agents.
- Agent source files are empty, leaving generated outputs effectively blank.

## Target Design

### 1) Capability Matrix (Authoritative)
Define and document this matrix in repo docs and script comments.

- Claude
  - Config file: `~/.claude/CLAUDE.md`
  - Skills dir: supported (`~/.claude/skills`)
  - Commands: supported (`~/.claude/commands`, Markdown)
  - Subagents: supported (`~/.claude/agents`, Markdown-based)
- Codex
  - Config file: `~/.codex/AGENTS.md`
  - Skills dir: no canonical global symlink target in current model; treat as unsupported for Sprint-001
  - Commands/prompts: supported via `~/.codex/prompts` (Markdown)
  - Subagents: unsupported in current model
- Copilot CLI
  - Config file: `~/.copilot/copilot-instructions.md`
  - Skills dir: supported (`~/.copilot/skills`)
  - Commands: unsupported
  - Subagents: supported (`~/.copilot/agents`) with required filename conventions
- Gemini CLI
  - Config file: `~/.gemini/GEMINI.md`
  - Skills dir: unsupported (no `skills/` directory convention)
  - Commands: supported only through Gemini-compatible format, generated from source
  - Subagents: supported (`~/.gemini/agents`) with Gemini format requirements

### 2) Repository Layout Rules
- Shared source remains in:
  - `agents/_GLOBAL.md`
  - `agents/<agent>/_<AGENT>.md`
  - `commands/*.md` (canonical source)
  - `subagents/*` (canonical source)
- Generated outputs go to a dedicated generated tree to prevent source/derived confusion:
  - `generated/agents/<agent>/...`
  - `generated/commands/gemini/...` (converted outputs)
  - `generated/subagents/<agent>/...` (if conversion needed)

If maintaining generated artifacts inside `agents/<agent>/` is required for compatibility, keep current location in Sprint-001 and defer generated tree migration to Sprint-002. Choose one path and document it.

### 3) Script Model
Refactor script behavior from hardcoded loops to feature-specific routing tables.

- `generate-agent-files.sh`
  - Keep merge behavior for instruction files.
  - Add guardrails for missing source files with explicit failures.
- `symlink-agents.sh`
  - Keep explicit mapping table for destination filenames.
  - Ensure parent directories exist before linking.
- `symlink-skills.sh`
  - Only link for agents with stable skills support (Claude, Copilot).
  - Emit clear skip messages for unsupported agents.
- `symlink-commands.sh`
  - Link Markdown commands for Claude and Codex.
  - Trigger Gemini conversion output generation and link converted directory/file(s) to Gemini path.
- `symlink-subagents.sh`
  - Use `subagents/` as source.
  - Route only to supported agents and apply per-agent filename/format transforms where required.

## Workstreams and Tasks

### Workstream A: Instruction File Pipeline
1. Validate and generate merged agent files for all four agents.
2. Standardize naming expectations in scripts/docs (`AGENTS.md` destination for Codex, internal generated source naming clearly documented).
3. Add explicit error if `_GLOBAL.md` or `_<AGENT>.md` missing.

Deliverables:
- Updated `scripts/generate-agent-files.sh`
- Updated `scripts/symlink-agents.sh`
- Non-empty placeholder content in source instruction files for smoke testing.

### Workstream B: Skills Routing
1. Restrict skills symlinking to supported agents only.
2. Add skip logs for unsupported agents.
3. Document Codex skill approach as manual/out-of-scope for this sprint unless finalized.

Deliverables:
- Updated `scripts/symlink-skills.sh`
- README compatibility table update.

### Workstream C: Commands Routing + Gemini Conversion
1. Keep `commands/*.md` as canonical source.
2. Implement conversion script for Gemini command format.
3. Ensure conversion runs before Gemini command symlink step.
4. Validate converted artifacts for all command files.

Deliverables:
- New conversion script (for example `scripts/generate-gemini-commands.sh`)
- Updated `scripts/symlink-commands.sh`
- Generated Gemini command artifacts and doc.

### Workstream D: Subagents Routing
1. Correct source path from `agents/` to `subagents/`.
2. Implement per-agent compatibility logic:
  - Claude: direct symlink if format compatible.
  - Copilot: apply `.agent.md` naming if needed.
  - Gemini: apply required frontmatter/format transform if needed.
3. Skip Codex cleanly with message.

Deliverables:
- Updated `scripts/symlink-subagents.sh`
- Optional conversion helper scripts for Copilot/Gemini subagent formats.

### Workstream E: Documentation and Developer UX
1. Update root `README.md` to represent actual feature support and paths.
2. Update `agents/README.md` to reflect current targets and naming.
3. Add a concise “Support Matrix” section and examples.
4. Add troubleshooting for existing file backups (`.old`).

Deliverables:
- Updated docs with verified commands and expected filesystem outputs.

## Execution Order
1. Capability matrix + support policy freeze.
2. Instruction generation/symlink correctness.
3. Skills routing fix.
4. Commands routing and Gemini conversion.
5. Subagents routing and conversion.
6. Documentation alignment.
7. End-to-end verification from clean state.

## Acceptance Criteria
1. `make all` succeeds from clean repo state on Bash 3.2+.
2. Agent config symlinks are correct:
  - `~/.claude/CLAUDE.md`
  - `~/.codex/AGENTS.md`
  - `~/.copilot/copilot-instructions.md`
  - `~/.gemini/GEMINI.md`
3. Skills symlinked only where supported (minimum: Claude + Copilot).
4. Commands installed only where supported; Gemini receives converted format artifacts.
5. Subagents symlinked from `subagents/` only for supported agents.
6. Unsupported features are skipped with explicit script output, not silent no-ops.
7. README and agents README match actual script behavior.

## Verification Plan

### Automated/Scripted Checks
- `make generate`
- `make symlinks`
- `make all`
- Script-level sanity checks:
  - Source paths exist before link
  - Destination parent directories are created as needed
  - Broken symlink detection after install

### Manual Validation
Inspect each destination in home directory after `make all`:
- `~/.claude/`
- `~/.codex/`
- `~/.copilot/`
- `~/.gemini/`

Confirm:
- symlink targets resolve
- expected files exist
- unsupported features are absent

### Behavioral Validation
Run each agent and verify it loads:
- primary instructions file
- commands/prompts where supported
- skills/subagents where supported

## Risks and Mitigations
- Risk: Gemini conversion spec ambiguity.
  - Mitigation: implement converter behind clear interface and lock with fixture examples.
- Risk: Codex skills path uncertainty.
  - Mitigation: explicitly defer and document manual setup in Sprint-001.
- Risk: Over-scoping into broad repo rewrite.
  - Mitigation: enforce capability-driven minimum viable architecture first.
- Risk: Silent breakage from stale docs.
  - Mitigation: doc updates are in-sprint deliverable with verification checklist.

## Definition of Done
- All acceptance criteria pass.
- Scripts are idempotent: repeated runs do not drift or fail unexpectedly.
- Unsupported combinations are explicitly documented and cleanly skipped.
- Sprint artifacts include:
  - updated scripts
  - updated docs
  - recorded verification outputs/checklist

## Decisions Needed Before Implementation (Blockers)
1. Gemini command conversion strategy:
  - Option A: convert at build/symlink time from Markdown source.
  - Option B: maintain separate Gemini-native command source files.
  - Recommendation: Option A for single source of truth.
2. Generated artifact location:
  - Option A: keep current in-place generated files.
  - Option B: move to `generated/` tree.
  - Recommendation: Option A in Sprint-001, Option B as follow-up.
3. Codex skills handling:
  - Option A: defer and document manual config.
  - Option B: add optional config helper script.
  - Recommendation: Option A in Sprint-001 for reliability.

## Proposed Sprint Deliverable List
1. Corrected and hardened scripts:
  - `scripts/generate-agent-files.sh`
  - `scripts/symlink-agents.sh`
  - `scripts/symlink-skills.sh`
  - `scripts/symlink-commands.sh`
  - `scripts/symlink-subagents.sh`
  - optional converter helpers
2. Updated docs:
  - `README.md`
  - `agents/README.md`
  - any new compatibility/support matrix doc
3. Validation artifacts:
  - command checklist and expected path map
  - before/after behavior notes

## Stretch Goals (Only If Core Is Complete)
1. Add lightweight test harness script to validate symlink graph automatically.
2. Add dry-run mode to scripts for auditability.
3. Add lint/check target for script shell safety (if zero-dependency path is acceptable).
