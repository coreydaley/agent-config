# SPRINT-004 Devil's Advocate Review (Blocking)

## Approval Recommendation
Reject this sprint plan as written. It is trying to turn a fuzzy, high-judgment security review workflow into an "existing infrastructure" problem, but most of the hard parts are still being hand-waved. The plan is strong on naming files and phases; it is weak on proving the output will be trustworthy, actionable, or safe to execute.

## 1) Flawed Assumptions

1. Assumes a security audit can be losslessly converted into a normal sprint document without destroying the context needed to judge exploitability, compensating controls, or remediation sequencing. Citation: [Overview](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L9), [Key Decisions](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L21), [Phase 5](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L177). That is a planning assumption, not a demonstrated fact.

2. Assumes `/sprint-work` can safely execute security remediation "as-is" merely because findings are mapped to P0/P1/Deferred. Citation: [Overview](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L11), [Out of Scope](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L35), [Acceptance](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L221). Security fixes routinely need ordering, rollback planning, test expansion, and cross-file coordination. The plan pretends priority mapping is enough.

3. Assumes two independent LLM reviews plus a synthesis pass meaningfully increase security confidence without introducing the same shared blind spots twice. Citation: [Architecture](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L63), [Key Decisions](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L27). "Two agents looked at it" is being used as a quality signal, but both agents are driven by the same repo, same prompt framing, and same missing runtime evidence.

4. Assumes the minimal finding schema is enough to support synthesis, adversarial review, and later remediation. Citation: [Finding Schema](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L83). It omits preconditions, exploit path, confidence, affected asset, and evidence. That means the downstream steps are being asked to make serious decisions from underspecified records.

5. Assumes severity can be rated credibly from static review prompts alone. Citation: [Key Decisions](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L29), [Phase 2 prompt](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L135), [Phase 3](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L155). Impact, reachability, and blast radius are often unknowable without runtime architecture, deployment context, or threat model validation. The plan treats them like they can be inferred from file reading.

## 2) Scope Risks

1. The "one new command" framing hides that this actually creates a new security-review process, a new artifact family, a new severity-to-priority contract, and a new ledger entry pattern. Citation: [Overview](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L5), [Key Decisions](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L23), [Phase 5](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L192). That is scope expansion disguised as documentation work.

2. Scope selection is badly underspecified. "Optional path/scope" sounds simple until the scope is a repo root, a directory with generated files, or a mixed trust boundary. Citation: [Architecture](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L55), [Phase 1](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L119). There is no rule for excluding vendored code, secrets, generated output, tests, or huge trees. That is how audits become slow, noisy, and inconsistent.

3. The sprint-numbering step is a race condition waiting to happen. Citation: [Architecture](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L61), [Phase 1](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L122). `ls ... | tail -1` is not a coordination mechanism. Two concurrent runs can claim the same `NNN`, and the plan has no collision handling.

4. The plan says "no scanner, linter, or automated code-analysis tooling" out of scope, but then expects security findings to be comprehensive enough to gate merges. Citation: [Out of Scope](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L37), [Use Cases](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L43). That is an ugly middle ground: too manual to be reliable, too authoritative to be treated as advisory.

5. The hidden dependency on ledger semantics is bigger than the plan admits. Citation: [Architecture](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L79), [Phase 5](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L193), [Tasks](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L212). If `/ledger add` behavior, format, or failure cases are off, the whole "handoff to `/sprint-work`" story breaks.

## 3) Design Weaknesses

1. The architecture optimizes for familiar ceremony over security rigor. Citation: [Overview](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L5), [Key Decisions](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L27). Reusing the `sprint-plan` pattern is convenient, but a security audit is not a planning debate. It needs evidence capture, false-positive control, and threat-model discipline that this pattern does not provide.

2. The finding schema is too thin to support deduplication without flattening materially different issues into one row. Citation: [Finding Schema](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L85), [Phase 3](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L151). Two findings can share a file and title while having different exploit preconditions, different blast radius, and different fixes. This design invites sloppy merges.

3. Using Codex for both the independent review and the devil's-advocate pass weakens the supposed adversarial separation. Citation: [Architecture](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L63), [Key Decisions](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L27), [Phase 4](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L160). You are asking the same system to first generate findings and later attack the synthesis built partly from its own work. That is not independent challenge; it is self-review with different instructions.

4. The plan creates security artifacts in `docs/security/` but treats operational sensitivity as a footnote. Citation: [Key Decisions](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L24), [P1-B](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L242). If these files may contain exploit descriptions or sensitive trust-boundary details, that should shape the design now, not get buried in a deferred lightweight README.

5. The plan hard-codes a severity-to-priority mapping that will be regretted the first time a Low-cost High-severity fix competes with an expensive Medium-severity architectural weakness. Citation: [Overview](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L11), [Phase 5](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L178). Security work is not that linear. This design bakes in false precision and hides remediation cost entirely.

## 4) Definition of Done Gaps

1. There is no requirement to prove that findings are correct, only that files exist and formatting is consistent. Citation: [Output checklist](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L196), [Acceptance](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L216). A useless audit with plausible markdown tables would pass this sprint.

2. The DoD never requires a demonstration that the produced sprint is actually safe for `/sprint-work` to execute. Citation: [Overview](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L12), [Acceptance](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L221). "Consumable" is not enough. A sprint can be syntactically consumable and still contain vague, non-verifiable, or dangerous remediation tasks.

3. No acceptance criterion checks failure handling when one review is empty, malformed, duplicated, or late. Citation: [Phase 2](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L126), [Phase 3](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L149). The plan assumes both review files will appear and be parseable. That is not a definition of done; that is wishful thinking.

4. The "no findings" case is dangerously underspecified. Citation: [Phase 5](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L188). A bad implementation can generate a ceremonial "Verify no findings" task even when the audit silently failed, skipped files, or lacked enough context to make a credible call.

5. There is no quality bar for deduplication, severity recalibration, or rejected devil's-advocate challenges. Citation: [Phase 3](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L151), [Phase 4](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L171), [Output checklist](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L201). The plan says those things should happen, but never defines how we know they happened well rather than superficially.

6. Nothing in acceptance verifies that sensitive findings are handled appropriately before being written into version-controlled docs. Citation: [Key Decisions](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L24), [P1-B](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L245). For a security command, that omission is irresponsible.

## 5) Most Likely Failure Mode

The most likely failure is not "the command crashes." The most likely failure is that it produces a polished, authoritative-looking sprint full of half-true findings and low-quality remediation tasks, and the team treats that artifact as trustworthy because the process looked rigorous on paper.

Failure chain:

1. Phase 1 picks an over-broad or under-specified scope because the only rule is "`$ARGUMENTS` or cwd." Citation: [Architecture](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L58), [Phase 1](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L120).
2. Phase 2 produces two superficially structured reviews, but both are missing key context because the schema and prompts do not require exploit preconditions, evidence quality, or confidence. Citation: [Finding Schema](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L89), [Phase 2 prompt](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L130).
3. Phase 3 deduplicates aggressively and re-rates severity from incomplete evidence, collapsing nuance into canonical rows that look cleaner than the underlying analysis deserves. Citation: [Phase 3](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L149).
4. Phase 4 gives a false sense of hardening because the adversarial pass is still another LLM critique, not real validation. Citation: [Key Decisions](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L27), [Phase 4](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L160).
5. Phase 5 turns those rows into executable sprint tasks, and the acceptance criteria bless the result because the files exist, the schema is consistent, and the user is told to run `/sprint-work NNN`. Citation: [Phase 5](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L177), [Acceptance](/Users/corey/Code/github.com/coreydaley/agent-config/docs/sprints/SPRINT-004.md#L216).

Net: the sprint succeeds administratively while failing substantively. It will generate security theater with just enough structure to be dangerous.

## Blocking Verdict
Do not approve implementation until the plan proves three things it currently only asserts:

1. The audit output preserves enough evidence and context to support trustworthy remediation decisions.
2. The handoff into `/sprint-work` cannot turn vague or wrong findings into executable-but-bad work.
3. The process can fail loudly when inputs, scope, or review quality are insufficient, instead of quietly emitting a reassuring sprint document.
