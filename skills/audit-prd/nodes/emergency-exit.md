# Node: emergency-exit

Orientation determined the source is **not a reviewable PRD** (empty, a
stub, a link dump, or a different document type). Halt before Phase 2 rather
than spend a dual-agent review on something that can't be meaningfully
audited. Write `EMERGENCY.md` explaining why and what the PRD needs before
it's worth auditing.

## Inputs

- `$AUDIT_DIR/prd-source.md` (the too-thin source)
- `$AUDIT_DIR/tooling-raw/section-map.md` (what was / wasn't found)
- Walker state: `audit_dir`, `source_ref`, `prd_title`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Steps

### 1. Write EMERGENCY.md

```bash
cat > "$AUDIT_DIR/EMERGENCY.md" <<EOF
# NOT A REVIEWABLE PRD — prd — $(date -u +%Y-%m-%dT%H:%M:%SZ)

## Trigger

The source resolved but is not substantial enough to audit as a PRD. The
audit has **halted before Phase 2**. No reviewer artifacts were produced.

## Source

- <source_kind>: <source_ref>
- Word count / headings: <from section-map.md>

## What's missing

At minimum, a reviewable PRD needs a stated **problem**, an intended
**user**, and a handful of concrete **requirements**. The section map shows
which canonical dimensions are absent:

<paste the "no" rows from tooling-raw/section-map.md>

## Next

1. Flesh out the PRD until it states a problem, a user, goals/non-goals, and
   testable requirements.
2. Re-run \`/audit-prd <source>\`.
EOF
```

Fill in the placeholders from `section-map.md` and walker state.

### 2. Tell the user

Print a short message: the source isn't a reviewable PRD yet, point at
`$AUDIT_DIR/EMERGENCY.md`, and confirm no Phase 2+ work ran. The PRD itself
was not modified.

## Outputs

- `$AUDIT_DIR/EMERGENCY.md` written
- No reviewer artifacts produced for this run

## Outgoing edges

- → `terminal` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from emergency_exit --to terminal
```

## Failure modes

- False trigger (a genuinely short but valid PRD) → if on reflection the
  source *is* reviewable, the right fix is to re-run; orient should have
  taken `proceed`. Prefer that over auditing a stub. `audit-verify.sh`
  short-circuits to success when `EMERGENCY.md` is present, so the run still
  closes cleanly.

## Notes

- This node is **terminal-bound**, mirroring the rest of the audit-* family's
  emergency-exit. The handoff format differs: point the user at
  `EMERGENCY.md`. No companion copy is written beside the source on this path.
