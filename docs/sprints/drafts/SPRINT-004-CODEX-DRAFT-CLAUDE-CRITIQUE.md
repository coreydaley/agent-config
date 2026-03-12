# Claude's Critique of SPRINT-004 Codex Draft

## What Codex Got Right

- **Guiding Principles section** — "Treat security findings as planning
  input, not as a separate tracking system" is a crisp articulation of
  the design. Worth surfacing prominently.
- **Key Decisions section** — captures the *why* behind design choices
  in a form that helps future maintainers. My draft buried these in
  prose; Codex surfaced them explicitly. Should incorporate this.
- **Explicit out-of-scope list** — listing "no separate remediation
  command" and "no bespoke report format" prevents scope creep and
  makes the sprint easier to execute. Good addition.
- **README.md update as P1** — I omitted this. Codex is right that
  users should be able to discover `audit-security` in the README
  without reading the source file. Valid P1 addition.
- **Verification Plan edge cases** — listing "no scope argument",
  "path-scoped audit", "overlapping findings", "no findings" as
  explicit verification scenarios is well-structured. My DoD had
  some of these but not systematically.
- **No script changes principle** — consistent with the project's
  preference for text-only changes.

## What Codex Missed or Got Wrong

### Critical gaps

1. **No actual command phases specified** — Codex's draft is a plan
   *to write* the command, not a spec *of what goes in* the command.
   P0-A says "write the full audit workflow" without ever saying what
   the phases are, what the Codex exec prompts contain, or what each
   phase produces. An agent executing this sprint would have to invent
   the workflow from scratch. My draft specifies the actual Phase 1-5
   structure, Codex exec prompt content, and what each phase writes.

2. **Intermediate file naming scheme undefined** — "specify intermediate
   files in docs/security/" (P0-B) says to define them but doesn't
   define them. Without explicit names (`NNN-CLAUDE.md`, `NNN-CODEX.md`,
   etc.), different agents will produce different file names, breaking
   the synthesis phase which reads specific paths.

3. **No `docs/security/README.md`** — Codex doesn't create this file.
   Without it, Codex exec prompts have no reference document to point
   to for orientation, and the `docs/security/` directory has no
   conventions documented. My draft includes this as P0-B.

4. **`/ledger add NNN` step missing** — Phase 5 of the command needs to
   add the new sprint to the ledger. Without this, `/sprint-work` won't
   find the sprint when run without explicit arguments. Codex's draft
   omits this entirely.

### Moderate gaps

5. **Severity escalation rule missing** — My draft includes: when both
   Claude and Codex independently flag the same finding, escalate severity
   by one level (Medium → High, High → Critical). This is important for
   calibration — agreement between independent reviewers is signal.
   Codex omits this.

6. **Codex exec prompt content not specified** — Codex says "ensure
   Codex invocations use `codex exec`" but doesn't specify what the
   prompts should say. The prompts are critical: vague prompts produce
   vague reviews. My draft specifies the categories each review must
   cover (attack surface, injection risks, data handling, auth/authz,
   dependencies, prompt injection for agent-config repos).

7. **"No findings" behavior underspecified** — P0-C mentions "add
   explicit handling" but doesn't say what that handling is. My draft
   specifies: produce a sprint with a single "no findings" P0
   verification task. Codex leaves it open.

## What I'd Defend From My Draft

- The actual phase structure of the `audit-security` command: Phase 1
  (Orient), Phase 2 (parallel reviews), Phase 3 (synthesis with
  escalation rule), Phase 4 (devil's advocate), Phase 5 (sprint output
  with ledger add). Codex's draft assumes this will be filled in later.
- The explicit Codex exec prompt text — being prescriptive here is
  correct; vague exec prompts are the most common failure mode.
- `docs/security/README.md` as P0-B — this is a clean reference for
  the `audit-*` namespace and naming conventions.

## What I'm Incorporating from Codex's Draft

- **Key Decisions section** — add to the final sprint document
- **Explicit out-of-scope list** — add to Overview or Guiding Principles
- **README.md update as P1** — add as P1-A (Codex had this right)
- **Verification Plan edge cases** — expand DoD to explicitly cover:
  no-scope, path-scoped, overlapping-findings, no-findings scenarios
- **"Output contract verification" check** — DoD item: compare final
  sprint output against `docs/sprints/README.md` and `sprint-work.md`

## Overall Assessment

Codex's draft is well-structured at the *sprint* level (clear principles,
good scope boundaries, useful Key Decisions section) but underspecified
at the *command* level — it describes what to build without specifying
what goes in it. An agent executing Codex's sprint would need to make
many undocumented decisions about the command's workflow.

My draft is stronger on actual command content but weaker on sprint-level
framing (missing Key Decisions, missing out-of-scope, missing README P1).

The merge should combine Codex's sprint framing with my command-level
specificity.
