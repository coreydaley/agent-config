# SPRINT-001 Devil's Advocate Review (Blocking)

## Approval Recommendation
Reject this sprint plan as written. It is operationally optimistic, under-specifies failure behavior, and treats compatibility claims as facts without validation gates.

## 1) Flawed Assumptions

1. Assumes the capability matrix is stable and universally true.
Citation: `Agent Capability Matrix`, `Overview`.
Concern: The plan hard-codes tool paths and feature support as facts (`~/.codex/prompts/`, Gemini command TOML model, Copilot capabilities) without version scoping or source-of-truth references. If one CLI release changes path or parser behavior, this sprint “succeeds” locally and fails in real environments.

2. Assumes symlinks are a safe default for every target agent.
Citation: `Guiding Principles` (“symlinks into agent homes”), `Architecture`, `Security Considerations`.
Concern: The plan assumes all target tools follow symlinks consistently and safely. Some clients copy-on-read, reject symlinks, or resolve relative paths differently. No detection or fallback exists.

3. Assumes “minimal non-empty stubs” are valid smoke tests.
Citation: `P0-A`, `Risks & Mitigations` (“non-whitespace line”).
Concern: Non-empty proves file existence, not semantic validity. A stub can still be malformed for an agent parser and pass this sprint.

4. Assumes awk-based conversion can safely cover markdown complexity.
Citation: `P0-C`, `Conversion spec`, `Risks & Mitigations`.
Concern: Markdown + YAML frontmatter parsing with shell/awk is brittle (multiline YAML, quotes, embedded `---`, Unicode, code fences with TOML-breaking content). The plan treats this as “medium” risk despite no parser contract.

5. Assumes shared `subagents/` superset frontmatter is cross-agent compatible.
Citation: `P0-D`, `Open Questions Resolved` (“Single dir, superset frontmatter”), `P1-B Notes`.
Concern: “Claude ignores unknown fields” and Gemini `tools:` requirements are asserted, not proven. This is a silent incompatibility trap.

## 2) Scope Risks

1. Hidden parser project disguised as “script task.”
Citation: `P0-C` (`generate-gemini-commands.sh`), `Execution Order` step 7.
Risk: You are building and maintaining a markdown-to-TOML transpiler with edge cases, escaping rules, and regression surface. That is larger than a “routing fix.”

2. Idempotency claim is under-scoped.
Citation: `Guiding Principles` (`make all` idempotent), `Definition of Done`.
Risk: “Run twice” checks happy-path idempotency only. It does not cover partial runs, interrupted runs, pre-existing conflicting files, broken symlinks, or mixed old/new layouts.

3. Cross-agent divergence is postponed into P1 but affects P0 design.
Citation: `P1-A`, `P1-B`, `P0-B`, `P0-D`.
Risk: P0 intentionally skips real Codex skills integration and Copilot subagent compatibility while branding architecture as foundational. You may lock in abstractions that P1 immediately breaks.

4. Documentation work is treated as cheap while behavior is still uncertain.
Citation: `P0-E`, `Execution Order` steps 10-11.
Risk: Updating docs before compatibility is truly validated creates authoritative but wrong instructions.

5. No explicit dependency check on local environment tooling.
Citation: `Guiding Principles` (Bash 3.2+), `P0-C` (awk conversion).
Risk: awk/sed behavior differs across BSD/GNU/macOS/Linux. “Bash 3.2+ compatible” does not guarantee parser behavior portability.

## 3) Design Weaknesses

1. Centralized shell-script architecture creates untestable stringly-typed logic.
Citation: `Architecture` scripts list, `Execution Order`.
Weakness: Critical behavior is spread across multiple shell scripts with implicit contracts. No typed interface, no schema validation, no unit-level parser tests required by DoD.

2. Capability routing is encoded procedurally, not declaratively.
Citation: `Guiding Principles`, `Architecture`.
Weakness: Each script manually knows which agent supports what. This duplicates policy and guarantees drift. One missed branch reintroduces the exact class of bugs this sprint claims to fix.

3. Build artifact strategy is inconsistent.
Citation: `Guiding Principles` (only format conversions go to `build/`), `Architecture`.
Weakness: Some generated outputs are in-place, others in `build/`. This mixed model increases confusion, cleanup complexity, and future migration churn (already acknowledged as deferred).

4. Security model is acknowledged but not operationalized.
Citation: `Security Considerations`.
Weakness: The plan notes that repo write access controls all agents’ behavior, but defines no guardrails (integrity checks, review gates, trust boundaries). That is a design-level omission, not a footnote.

5. Error handling design is logging-heavy and correctness-light.
Citation: `Guiding Principles` (explicit skips/logging), `Definition of Done` (skip messages).
Weakness: Emitting skip logs is treated as success criteria. Logging is not a substitute for enforceable invariants and machine-verifiable checks.

## 4) Definition of Done Gaps

1. No parser validity checks per agent.
Citation: `Definition of Done`.
Gap: DoD checks symlink existence and non-empty files, but not whether each target agent can parse/load the artifact.

2. No content correctness checks for converted Gemini TOML.
Citation: `Definition of Done`, `P0-C`.
Gap: “contains `.toml` files” is not validation. Missing checks for escaped multiline content, preserved description, and rejected/stripped fields behavior.

3. No negative tests for malformed inputs.
Citation: `P0-C`, `generate-agent-files.sh` failure requirement, `Risks & Mitigations`.
Gap: Only missing-file error is required. No DoD for malformed frontmatter, empty descriptions, duplicate keys, invalid markdown edge cases.

4. No resilience tests for existing user state.
Citation: `Definition of Done`, `Security Considerations`.
Gap: No tests for pre-existing real files (not symlinks), permission issues, broken symlink repair, backup/rollback integrity.

5. No enforcement of “explicit skip” quality.
Citation: `P0-B`, `P0-D`, `Definition of Done`.
Gap: DoD requires skip messages but not stable format, exit behavior, or auditability. This will drift and become unreliable for automation.

6. No matrix validation in CI-like isolated environments.
Citation: entire DoD relies on local `~/.<agent>/` checks.
Gap: No reproducible validation harness. Local-home assertions are fragile and non-portable.

## 5) Most Likely Failure Mode

Most likely failure is a false-positive green sprint: `make all` passes, symlinks exist, but Gemini command ingestion fails silently due to conversion edge cases, while docs claim support is complete.

Failure chain:
1. `generate-gemini-commands.sh` emits syntactically invalid or semantically wrong TOML for one non-trivial command body.
Citation: `P0-C`, `Conversion spec`, `Risks & Mitigations`.
2. DoD still passes because it only requires `.toml` presence and symlink targets.
Citation: `Definition of Done`.
3. README capability matrix presents Gemini command support as shipped.
Citation: `P0-E`, `README` update requirement.
4. Team discovers runtime failure only after users execute commands in Gemini.
Citation: implicit from absence of parser/runtime validation gates.

Net: the sprint optimizes for file topology correctness, not behavioral correctness. It can “complete” while delivering a broken integration.

## Blocking Verdict
Do not start implementation under this plan without stronger behavioral validation gates. As written, it is designed to pass structural checks while leaving high-probability runtime failures undetected.
