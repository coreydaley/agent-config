# SPRINT-003 Devil's Advocate Review (Blocking)

## Approval Recommendation
Reject this sprint plan as written. It frames a behavior-critical orchestration change as low-risk text editing, but the acceptance model proves wording changes, not runtime correctness.

## 1) Flawed Assumptions

1. Assumes removing `disable-model-invocation` is a narrow fix with bounded blast radius.
Citation: `Overview`, `P0-A`, `Security Considerations`.
Concern: This changes trust boundaries for the ledger skill globally, not just for `/sprint`. The plan treats it as local plumbing while under-specifying cross-command side effects.

2. Assumes `allowed-tools: Bash(python3 *)` is a sufficient safety control.
Citation: `P0-A` tasks, `Risks & Mitigations`, `Security Considerations`.
Concern: `python3 *` is broad. The plan calls it a guardrail without proving it prevents unintended script invocation patterns or bad argument surfaces.

3. Assumes `/ledger current` semantics are stable and unambiguous.
Citation: `P0-B` (In-progress guard), `Open Questions Resolved`.
Concern: The plan depends on a single command for control flow but never verifies output format, ambiguity handling, or failure behavior if current sprint state is stale.

4. Assumes explicit sprint argument validation can be reliably done via `/ledger stats` or `/ledger list`.
Citation: `P0-B` (Explicit sprint number path).
Concern: The plan offers two different read paths without specifying canonical source or conflict resolution. That invites divergent implementations and inconsistent operator behavior.

5. Assumes “text-only edits” imply low implementation risk.
Citation: `Overview` (“All changes are text edits to two files”), `Guiding Principles`.
Concern: `commands/sprint.md` is executable instruction logic. Small wording changes can materially alter autonomous behavior and state transitions.

## 2) Scope Risks

1. Hidden scope: this is effectively a state-machine edit, not copy changes.
Citation: `P0-B`, `Definition of Done` (Step 1 handles four states).
Risk: Adding no-planned, in-progress, explicit-NNN-not-found paths introduces branching behavior that is easy to make contradictory and hard to validate by inspection.

2. Soft prompt design can balloon into UX and policy debates.
Citation: `P0-B` (In-progress guard: ask continue/abort; default continue).
Risk: Defaulting to continue is a policy choice with operational consequences. Expect churn over whether default should be continue, abort, or require explicit confirmation.

3. Hidden dependency on `/ledger sync` correctness and discoverability.
Citation: `P0-B` (Explicit NNN not in ledger), `Ledger sync guidance`.
Risk: The sprint pushes recovery onto `/ledger sync` and `/ledger add` but does not verify those paths are safe, documented, or deterministic in edge repos.

4. Build/test guidance can still be too vague for automation.
Citation: `P0-C`, `Definition of Done` (Step 3 references README/Makefile).
Risk: “Check README/Makefile” sounds concrete but may still produce nondeterministic command selection and hand-wavy validation outcomes.

5. Manual read-through is undersized for branch complexity.
Citation: `Definition of Done` (three scenarios), `Execution Order` step 6.
Risk: Plan adds at least four Step 1 branches plus argument-driven behavior; three manual scenarios will miss regressions.

## 3) Design Weaknesses

1. Global capability toggle is used instead of command-local enforcement.
Citation: `P0-A`, `Open Questions Resolved`.
Weakness: Enabling model invocation at skill level is coarse-grained. If the intent is only `/sprint` use, this choice over-authorizes by design.

2. Control flow remains prose-driven with no canonical decision table.
Citation: `P0-B`, `Definition of Done` Step 1 requirements.
Weakness: Multi-branch behavior embedded in paragraph text is fragile and easy to interpret differently across models.

3. Validation architecture is grep-first, behavior-second.
Citation: `Acceptance` across `P0-A/P0-B/P0-C`, `Execution Order` steps 1 and 5.
Weakness: String checks prove edits occurred, not that command orchestration works under realistic state transitions.

4. Recovery paths are bolt-ons rather than a unified error strategy.
Citation: `P0-B` (no planned => suggest `/superplan`; missing NNN => `/ledger sync` or `/ledger add`).
Weakness: Error handling is fragmented by case. There is no consistent remediation policy, escalation behavior, or retry model.

5. “Do not redesign workflow” locks in known fragility.
Citation: `Guiding Principles`.
Weakness: The plan acknowledges current breakage source (skill invocation mismatch) but forbids structural hardening beyond patch-level edits.

## 4) Definition of Done Gaps

1. No end-to-end execution proof of `/sprint` with real ledger mutations.
Citation: `Definition of Done` (`can invoke ... without error`), `Execution Order`.
Gap: “without error” is underspecified. No requirement verifies correct state transitions before/after `start` and `complete`.

2. Missing negative tests for command failure and malformed outputs.
Citation: `P0-B`, `Definition of Done`.
Gap: No DoD for `/ledger` command timeouts, parse failures, or non-zero exits. The plan assumes happy-path command responses.

3. No guard that default “continue in-progress sprint” is explicitly user-confirmed.
Citation: `P0-B` (soft prompt + default continue), `Open Questions Resolved`.
Gap: A bad implementation could auto-continue silently and still pass current DoD.

4. No compatibility check that removing frontmatter key does not break other tooling.
Citation: `P0-A`, `Risks & Mitigations` (Gemini TOML conversion low risk).
Gap: DoD checks key removal, not downstream parser behavior across agent tooling that consumes `SKILL.md`.

5. Scenario coverage is incomplete relative to stated branches.
Citation: `Definition of Done` (three manual scenarios), `P0-B` (four Step 1 cases + explicit argument path).
Gap: Explicit `NNN` missing-from-ledger case is required behavior but absent from mandatory manual scenarios.

6. No regression gate for “wrong command reference” class.
Citation: `Overview` (incorrect `/ledger status` usage), `P0-B Acceptance`.
Gap: DoD bans one bad token but does not require auditing other read-vs-mutate command misuse patterns.

## 5) Most Likely Failure Mode

Most likely failure is a silent logic regression in `/sprint`: the document passes grep-based acceptance, but real runs mutate the wrong sprint state when an in-progress sprint exists and a user provides explicit `NNN`.

Failure chain:
1. `disable-model-invocation` is removed and checks pass.
Citation: `P0-A Acceptance`, `Definition of Done` first checkbox.
2. Step 1 prose is updated for multiple branches but lacks strict precedence rules between “existing in-progress sprint” and “explicit argument path.”
Citation: `P0-B` (In-progress guard + explicit sprint number path).
3. Implementation chooses an unintended precedence (for example, default continue overrides explicit target, or explicit target bypasses current sprint warning).
Citation: implied by prose-only branching.
4. Manual read-through misses it because required scenarios omit explicit precedence conflict testing.
Citation: `Definition of Done` (only three scenarios).
5. Sprint is marked complete while runtime behavior is operationally unsafe and requires hotfix clarification.
Citation: `Execution Order` and DoD relying on grep + read-through.

Net: this plan is optimized to show edits happened, not to prove the command now behaves correctly under conflicting ledger states.

## Blocking Verdict
Do not approve implementation until the plan adds behavioral validation gates for branch precedence, ledger mutation correctness, and explicit failure-path handling.
