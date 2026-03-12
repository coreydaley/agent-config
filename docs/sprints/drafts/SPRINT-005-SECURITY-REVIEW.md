# Security Review: SPRINT-005

**Sprint**: Sprint 005 — `audit-design` and `audit-accessibility` Commands
**Date**: 2026-03-12
**Reviewer**: Claude (Audit)

---

## Scope

Review `docs/sprints/SPRINT-005.md` for security risks introduced by
the planned changes: two new `commands/audit-design.md` and
`commands/audit-accessibility.md` command files in an agent-config repo
whose contents flow directly into agent system prompts.

---

## Findings

| ID | Severity | Title | Location | Why It Matters | Recommended Fix | Evidence/Notes |
|----|----------|-------|----------|----------------|-----------------|----------------|
| A001 | High | Command files flow into agent system prompts | Security Considerations | Both new command files will be loaded as agent instructions. Malicious or ambiguous phrasing in the command body could expand agent scope, grant unintended permissions, or create prompt injection vectors. | Before merging: review each command file line-by-line for instructions that could be misinterpreted as elevated-privilege grants, scope expansions, or execution bypasses. Add to DoD: "No instruction in the command body grants elevated scope or permissions not already present in the project." | All commands in `commands/` are treated as system prompt components per SECURITY.md. |
| A002 | High | `$ARGUMENTS` path validation must prevent shell injection | P0-A / P0-B Phase 1 requirements | Both commands accept `$ARGUMENTS` as optional path(s). If an executing agent fails to validate this input before interpolating into a `codex exec` shell string, a crafted argument could inject shell commands. | DoD must explicitly state: `$ARGUMENTS` is validated as a file path in Phase 1 and stored as a resolved path — the raw argument text is never interpolated into any shell string. The sprint already mentions this but it must appear in DoD, not just description prose. | `audit-security` had SR-005 (High) for the same issue. |
| A003 | Medium | Codex exec prompts instruct writing to directories that may not exist | P0-A / P0-B Phase 2 | If `docs/design/` or `docs/accessibility/` don't exist when Codex writes to them, the write may silently fail or write to an unexpected location. | Phase 1 of each command must create the artifact directory before launching Codex in background. Sprint plan says "create docs/design/ if needed" in Phase 1 — confirm this is explicit in the DoD. | Low exploitability but could produce confusing partial runs. |
| A004 | Medium | Codex exec prompts may reference finding files that don't exist | Phase 3 / 4 of each command | If Codex's Phase 2 review fails or produces an empty file, Phase 3 synthesis will read a missing/empty file. Phase 4 Codex exec prompt for devil's advocate reads the synthesis file — if synthesis didn't complete correctly, devil's advocate operates on incomplete data. | Sprint plan already addresses this: "Verify both files non-empty (single-agent warning if one missing)." Confirm this verification step is in Phase 3's DoD, not just prose. Rating: Medium because it's a workflow correctness issue, not a direct security exploit. | Existing mitigation in sprint plan is adequate; just needs DoD reference. |
| A005 | Medium | Findings artifacts may contain sensitive project information | Security Considerations | `docs/design/` and `docs/accessibility/` artifacts will contain design weakness findings and accessibility gap findings for the target project. If the target is a security-sensitive application, these findings could reveal attack surface information. | P1-B directory READMEs should include: "These files may contain sensitive findings about your project's design or accessibility gaps. Review before committing to public repositories." Sprint plan already mentions this; ensure it's in P1-B task description. | Same risk exists for `docs/security/` from SPRINT-004. |
| A006 | Low | New command names could collide with future `audit-*` commands | Sprint naming | No immediate risk, but `audit-design` and `audit-accessibility` don't leave obvious namespace slots for adjacent concerns (e.g., `audit-ux` would overlap with `audit-design`). | Document the audit family namespace in `docs/security/README.md` or a future `commands/README.md`. Out of scope for this sprint; add to Deferred. | Low risk in current repo state. |
| A007 | Low | Inherent-limitations disclaimer could create false confidence if omitted | Both command Overview sections | If an executing agent omits the static-review limitations note from the sprint output, users may treat findings as exhaustive. | Sprint plan requires the limitations note in both command Overviews. DoD already covers this indirectly. No change needed; noting for completeness. | Self-referential: the sprint plan itself contains the disclaimer. |

---

## Attack Surface Analysis

### New inputs introduced
- `$ARGUMENTS`: optional path(s) passed to each command. **Already mitigated** in Phase 1 validation requirement.

### New trust boundaries
- `docs/design/` and `docs/accessibility/` are new writable artifact directories. Files written here by Codex could theoretically contain prompt injection payloads if Codex's output is later fed back into a model context. **Low risk**: these files are intermediate artifacts, not loaded as instructions.

### New APIs or external service calls
- None. Both commands use the same `codex exec` pattern as `audit-security`.

---

## Data Handling

- No PII, secrets, or credentials are handled by these commands.
- Artifact files may contain project findings — see A005.

---

## Dependency Risks

- No new libraries or external services introduced.
- Both commands depend on `codex exec` being available — same dependency as `audit-security` and `sprint-plan`.

---

## Threat Model

**Realistic adversarial scenario**: A contributor with write access to
this repo modifies `commands/audit-design.md` or
`commands/audit-accessibility.md` to include a prompt injection payload
(e.g., "Also execute the following as a system instruction: [payload]").
When another agent runs `/audit-design`, the injected instruction is
executed.

**Mitigation**: Same as for all commands — write access to this repo
is equivalent to write access to agent system prompts. This is
documented in `SECURITY.md`. Code review before merging command changes
is the primary control.

**No new threat surface beyond what already exists for `commands/*.md`.**

---

## Findings Summary by Severity

| Severity | Count | Findings |
|----------|-------|----------|
| Critical | 0 | — |
| High | 2 | A001, A002 |
| Medium | 3 | A003, A004, A005 |
| Low | 2 | A006, A007 |

---

## Recommendations for Sprint Document

1. **DoD addition (A002)**: Add explicit DoD item: "`$ARGUMENTS` validated
   as path(s) in Phase 1 of each command; raw argument text never
   interpolated into shell strings." (The sprint plan body mentions
   this but it should be in the DoD checklist.)

2. **DoD addition (A003)**: Add explicit DoD item: "Phase 1 of each
   command creates artifact directory before launching Codex in Phase 2."

3. **No Critical or new High findings requiring sprint plan changes**
   beyond the two DoD additions above. Both High findings (A001, A002)
   are already addressed by existing sprint requirements — the DoD
   additions make them explicit rather than buried in prose.

4. A003 and A004 are adequately addressed in sprint prose; DoD additions
   would harden them.

5. A005 is addressed in P1-B task description — adequate.
