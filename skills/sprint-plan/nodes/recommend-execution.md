# Node: recommend-execution

Phase 9 Step 3-4: write the Recommended Execution section into SPRINT.md and run the Definition of Ready (DoR) pre-flight check.

## Inputs

- `sprint_md_path`, `reviews_run`, `uncertainty_too_high`, `spike_choice` from walker state

```bash
STATE="<path>"
SPRINT_MD=$(scripts/walk.sh get --state "$STATE" --key sprint_md_path)
```

## Step 1: Recommend a tier

Based on everything learned, recommend which Claude model tier `/sprint-work` should use:

| Tier | Model | When |
|---|---|---|
| `high` | `opus` | Complex / novel / high-risk sprints |
| `medium` | `sonnet` | Standard sprints with moderate scope |
| `low` | `haiku` | Trivial sprints (typo fixes, small refactors) |

### Heuristics

Bump toward **high** when any of:

- Any Critical or High finding from any Phase 8 review
- Novel architecture, new abstractions, or spec/parser/migration work
- High uncertainty in Correctness / Scope / Architecture
- Touches auth, secrets, PII, or production data paths

Settle on **medium** when:

- Standard extension of existing patterns
- Moderate scope, low-to-medium uncertainty
- Review findings all Medium/Low and incorporated

Settle on **low** when:

- Trivial scope (typo, cosmetic, docstring, one-line bug fix)
- No review phases surfaced anything (or none enabled)
- Confident the work is mechanical

## Step 2: Append the Recommended Execution section

Append to `$SESSION_DIR/SPRINT.md`:

```markdown
## Recommended Execution

**Model**: <model> (<tier> tier)

Before running `/sprint-work`, set the session model:

    /model <model>

Then run:

    /sprint-work [<query>]

Rationale: <2-3 sentences explaining why this tier was picked.>
```

If `spike_choice=accept` (user accepted risk on a spike-worthy uncertainty), include a note in the rationale: "Reviews surfaced structural uncertainty; user accepted the risk and chose to proceed with the full plan. Bump tier to high if you want extra cushion."

## Step 3: Definition of Ready pre-flight

Run a checklist over the final SPRINT.md. Each item should be **yes** before the user is asked to approve:

- [ ] **Goal is observable** — Success Criteria describes outcomes a third party could verify
- [ ] **Scope is bounded** — Implementation Plan has clear P0/P1/Deferred tiering
- [ ] **Definition of Done is testable** — every item is a binary yes/no
- [ ] **Dependencies identified** — external services, prior PRs, config dependencies are listed
- [ ] **Risks have mitigations** — every Risk row has a concrete mitigation
- [ ] **Files Summary populated** — at least the major files are listed
- [ ] **Documentation tasks listed** — anything that introduces new behavior has a doc task
- [ ] **Recommended Execution populated** — tier, command lines, rationale present

If any item fails, **patch SPRINT.md** to address it before transitioning. The DoR is a quality gate, not informational.

## Outputs

- Updated `$SESSION_DIR/SPRINT.md` (Recommended Execution section appended; DoR patches applied)
- Persist:
  ```bash
  scripts/walk.sh set --state "$STATE" --key recommended_tier --value "<high|medium|low>"
  scripts/walk.sh set --state "$STATE" --key recommended_model --value "<opus|sonnet|haiku>"
  ```

## Outgoing edges

- → `ask-approval` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from recommend_execution --to ask_approval
```

## Notes

- **The DoR is binding.** Don't pass forward a SPRINT.md with failed checks; patch them.
- **The Recommended Execution section is the LAST thing the user reads** before approval. Make sure it's current with any patches applied above.
