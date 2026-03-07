# Sprint 001 Intent: Agent-Config Repository Revamp

## Seed

This repository is meant to be a centralized location to manage all of your CLI agents like claude, codex, copilot, gemini, etc. It was originally written with good intentions but a fundamental misunderstanding of the differences between all of these agents' configurations on a user's local system. We need to account for all of the differences between how each of these agents are configured on the local filesystem and how we can use base configurations and sharing of skills, commands, etc between them. We want a plan to revamp this repository to be what it was meant to be, even if it is a complete rewrite. We should be able to share as much configuration between the agents as possible, but also allow for each agent to have its own instructions, skills, commands, etc, including any conversions that need to happen between file types.

## Context

This is the first sprint for this repository. The project was conceived as a dotfiles-style manager for AI CLI agent configurations, centralizing shared content (instructions, skills, commands, subagents) and symlinking it into each agent's expected home directory. However, the original implementation assumed all agents behave identically, which they do not.

Key issues discovered:

- **Agent config filenames differ**: `CLAUDE.md`, `AGENTS.md` (Codex), `copilot-instructions.md`, `GEMINI.md`
- **Commands format differs**: Claude uses `.md` in `commands/`; Codex uses `.md` but in `prompts/`; Copilot CLI has no custom commands feature; Gemini uses `.toml` format (incompatible)
- **Skills paths differ**: Claude `~/.claude/skills/`, Copilot `~/.copilot/skills/`, Codex reads `.agents/skills/` from project dirs (no standard global path), Gemini has no `skills/` convention (uses `@file.md` imports in GEMINI.md)
- **Subagent formats differ**: Claude uses `.md` in `agents/`; Copilot uses `.agent.md` in `~/.copilot/agents/`; Gemini uses `~/.gemini/agents/` with YAML frontmatter (name, description, tools fields); Codex has no native subagents
- **Agent instruction files are empty stubs**: `_GLOBAL.md`, `_CLAUDE.md`, `_CODEX.md`, `_COPILOT.md`, `_GEMINI.md` are all blank
- **The generate+symlink architecture is conceptually sound** but needs per-agent routing rules rather than a uniform loop

## Recent Sprint Context

No prior sprints exist. This is SPRINT-001 and represents the foundational work for the entire repository.

## Relevant Codebase Areas

| Area | Current State | Issue |
|---|---|---|
| `agents/` | Source + generated config files | All agent source files are empty; Codex symlinks to wrong filename |
| `scripts/generate-agent-files.sh` | Concatenates `_GLOBAL.md` + `_<AGENT>.md` | Only works for text merging; no format conversion |
| `scripts/symlink-agents.sh` | Symlinks per-agent to correct filename | Codex was wrong (now fixed to `AGENTS.md`) |
| `scripts/symlink-commands.sh` | Symlinks `commands/` to each agent | Copilot removed; Codex now points to `prompts/`; Gemini excluded |
| `scripts/symlink-skills.sh` | Symlinks `skills/` to each agent | Codex and Gemini paths are wrong/unsupported |
| `scripts/symlink-subagents.sh` | Symlinks `agents/` dir to each agent | Symlinks wrong source (should be `subagents/`); Codex unsupported |
| `skills/` | frontier-design, mcp-builder, skill-creator, ledger | Structured correctly for Claude; untested on others |
| `commands/` | commit.md, tag.md, sprint.md, superplan.md | Claude-compatible markdown; Gemini needs TOML conversion |
| `subagents/` | Empty | No subagents defined yet |

## Constraints

- Must preserve the generate+symlink architecture (it's the right model)
- Must not break existing Claude functionality
- Should support graceful degradation: if an agent doesn't support a feature, skip it cleanly
- Shell scripts must remain Bash 3.2+ compatible (macOS ships old bash)
- No new runtime dependencies beyond standard Unix utilities and the agents themselves
- Markdown files that agents read must not contain README/documentation content (would confuse agents)

## Success Criteria

1. Each agent's config file (`CLAUDE.md`, `AGENTS.md`, `copilot-instructions.md`, `GEMINI.md`) is correctly generated and symlinked to the right path
2. Skills are symlinked only to agents that support a `skills/` directory convention
3. Commands are symlinked/converted to the correct format and path for each agent that supports them
4. Subagents are symlinked only to agents that support an `agents/` directory
5. A shared base layer (`_GLOBAL.md`) provides common instructions that flow into every agent config
6. Agent-specific instruction files allow per-agent customization on top of the shared base
7. Running `make all` from a clean state produces all correct symlinks for all four agents
8. The repo structure and README clearly document what is and isn't supported per agent

## Verification Strategy

- Spec/documentation: Official docs for each agent (Claude Code docs, OpenAI Codex docs, GitHub Copilot docs, Gemini CLI docs) define what files each agent reads from where
- Manual verification: After `make all`, inspect `~/.claude/`, `~/.codex/`, `~/.copilot/`, `~/.gemini/` to confirm correct symlinks
- Edge cases: Agent doesn't have home directory yet; existing file at symlink destination; source file empty
- Compatibility testing: Confirm each agent actually loads the symlinked files

## Uncertainty Assessment

- **Correctness uncertainty: Medium** — Codex global skills path and subagent support are underdocumented; Gemini TOML command conversion needs prototyping
- **Scope uncertainty: High** — "complete rewrite" could mean many things; scope needs user input on what to include in Sprint 001 vs. later
- **Architecture uncertainty: Low** — The generate+symlink pattern is validated; per-agent routing is the clear solution

## Open Questions

1. Should the `commands/` → Gemini TOML conversion happen at `make` time (build step), or should we maintain parallel `.toml` source files?
2. Should agent-specific skills (skills only relevant to one agent) live in `skills/<agent>/` or in `agents/<agent>/skills/`?
3. Should we populate the shared `_GLOBAL.md` with actual content in this sprint, or define the architecture only and leave content population for later?
4. For Codex global skills, should we use `~/.codex/config.toml` registration or assume the user manages it manually?
5. What is the intended audience — personal use only, or designed for others to fork and use?
