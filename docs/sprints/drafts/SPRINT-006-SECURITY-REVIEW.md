# Security Review: SPRINT-006 `audit-architecture` Command

## Scope

`docs/sprints/SPRINT-006.md` — the sprint plan for creating
`commands/audit-architecture.md`.

## Summary

This sprint creates a command file that gets loaded into agent system prompts. The
primary security surface is: (1) the command file itself being used as a system prompt
injection vector, (2) `$ARGUMENTS` handling in Phase 1, (3) Codex exec prompt
construction. The risk profile is similar to `audit-security` (SPRINT-004); the
same mitigations apply.

---

## Findings

### SR-001 — `$ARGUMENTS` Path Injection into Codex exec Prompts

**Severity: High**

**Attack surface**: Phase 1 validates `$ARGUMENTS` as a path, but the command
instructs the implementing agent to substitute the "resolved scope" into `codex exec`
prompt strings. If the validating agent passes the raw argument rather than a resolved
path, a malicious argument like `src/ && rm -rf /` or a path containing backticks
could be interpolated into the shell string passed to `codex exec`.

**Evidence**: The plan says "store resolved paths — never interpolate raw `$ARGUMENTS`
into shell strings" but does not specify what validation means (does it require the
path to exist via `stat`, or just that it doesn't look like a shell injection?).

**Mitigation**: The command body should explicitly state: validate `$ARGUMENTS` using
`ls` or equivalent to confirm the path exists before using it anywhere; the resolved
scope passed to Codex exec prompts must be the filesystem path, not the raw argument
string. The plan's existing language is directionally correct but needs this
specificity in the actual command file.

**DoD addition**: Add explicit check — "Phase 1 validates each path in `$ARGUMENTS`
confirms it exists before storing as resolved scope."

**Rating**: High — this pattern is the same risk mitigated in SPRINT-004 (SR-005).
Consistent treatment required.

---

### SR-002 — Command File as System Prompt Injection Vector

**Severity: Medium**

**Attack surface**: `commands/audit-architecture.md` flows directly into agent system
prompts. Adversarial content in the command file (added via a compromised PR or
malicious edit) could hijack agent behavior during any `/audit-architecture` invocation.

**Evidence**: SPRINT-004's security considerations noted this for `audit-security`.
The same applies here.

**Mitigation**: The plan acknowledges this: "Command file flows into agent system
prompts — review for unintended scope expansion." The command's own review
categories should be reviewed before committing. No additional DoD change needed
beyond the standard review process already documented.

**Rating**: Medium — inherent to the command file model; mitigated by the existing
review process and the `SECURITY.md` disclaimer in the repo.

---

### SR-003 — Codex exec Prompt Scope Expansion

**Severity: Medium**

**Attack surface**: The Phase 2 Codex exec prompt instructs Codex to "read files" and
"write to `docs/architecture/`." If the prompt wording is imprecise, a Codex session
running in `danger-full-access` sandbox mode could be instructed (by a maliciously
crafted finding or a prompt injection in a source file it reads) to write outside
`docs/architecture/`.

**Evidence**: The plan says "Codex exec prompts must not instruct Codex to execute
shell commands beyond reading files and writing to `docs/architecture/`" — this is
the correct constraint but only exists in Security Considerations, not in the Phase 2
prompt requirements.

**Mitigation**: The Phase 2 and Phase 4 Codex exec prompt templates in the command
file should include an explicit negative instruction: "Do not write to any path
outside docs/architecture/. Do not run shell commands."

**DoD addition**: "Phase 2 and Phase 4 Codex exec prompts explicitly restrict writes
to `docs/architecture/` and prohibit shell command execution."

**Rating**: Medium — risk is constrained by sandbox mode in most configurations, but
the prompt should be explicit.

---

### SR-004 — Architecture Artifact Disclosure in Public Repos

**Severity: Low**

**Attack surface**: `docs/architecture/NNN-*.md` files may contain structural weakness
findings — module boundaries, coupling points, and extensibility gaps — that are useful
for attackers planning targeted exploits against a public repo.

**Evidence**: The plan includes this in Security Considerations and P1-B README task.

**Mitigation**: Addressed. P1-B `docs/architecture/README.md` will include the note
to review before committing. Consistent with `audit-security` treatment.

**Rating**: Low — documented, mitigated, no additional action needed.

---

### SR-005 — Sprint Tasks Too Broad for Safe Agent Execution

**Severity: Low**

**Attack surface**: Architecture sprint tasks produced in Phase 5 will be executed by
agents via `/sprint-work`. If tasks say "refactor the entire commands/ directory" or
"restructure agent invocation chain," the executing agent has wide, hard-to-bound
authority.

**Evidence**: The plan's Phase 5 requirements say "task descriptions must be specific
enough to be safe; no 'refactor everything in X' broad tasks." But the task format
only requires `finding ID, location, principle, alternative, migration cost,
remediation, verification` — it doesn't explicitly prohibit multi-file broad tasks.

**Mitigation**: Add to the Phase 5 sprint output requirements: "Each task must be
scoped to a single specific change. Tasks that touch multiple files must enumerate
the files explicitly."

**DoD addition**: "Phase 5 tasks are scoped to specific, enumerable changes — no
single task that broadly modifies a directory without enumerating affected files."

**Rating**: Low for this sprint (the plan is a command file, not code); slightly
higher risk when the command is actually invoked.

---

## Summary by Severity

| Severity | Count | Findings |
|---|---|---|
| Critical | 0 | — |
| High | 1 | SR-001 ($ARGUMENTS injection) |
| Medium | 2 | SR-002 (system prompt injection), SR-003 (Codex scope expansion) |
| Low | 2 | SR-004 (artifact disclosure), SR-005 (broad sprint tasks) |

## DoD Additions Required (High/Medium findings)

For **SR-001** (High):
- [ ] Phase 1 validates each path in `$ARGUMENTS` confirms it exists (via `ls` or
  equivalent) before storing as resolved scope — not just syntactic validation

For **SR-003** (Medium):
- [ ] Phase 2 and Phase 4 Codex exec prompts explicitly restrict writes to
  `docs/architecture/` and prohibit shell command execution beyond file reads

For **SR-005** (Low — judgment call):
- [ ] Phase 5 tasks scoped to specific changes; multi-file tasks enumerate files
  explicitly
