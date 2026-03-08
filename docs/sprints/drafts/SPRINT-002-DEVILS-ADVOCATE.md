# SPRINT-002 Devil's Advocate Review (Blocking)

## Approval Recommendation
Reject this sprint plan as written. It is overconfident about low-risk “text edits,” underestimates behavioral risk in prompt-orchestration changes, and defines success mostly as grep cleanliness.

## 1) Flawed Assumptions

1. Assumes reference swaps are harmless because they are “text edits.”
Citation: `Overview` (“All P0 changes are text edits”), `Security Considerations`.
Concern: `superplan.md` is executable process documentation for multi-agent runs. A one-line wording change can alter run behavior materially. Treating this as low-risk docs-only work is incorrect.

2. Assumes `SPRINT-001.md` is a stable canonical fallback for Phase 5 examples.
Citation: `P0-A` (Phase 5 and Reference changes), `Dependencies`.
Concern: This hard-codes an old sprint artifact as normative guidance. If Sprint 001 style diverges from current process, this bakes drift into the command.

3. Assumes `/ledger` skill invocation is universally available and equivalent to direct script calls.
Citation: `P0-A` (Output Checklist + Ledger audit), `Definition of Done`.
Concern: The plan replaces executable fallback (`python3 ...`) with skill-only syntax but never proves operational equivalence, availability, or failure behavior when skill routing is unavailable.

4. Assumes fresh-repo fallback logic is solved by one sentence.
Citation: `P0-B` (Phase 2 Step 1 fallback), `Definition of Done`.
Concern: “start at SPRINT-001” does not cover pre-existing nonstandard files, sparse checkouts, or concurrent sprint creation. This is an edge-case band-aid, not robust sequencing logic.

5. Assumes language-agnosticism is achieved by renaming `.rs` to `.ext`.
Citation: `P0-B` (Phase 3 template), `Acceptance` (`grep -n "\.rs"`).
Concern: This is surface-level neutrality. The underlying examples may still encode Rust-centric assumptions and path patterns.

## 2) Scope Risks

1. Hidden dependency on the exact internal structure of `commands/superplan.md`.
Citation: `P0-A`, `Execution Order` (grep-driven workflow), `Definition of Done` (“only 7 targeted changes”).
Risk: The plan assumes deterministic placement and wording of strings. Any upstream variation makes this brittle and can trigger false “done” or missed defects.

2. P1 creates a flip-flop dependency that can cause late rework.
Citation: `P1-A` task to switch Phase 5 reference back to `README.md`, `Execution Order` steps 6-7.
Risk: P0 intentionally points away from README, then P1 may reverse it in the same sprint. This churn increases merge conflicts and review confusion for no product gain.

3. “Ship if capacity allows” for README understates coupling to P0 correctness.
Citation: `P1-A Goal`, `P0-A` references, `Open Questions Resolved`.
Risk: The plan treats README as optional while actively changing core references based on its existence. That is not optional scope; it is a branching dependency.

4. Multi-agent prompt wording changes are scoped like simple content edits.
Citation: `Overview` (8-phase collaborative workflow), `P0-B` (new Phase 7 summary step), `Risks & Mitigations`.
Risk: Added Phase 7 communication can alter decision cadence, user approval timing, and phase transitions. This is process behavior scope, not cosmetic wording scope.

5. Acceptance checks are overly regex-centric and can miss semantic regressions.
Citation: `P0-A Acceptance`, `P0-B Acceptance`, `Execution Order`.
Risk: Passing grep does not prove the resulting instructions are coherent, non-contradictory, or executable end-to-end.

## 3) Design Weaknesses

1. String-match validation is used as primary design assurance.
Citation: `P0-A Acceptance`, `Execution Order` steps 1/4.
Weakness: The quality model is “tokens absent/present,” not “workflow executes correctly.” This is a poor fit for an orchestration command.

2. The plan optimizes for minimal edits over system clarity.
Citation: `Guiding Principles` (“Fix observed defects; do not redesign workflow”, “Prefer the smallest edit”).
Weakness: This codifies local patching and blocks structural cleanup where repeated reference confusion already exists.

3. Reference strategy is unstable and historically fragile.
Citation: `Overview` (broken references introduced during derivation), `P0-A`, `P1-A`, `Open Questions Resolved`.
Weakness: The plan acknowledges reference fragility but continues with manual pointer toggling instead of a durable reference policy.

4. Risk model is miscalibrated to “Low” despite process-critical edits.
Citation: `Risks & Mitigations` table.
Weakness: The stated risks focus on verbosity and conversion format, but not on orchestration correctness, user misguidance, or phase-control regressions.

5. No explicit design for backward compatibility with existing operator habits.
Citation: `P0-A` ledger invocation replacement, `Guiding Principles`.
Weakness: Eliminating direct command examples without transition guidance can break established workflows and reduce operability under degraded tooling.

## 4) Definition of Done Gaps

1. No end-to-end simulation of the 8-phase workflow after edits.
Citation: `Definition of Done`, `Execution Order`.
Gap: DoD never requires a dry-run walkthrough proving each phase still connects logically after the new Phase 7 step and reference changes.

2. No quality bar for the new Phase 7 user summary content.
Citation: `P0-B` (Phase 7 closing), `Definition of Done`.
Gap: “ends with a user-facing summary step” checks existence, not clarity, neutrality, or decision safety.

3. No verification that `/ledger` invocation instructions are actually actionable.
Citation: `P0-A` ledger changes, `Definition of Done`.
Gap: DoD checks syntax substitution only; it does not verify expected parameters, outputs, or fallback guidance.

4. “Only 7 targeted changes” is anti-quality when unknown defects may remain.
Citation: `Definition of Done` (“Diff reviewed: only the 7 targeted changes applied”).
Gap: This can cause reviewers to reject necessary collateral fixes and knowingly leave adjacent defects in place.

5. P1 DoD does not validate README authority or accuracy.
Citation: `P1 (if shipped)`.
Gap: It requires existence + minimal content but not alignment with current command behavior, cross-links, or contradiction checks.

6. No explicit regression check against `megaplan.md` divergence risk.
Citation: `Guiding Principles` (`megaplan.md: out of scope`), `Overview` (derivation introduced defects).
Gap: The known failure source is derivation drift, yet DoD includes no guardrail to prevent repeating that class of errors.

## 5) Most Likely Failure Mode

Most likely failure is a “green by grep, red in practice” sprint: all regex acceptance checks pass, but operators follow subtly inconsistent instructions in a live superplan run and stall between Phases 7 and 8 or run ledger updates incorrectly.

Failure chain:
1. P0 edits satisfy presence/absence grep checks.
Citation: `P0-A Acceptance`, `P0-B Acceptance`.
2. New Phase 7 summary text is present but ambiguous about required user approval semantics.
Citation: `P0-B` (Phase 7 closing), `Definition of Done`.
3. `/ledger` references are normalized syntactically, but no behavioral test confirms expected invocation in real runs.
Citation: `P0-A` ledger audit, `Definition of Done`.
4. Team marks sprint done because “only 7 targeted changes” were made and checks passed.
Citation: `Definition of Done`, `Execution Order`.
5. First real planning session hits interpretation gaps and phase transition confusion, requiring hotfix edits under pressure.
Citation: implied by missing end-to-end validation gates.

Net: this plan can certify textual consistency while still shipping operational inconsistency in the core planning command.

## Blocking Verdict
Do not start implementation until this plan adds behavioral validation gates beyond grep and explicitly tests phase-flow correctness with at least one full dry run.
