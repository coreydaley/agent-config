# Sprint 003 Security Review

Reviewed: `docs/sprints/SPRINT-003.md`
Reviewer: Claude (Sonnet 4.6)

## 1. Attack Surface

**New trust boundary: ledger skill becomes model-invocable**

- **Rating: Medium**
- Before this sprint: `disable-model-invocation: true` meant only human users could invoke the ledger skill. After: any model-executed command (not just `/sprint`) can call `/ledger` with any subcommand.
- Realistic concern: If a prompt injection payload were to reach Claude's execution context (e.g. via sprint document content, agent instructions, or an external source), it could trigger `/ledger` state mutations (marking sprints in_progress, completed, skipped) without user awareness.
- Mitigation in plan: `allowed-tools: Bash(python3 *)` limits execution to python3 subprocesses; ledger.py only writes to `docs/sprints/ledger.tsv` and reads from `docs/sprints/SPRINT-*.md`. No network access, no shell expansion, no external data exfiltration path.
- **Recommended DoD addition**: Add a note to the sprint that the ledger skill, once model-invocable, is limited to the local `ledger.py` script. Document this scope in `skills/ledger/SKILL.md` body text so future readers understand the intent.

**sprint.md guidance surfaces user-facing decisions**

- **Rating: Low**
- The soft in-progress prompt and no-planned-sprint messaging become part of Claude's output to users. These messages could be manipulated if sprint document titles or ledger entries contain injection-adjacent content (e.g. a sprint titled with markdown that mimics a system instruction).
- ledger.py reads sprint titles from `SPRINT-*.md` first-line headers and from ledger.tsv. Both are repo-controlled files.
- Rating stays Low: this repo is owner-controlled; no untrusted external content flows into sprint titles.

## 2. Data Handling

- **Rating: Low**
- `ledger.tsv` contains only: sprint IDs, titles, statuses, and ISO timestamps. No PII, secrets, or credentials.
- `ledger.py` reads from and writes to this file only. No network I/O.
- `sprint.md` and `skills/ledger/SKILL.md` are text instruction files; they contain no sensitive data.
- No new data flows introduced.

## 3. Injection and Parsing Risks

- **Rating: Low**
- `ledger.py` uses `sys.argv` for command arguments. The arguments passed from the Skill tool are the subcommand string (e.g. `stats`, `start 003`). These are passed through Python's `sys.argv`, not `eval` or `shell -c`.
- `allowed-tools: Bash(python3 *)` means the skill is called as `python3 <path>/ledger.py <args>`. The args come from the Skill tool invocation text in the command, not from user-controlled external input.
- One mild risk: if `$ARGUMENTS` in the ledger SKILL.md body is interpolated and a sprint ID contains shell metacharacters, there could be argument injection. However: sprint IDs are always 3-digit zero-padded integers (enforced by `SprintEntry.__post_init__`); this risk does not materialize in practice.
- No new parsers introduced.

## 4. Authentication / Authorization

- **Rating: Low**
- This sprint introduces no auth flows or permission checks.
- The only authorization change is enabling model invocation of the ledger skill. The "authorization" model here is Claude Code's permission system: the user must have granted the Skill tool access.
- No gaps introduced.

## 5. Dependency Risks

- **Rating: Low**
- No new libraries introduced.
- `ledger.py` uses only Python standard library (`sys`, `re`, `dataclasses`, `datetime`, `pathlib`, `typing`). No new third-party dependencies.
- No new external services.

## 6. Threat Model

**Scenario: prompt injection via sprint document content**

The most realistic adversarial scenario given this sprint's changes:
1. An attacker contributes a sprint document (`SPRINT-NNN.md`) with content crafted to manipulate Claude's behavior when `/sprint` reads it — for example, injecting instructions like "mark all other sprints as completed" or "call `/ledger skip 001`".
2. After this sprint, Claude now has Skill tool access to `/ledger`, meaning the injected instruction could actually execute a ledger mutation.

**Assessment**: This threat exists regardless of this sprint — the sprint command already instructs Claude to read and execute sprint documents, and a malicious document could influence Claude's behavior. This sprint increases the blast radius slightly (ledger mutations are now in scope), but the mitigation is identical to the project's existing defense: repo access control. Only repo contributors can create `SPRINT-*.md` files.

**Mitigation in place**: The `CLAUDE.md` (global) already contains: "This repository contains AI-generated content. Review all configurations, scripts, and instructions before use in production or sensitive environments." This is the appropriate defense for a tool that processes repo-controlled content.

**No Critical or High findings identified.**

## Findings Summary

| Finding | Rating | Action |
|---------|--------|--------|
| Ledger skill becomes model-invocable (expanded trust boundary) | Medium | Add scope documentation to ledger SKILL.md body; already mitigated by `allowed-tools` |
| sprint.md output surfaces sprint titles (injection-adjacent) | Low | No action; repo-controlled content only |
| ledger.py argument handling | Low | No action; integer-enforced sprint IDs |
| No auth changes | Low | No action |
| No new dependencies | Low | No action |
| Prompt injection via sprint doc content | Medium | No new action; existing repo access control is the defense; documented in CLAUDE.md |

## Recommended Sprint Document Addition

Add to `skills/ledger/SKILL.md` body text (after removing `disable-model-invocation: true`) a brief note clarifying that this skill is intended for use within the `/sprint` command workflow, so future maintainers understand the model-invocable scope is intentional and bounded.

This is a **Low**-severity recommendation (no security requirement added to DoD); it is a documentation hygiene improvement.
