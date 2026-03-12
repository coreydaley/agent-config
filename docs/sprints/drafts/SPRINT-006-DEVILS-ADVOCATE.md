# SPRINT-006 Devil's Advocate Review (Blocking)

## Approval Recommendation
Reject this sprint plan as written. It is too confident that a subjective, high-variance review process can be made reliable through prompt wording and markdown structure alone. The plan is disciplined on paper, but weak on operational proof, failure handling, and containment of architectural subjectivity.

## 1) Flawed Assumptions

1. Assumes named principles are enough to convert architectural opinion into objective findings.
Citation: `Overview`, `Guiding Principles`, `Finding Schema`, `Risks & Mitigations`.
Concern: Requiring `Pattern/Principle` and `Alternative` does not make a judgment evidence-based. It just forces reviewers to label their opinion. A reviewer can still manufacture plausible-sounding anchors like `Separation of Concerns` or `Low Coupling` for almost any structural preference.

2. Assumes the existing `audit-*` workflow is portable into architecture review with only schema extensions.
Citation: `Guiding Principles`, `Architecture`, `Dependencies` (`SPRINT-004` as pattern template).
Concern: Security and accessibility audits have external anchors. Architecture does not. Reusing the same 5-phase machinery assumes the hard part is orchestration, when the hard part is calibration. This plan is borrowing confidence from earlier audits without proving the underlying review type is equally tractable.

3. Assumes “minimum discovery before findings” is sufficient to understand a codebase’s architecture.
Citation: `Implementation Plan > P0-A > Phase 1 — Orient requirements`.
Concern: “Survey `git log --oneline -10`,” “identify dependency direction where visible,” and “sample representative modules” is shallow reconnaissance, not architectural understanding. On a medium-size repo, this is exactly how you get confident nonsense.

4. Assumes unusual or flat repos should still receive architecture findings instead of failing closed.
Citation: `Architecture` (`Warn and continue if no recognizable formal structure`), `Implementation Plan > P0-A > Unusual/flat repos`, `Definition of Done`.
Concern: This is backwards. If the command cannot identify meaningful structure, it should degrade to “insufficient evidence,” not proceed with low-confidence findings that will still be turned into sprint tasks.

5. Assumes multi-path audits are a normal extension rather than a complexity multiplier.
Citation: `Architecture` (`supports multiple paths`), `Implementation Plan > P0-A`, `P0-B`, `P0-C`, `Definition of Done`.
Concern: Auditing one bounded subsystem is plausible. Auditing several paths at once introduces cross-boundary interpretation, duplicate findings, inconsistent context depth, and title/ledger complexity. The plan treats this as string propagation instead of an analysis problem.

6. Assumes agent-config repos can be architecture-audited by adding a custom checklist.
Citation: `Overview`, `Use Cases` (`Agent-config self-audit`), `Implementation Plan > P0-A`, `P0-A > Phase 2`.
Concern: This repo class is prompt-orchestration-as-code. Many “architectural” choices are really workflow, trust-boundary, or authoring-convention decisions. The plan assumes the command can distinguish those cleanly just because it names `commands/`, `skills/`, `agents/`, `prompts/`, and `scripts/`.

7. Assumes there are no unresolved design questions.
Citation: `Open Questions` (`None — all design questions resolved during planning and interview.`).
Concern: That is not credible. The plan still leaves unresolved what “correct” severity calibration means, when to refuse findings for low evidence, what counts as an intentional design trade-off, and how large a repo can be before the workflow becomes untrustworthy.

## 2) Scope Risks

1. The real scope is not “author one command file”; it is defining and stabilizing a new audit discipline.
Citation: `Guiding Principles` (`Favor the smallest viable scope: author the command file well before expanding`), `Implementation Plan > P0-A`.
Risk: This is framed as a command-authoring sprint, but the deliverable is a new review product with its own schema, calibration rules, synthesis policy, and sprint-mapping behavior. That is process design, not just file creation.

2. The multi-agent flow has hidden dependencies on external tool behavior the plan does not control.
Citation: `Architecture > Phase 2`, `Implementation Plan > P0-A > Phase 2`, `Security Considerations`.
Risk: The plan assumes `codex exec` works reliably in background, that Claude can operate simultaneously, that file writes complete before synthesis, and that “wait for Codex to finish” is enough coordination. There is no handling for partial writes, stale files, collision with pre-existing `AUDIT_NNN-*` artifacts, or one agent producing malformed output.

3. “Do not read or reference any other review file” is a brittle independence mechanism.
Citation: `Implementation Plan > P0-A > Phase 2` (Codex prompt).
Risk: This only constrains one agent prompt, and only textually. It does not prevent accidental contamination through existing artifacts, preloaded context, or human operator behavior. The plan promises independence without a real containment model.

4. Synthesis complexity is badly underestimated.
Citation: `Implementation Plan > P0-B > Phase 3 — Synthesis requirements`.
Risk: Deduplicating architecture findings is not like deduplicating lint errors. Two reviewers can describe the same issue at different abstraction levels, with different proposed alternatives, different severity, and different implied scope. “Preserve the most specific Alternative” is an underspecified rule that will produce arbitrary merges.

5. The devil's-advocate phase can balloon into a second synthesis pass.
Citation: `Architecture > Phase 4`, `Implementation Plan > P0-B > Phase 4`.
Risk: Once Codex is allowed to challenge false positives, missing findings, severity, and migration cost, Claude is effectively doing triage, resynthesis, and rejection tracking. That is not a cheap polish step. It can become the dominant effort in the workflow.

6. The “no findings” path is a smell that masks weak review quality.
Citation: `Implementation Plan > P0-C > No-findings case`, `Definition of Done`.
Risk: A forced P0 task to “Verify no findings” incentivizes the command to always emit sprint output even when the review was shallow, confused, or inconclusive. That keeps the workflow mechanically consistent while hiding that the audit may have produced no trustworthy signal.

7. P1 documentation is treated as optional even though user judgment is a central mitigation.
Citation: `Overview` (`structured starting point for team discussion`), `P1-A`, `P1-B`, `Assumptions`.
Risk: If the product depends on humans understanding the subjectivity and limits of the output, then discoverability and caveat documentation are not optional polish. They are part of safe operation.

## 3) Design Weaknesses

1. The design confuses stronger schema with stronger architecture review.
Citation: `Overview`, `Finding Schema`, `Definition of Done`.
Weakness: Most of the rigor is invested in table columns, ID prefixes, and prompt wording. Very little is invested in making the actual analysis trustworthy. This is classic process theater: polished artifact format, shaky underlying judgment.

2. Severity mapping is structurally naive for architecture work.
Citation: `Architecture > Phase 5`, `Implementation Plan > P0-C > Sprint mapping`, `Severity anchors`.
Weakness: Mapping `Critical/High` directly to `P0` assumes architectural concerns are sprint-immediate in the same way as broken functionality. Many architectural problems are real but not urgent; many urgent architectural issues are migration-bound and should not be executed without broader design work. This mapping will overfill P0 with refactor bait.

3. The design makes sprint generation too eager and too literal.
Citation: `Overview` (`executable sprint of architecture improvement tasks`), `P0-C`, `Security Considerations`.
Weakness: Architecture findings often require ADRs, sequencing, stakeholder validation, or metrics before implementation. The plan explicitly forbids ADR workflows and still insists on executable tasks. That is how you turn speculative design critiques into premature work orders.

4. “Specific alternative approach” is treated as a benefit when it is also a failure mode.
Citation: `Overview`, `Finding Schema`, `Implementation Plan > P0-A > Phase 2`.
Weakness: Forcing every finding to include a concrete alternative will bias reviewers toward overconfident redesign proposals, even when the real answer should be “investigate further” or “document the intentional trade-off.”

5. The design has no explicit confidence model.
Citation: `Overview`, `Evidence discipline`, `Phase 3 — Synthesis requirements`, `Summary` template.
Weakness: The plan mentions reviewer agreement raises confidence, not severity, but there is nowhere to record confidence, evidence quality, or uncertainty. That means weakly supported claims and strongly supported claims look equally official once they enter the sprint.

6. The architecture review model is repo-centric and static-text-heavy.
Citation: `Overview`, `Implementation Plan > P0-A > Minimum discovery before findings`, `Security Considerations`.
Weakness: The command inspects files and repository structure, but architecture failures often show up in runtime behavior, ownership boundaries, deployment constraints, and integration seams. The plan acknowledges this limitation and then proceeds as if structured file review still yields implementation-ready tasks.

7. The design gives the devil's-advocate role to Codex after Codex already contributed original findings.
Citation: `Architecture > Phase 2`, `Architecture > Phase 4`.
Weakness: That is not a clean adversarial separation. One of the original reviewers is also the challenger of the synthesis that included its own claims. This increases the chance of self-justifying corrections and blind spots instead of genuine adversarial review.

## 4) Definition of Done Gaps

1. No DoD item proves the command can distinguish low-evidence observations from real findings.
Citation: `Definition of Done`, `Evidence discipline`.
Gap: The DoD checks that the prompt says to skip opinion-only findings. It does not require examples, counterexamples, or any validation that reviewers actually behave that way.

2. No end-to-end validation of output quality, only output shape.
Citation: `Definition of Done`, `Verification Plan`.
Gap: The checks are almost entirely structural: frontmatter, columns, prompts, template sections, edge-case read-through. None require that the resulting findings are sensible, non-duplicative, proportional, or actionable.

3. No acceptance gate for false-positive rate.
Citation: `Overview`, `Phase 4`, `Risks & Mitigations`.
Gap: The plan knows subjectivity is the main risk and adds a devil's-advocate phase, but DoD never asks whether that phase materially reduced bad findings or whether the synthesis was still mostly noise.

4. No requirement to validate behavior on a repo large enough to stress the workflow.
Citation: `Use Cases`, `Observability & Rollback`, `Definition of Done`.
Gap: Verifying on “this repo” is weak. A small or familiar repo is the friendliest possible case. There is no test against a larger, layered, or messier repository where shallow discovery and dedup logic are more likely to fail.

5. No explicit failure behavior when both reviews are low quality but non-empty.
Citation: `Implementation Plan > P0-B > Phase 3`, `Definition of Done`.
Gap: The plan only checks whether files are non-empty. Two garbage reviews still satisfy the gate and move into synthesis. There is no quality threshold, retry rule, or “abort due to insufficient evidence” path.

6. No DoD requirement for concurrency safety around `AUDIT_NNN`.
Citation: `Architecture > Phase 1`, `Implementation Plan > P0-A`, `Definition of Done`.
Gap: The plan repeatedly says “determine next SPRINT-NNN” and reuse it literally, but does not define what happens if two audits start near-simultaneously, if the ledger advances between phases, or if stale draft files already exist for that number.

7. No validation that sprint tasks respect sequencing and blast radius.
Citation: `P0-C`, `Security Considerations`, `Definition of Done`.
Gap: The user handoff warns that architecture changes “often have sequencing dependencies,” but DoD does not require the generated sprint to encode those dependencies or even avoid contradictory tasks.

8. No safeguard against turning critique into broad unsafe work items.
Citation: `Security Considerations` (`no "refactor everything in X"` broad tasks), `P0-C`.
Gap: The plan states the safety goal, but DoD never checks task granularity, bounded scope, or whether remediation steps are actually implementable without design thrash.

## 5) Most Likely Failure Mode

The most likely failure is a high-confidence, low-trustworthiness sprint: the command produces cleanly formatted findings, a polished synthesis, a dramatic devil's-advocate memo, and an executable sprint full of architecture tasks that sound rigorous but are based on shallow repo reading and arbitrary severity calls.

Failure chain:

1. Phase 1 performs lightweight discovery and samples a few representative files.
Citation: `Implementation Plan > P0-A > Minimum discovery before findings`.

2. Both reviewers generate principle-labeled findings because the schema and prompt force them to do so.
Citation: `Overview`, `Finding Schema`, `Implementation Plan > P0-A > Phase 2`.

3. Synthesis mistakes agreement or overlapping language for robustness, even though both reviews were produced from the same shallow evidence base.
Citation: `Evidence discipline`, `Implementation Plan > P0-B > Phase 3`.

4. The devil's-advocate phase catches some weak claims but cannot repair the underlying problem that the audit never had enough architectural context.
Citation: `Implementation Plan > P0-B > Phase 4`.

5. Phase 5 converts these shaky findings into P0/P1 sprint tasks with remediation steps and verification language, making speculation look implementation-ready.
Citation: `Overview`, `Implementation Plan > P0-C > Sprint mapping`, `Definition of Done`.

6. The team executes refactor work because the sprint artifact looks formal and “approved,” then discovers the supposed architecture issues were either intentional trade-offs, symptoms not causes, or not the most important problems.
Citation: `Overview` (`structured starting point for team discussion, not a mandate to refactor`) in direct tension with `Phase 5` executable sprint output.

Net: the sprint will likely fail not by crashing, but by manufacturing unjustified certainty. That is the dangerous failure mode for architecture work.

## Blocking Verdict
Do not approve implementation until this plan adds hard quality gates for evidence sufficiency, confidence, failure-to-abstain behavior, and sprint-task safety. As written, it is optimized to produce convincing artifacts, not trustworthy architectural guidance.
