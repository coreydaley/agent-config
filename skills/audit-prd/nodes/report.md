# Node: report

Phase 5 of the framework. Convert the synthesized findings into `REPORT.md`,
headlined by the **readiness verdict** and tiered by severity. The report is
the machine-actionable input for a follow-up "update the PRD based on this
report" turn, so it must record the source ref and carry concrete suggested
revisions.

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/section-map.md`
- Walker state: `audit_dir`, `da_status`, `codex_status`, `source_kind`,
  `source_ref`, `prd_title`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Readiness verdict (the headline)

Derive mechanically from the calibrated severities in `synthesis.md`:

| Condition | Verdict |
|---|---|
| ≥1 **Blocker** | 🔴 **Not ready** — do not start building; revise the Blockers first |
| no Blocker, ≥1 **Major** | 🟡 **Needs revision** — revise the flagged sections before building |
| only **Minor/Nit**, or none | 🟢 **Ready to build** — proceed; fix minors inline |

## Severity → tier mapping

| Severity | Tier |
|---|---|
| **Blocker** | **Must fix before build** |
| Major | Should fix before build |
| Minor | Fix during build |
| Nit | Optional polish |

## Per-finding contents

Each finding block must include:

- **ID** — the synthesis `S###` ID
- **Dimension** — one of the 11
- **PRD Location** — section heading / quoted anchor (or `(absent)`)
- **Problem** — what's wrong, in one or two sentences
- **Suggested Revision** — the concrete rewrite to apply to the PRD
- **Why It Matters** — the build/test/scope consequence of leaving it

## No-findings case

If `synthesis.md` has zero findings after Phase 4:

- Verdict = 🟢 **Ready to build**.
- Emit a single confirmation task: `Verify no findings — prd — <title>, <date>`
  describing dimensions reviewed, reviewers, and date. Don't fabricate findings.

## Output template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# PRD Audit — <prd_title> (<YYYY-MM-DD>)

## Verdict: <🔴 Not ready | 🟡 Needs revision | 🟢 Ready to build>

<1-2 sentences justifying the verdict and naming the single most important
thing to fix.>

## Source (for follow-up edits)

- **Kind:** <file | wiki>
- **Ref:** <source_ref>          ← edit THIS to apply revisions
- **Audited copy:** <$AUDIT_DIR/prd-source.md> (read-only snapshot)

> This audit did not modify the PRD. To apply fixes, point an agent at the
> source ref above with this report:
> `update the PRD at <source_ref> based on <$AUDIT_DIR/REPORT.md>`

## Summary

| Severity | Count |
|---|---|
| Blocker | N |
| Major | N |
| Minor | N |
| Nit | N |
| Total | N |

| Dimension | Count |
|---|---|
<non-zero dimensions only>

Intermediate audit artifacts:
- $AUDIT_DIR/prd-source.md
- $AUDIT_DIR/tooling-raw/section-map.md
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/codex.md           <or "MISSING — single-agent run" if codex_status=failed>
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Findings

### Must fix before build  (Blocker)

<one block per Blocker finding>

**S### — <Dimension> — <Title>**
- PRD Location: <heading / quote / (absent)>
- Problem: <description>
- Suggested Revision: <concrete rewrite>
- Why It Matters: <consequence>

### Should fix before build  (Major)

<one block per Major finding, same format>

### Fix during build  (Minor)

<one block per Minor finding>

### Optional polish  (Nit)

<one-line per Nit finding>

## Contradiction Clusters

<reproduce from synthesis.md if any>

## Definition of Done

- [ ] All Blocker and Major findings resolved in the PRD source
- [ ] Each affected requirement is now testable with explicit acceptance criteria
- [ ] Goals/non-goals and metrics are mutually consistent (no open contradiction cluster)
- [ ] Privacy/security constraints stated for any sensitive-data handling
- [ ] Re-run /audit-prd and confirm the verdict is 🟢 Ready to build
```

## Outputs

- `$AUDIT_DIR/REPORT.md` exists, non-empty, headlined by the verdict, with
  tiers populated and the source ref recorded.

## Outgoing edges

- → `verify` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from report --to verify
```

## Failure modes

- Synthesis has zero findings → produce the no-findings confirmation with a
  🟢 verdict; still transition to `verify`.
- A Blocker without a concrete suggested revision → write what's known and
  flag `**REVISION INCOMPLETE**` in the block; verify still passes on artifact
  existence, but the user sees the gap.
