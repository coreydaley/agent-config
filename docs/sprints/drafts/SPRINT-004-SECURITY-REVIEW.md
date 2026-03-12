# Security Review: SPRINT-004

## Scope

Reviewing `docs/sprints/SPRINT-004.md` — the plan to create
`commands/audit-security.md`.

## 1. Attack Surface

**Finding SR-001 — Medium**

**Title**: New command expands agent prompt execution surface

**Location**: `commands/audit-security.md` (to be created); `commands/`
directory flows into agent system prompts for Claude, Codex (via
`~/.codex/prompts/`), and Gemini (via TOML conversion).

**Why It Matters**: Any text in the command file becomes part of the
agent's execution context. A maliciously crafted or accidentally
ambiguous instruction in `audit-security.md` could cause agents to
take unintended actions (exfiltrate findings, expand scope beyond
what the user intended, or execute shell commands outside the
`docs/security/` write boundary).

**Recommended Fix**: Include in the command's DoD: review Phase 2 and
Phase 4 Codex exec prompts specifically for scope boundary instructions
(Codex must only read files and write to `docs/security/`; no other
shell execution). Already partially addressed in Security Considerations
section — ensure this is a DoD item, not just guidance prose.

---

**Finding SR-002 — Low**

**Title**: Gemini TOML conversion of a long command body is untested

**Location**: Sprint Overview, Gemini TOML compatibility note; existing
`build/gemini-commands/` pipeline (SPRINT-001)

**Why It Matters**: The `generate-gemini-commands.sh` script has a known
limitation with embedded triple-quoted strings. A very long prompt body
(Phase 2/4 Codex exec strings are multi-line) could produce malformed
TOML with unbalanced `"""` if the awk parser mishandles them.

**Recommended Fix**: Add to DoD: run `grep -c '"""' build/gemini-commands/audit-security.toml` after generation and verify even count. This is consistent with the SPRINT-001 DoD check for existing commands.

## 2. Data Handling

**Finding SR-003 — Medium**

**Title**: `docs/security/` intermediate files may contain sensitive
findings committed to version control

**Location**: P1-B note in sprint document

**Why It Matters**: Security findings describe exploitable
vulnerabilities — exposed secrets, auth bypass paths, injection
vectors. If these files are committed to a public repository (this
repo is on GitHub), the findings become a roadmap for attackers before
remediations are applied.

**Recommended Fix**: The sprint already notes this in P1-B and Security
Considerations. Strengthen: add a `.gitignore` entry for `docs/security/`
as a P1 task (or note in the command that users should add one), not
just a README advisory. Low lift, meaningful protection.

---

**Finding SR-004 — Low**

**Title**: Sprint output (`SPRINT-NNN.md`) contains security finding
details in a tracked, potentially public file

**Location**: Phase 5, Sprint Output section

**Why It Matters**: The sprint document will describe vulnerabilities
in task form. Same concern as SR-003 but for the sprint file itself.

**Recommended Fix**: Add a note in Phase 5: "Consider whether to commit
the sprint document before P0 tasks are resolved. The sprint file
describes exploitable findings."

## 3. Injection and Parsing Risks

**Finding SR-005 — High**

**Title**: Codex exec prompts include user-controlled scope from
`$ARGUMENTS` — potential prompt injection

**Location**: Phase 2 Codex exec prompt; Phase 1 Orient step

**Why It Matters**: If `$ARGUMENTS` contains special characters, shell
metacharacters, or adversarial text, it gets interpolated directly into
the `codex exec "..."` string. For example: `audit-security '; rm -rf ~;
echo '` could be harmful in a naive implementation.

**Recommended Fix**: The command must instruct Claude to sanitize/escape
the scope argument before embedding it in the Codex exec prompt. The
scope should be passed as a directory path reference, not interpolated
verbatim as shell text. Specifically, Phase 1 should resolve the scope
to a validated path and pass only the resolved path to Codex. This
should be a **P0 DoD item**.

---

**Finding SR-006 — Low**

**Title**: Finding schema uses pipe-delimited markdown tables; malformed
findings could break synthesis

**Location**: Finding Schema section; Phase 3 Synthesis

**Why It Matters**: If a finding description contains `|` characters,
the table breaks and synthesis parsing becomes ambiguous.

**Recommended Fix**: Add to command: instruct both Claude and Codex to
escape or avoid `|` in finding titles/descriptions. Low friction fix.

## 4. Authentication / Authorization

**Finding SR-007 — Low**

**Title**: No auth/authz surface introduced

The sprint creates text files and command documents only. No new
authentication flows, permission checks, or credential handling is
introduced. This category is not applicable to this sprint.

## 5. Dependency Risks

**Finding SR-008 — Low**

**Title**: Codex exec depends on Codex being installed and configured

**Location**: Phase 2, Phase 4 Codex exec calls

**Why It Matters**: If Codex is not installed or not configured with
API access, both Phase 2 (Codex independent review) and Phase 4
(devil's advocate) silently fail, producing an incomplete audit.

**Recommended Fix**: Add to Phase 1 (Orient): check that `codex` is
available (`which codex`); if not, instruct Claude to perform both
independent reviews itself (noting they are single-agent) and skip the
devil's advocate Codex pass, with a warning in the final sprint that
the audit used single-agent review only.

## 6. Threat Model (Agent-Config Specific)

**Finding SR-009 — High**

**Title**: The command instructs agents to perform security reviews of
their own configuration files — potential for self-serving blind spots

**Location**: Use Case 4 ("Agent config self-audit"); Phase 2 review
categories mention prompt injection in command files

**Why It Matters**: When `audit-security` is run on the agent-config
repo itself (the primary use case), Claude is reviewing its own
command files — including `audit-security.md` itself. An agent may
have systematic blind spots about flaws in its own instructions, or
may be motivated (intentionally or via training) to underreport issues
in its own command files.

**Recommended Fix**: Add to the command: when running on the agent-
config repo, the Codex independent review is especially important as
an adversarial second opinion. The synthesis phase should note if
Claude and Codex disagree about agent/command file findings, and
escalate those specific disagreements to the devil's advocate pass.
The DoD should require Codex's independent review to specifically
cover `commands/*.md` and `skills/*/SKILL.md` files.

## Summary of Findings

| ID | Severity | Title |
|----|----------|-------|
| SR-001 | Medium | New command expands agent prompt execution surface |
| SR-002 | Low | Gemini TOML conversion of long body untested |
| SR-003 | Medium | Security findings in docs/security/ may be committed |
| SR-004 | Low | Sprint file describes exploitable findings |
| SR-005 | High | Prompt injection via $ARGUMENTS in Codex exec strings |
| SR-006 | Low | Pipe chars in finding descriptions break table syntax |
| SR-007 | Low | No auth/authz surface (N/A) |
| SR-008 | Low | Codex unavailable → silent incomplete audit |
| SR-009 | High | Agent self-review blind spots on own config files |

## Mitigations to Incorporate

**Critical/High → add to sprint tasks or DoD:**

- **SR-005 (High)**: Add to P0 DoD: "Phase 1 must validate/resolve
  `$ARGUMENTS` to a safe path before embedding in Codex exec prompts;
  do not interpolate raw user input into shell strings."
- **SR-009 (High)**: Add to command: when auditing agent-config repo,
  Codex review must specifically cover `commands/*.md` and `skills/`;
  divergences from Claude's assessment in this area are flagged for
  devil's advocate attention.

**Medium → add to Security Considerations section:**

- **SR-001 (Medium)**: Add DoD item: review Codex exec prompts
  for scope boundary instructions (read only + write to `docs/security/`
  only).
- **SR-003 (Medium)**: Add to P1: `.gitignore` entry for
  `docs/security/` with note that this is the user's choice to make.
