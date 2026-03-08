# Sprint 003 Merge Notes

## Claude Draft Strengths
- Correctly identifies the root defect (`disable-model-invocation: true`) and targets a minimal fix
- Keeps scope constrained to `commands/sprint.md` and `skills/ledger/SKILL.md`
- Good edge case identification (no planned sprints, in-progress guard)
- Preserves no-change stance on ledger.py

## Codex Draft Strengths
- Identified the "ledger bootstrap/sync" edge case (sprint doc exists but ledger has no entry)
- Better build/test guidance: anchor to `README.md` and `Makefile`, not CLAUDE.md
- More explicit scenario-based read-through verification plan
- Explicit policy: when explicit NNN is given and missing from ledger → `/ledger sync` or `/ledger add`, then stop (not run anyway)
- Cleaner structure for the in-progress case: continue the existing in-progress sprint rather than asking

## Valid Critiques Accepted

1. **High: CLAUDE.md reference is wrong** — root-level `CLAUDE.md` doesn't exist in this repo; replace with `README.md` and `Makefile`. Accepted.
2. **High: `/ledger status NNN` is a mutating command** — can't use it for existence verification. Replace with `/ledger stats` (read-only). Accepted.
3. **Medium: Explicit argument policy must be decided, not left ambiguous** — encode the rule: if the sprint exists in the ledger, run it; if it doesn't, tell user to run `/ledger sync` or `/ledger add NNN "Title"` first. Accepted.
4. **Medium: In-progress handling must be a concrete decision, not an open question** — user decided: soft prompt (surface the current sprint and ask to confirm continuing it). Encode in DoD. Accepted.

## Critiques Rejected

5. **Low: Security section needs an "enforceable" guardrail** — adding constraint language to the skill or command about "non-use outside `/sprint`" would be over-engineering. The `allowed-tools: Bash(python3 *)` is the guardrail. Rejected.

## Interview Refinements Applied

- Enable model invocation (user chose to remove `disable-model-invocation: true`)
- No planned sprints → inform + suggest `/superplan`
- In-progress sprint → soft prompt (surface it, ask user to confirm continuing)

## Final Decisions

1. Remove `disable-model-invocation: true` from `skills/ledger/SKILL.md`
2. In sprint.md Step 1: add explicit handling for (a) empty ledger, (b) no planned sprints
3. In sprint.md Step 1: add soft in-progress guard before starting a new sprint
4. In sprint.md Step 1 (explicit NNN path): verify sprint exists in ledger first; if not, instruct user to sync or add, then stop
5. Build/test guidance: reference `README.md` and `Makefile`; fall back to sprint doc's DoD items
6. Replace any verification using `/ledger status` with read-only commands
