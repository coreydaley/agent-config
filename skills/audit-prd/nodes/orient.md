# Node: orient

Phase 1 of the framework. The unit of audit is a *document*, so there is no
security/SAST tooling here. Instead: read the staged PRD, build a **section
map** (which canonical PRD sections are present vs. missing) into
`tooling-raw/`, and run the **reviewability gate** — if the source isn't
actually a reviewable PRD (empty, a stub, or not a PRD at all), take the
`emergency` edge before spending the dual-agent review.

## Inputs

- `$AUDIT_DIR/prd-source.md` (the fetched PRD)
- Walker state: `audit_dir`, `source_kind`, `source_ref`, `prd_title`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
SRC="$AUDIT_DIR/prd-source.md"
```

## Steps

### 1. Build the section map

Read `prd-source.md` and record which of the canonical PRD dimensions have a
corresponding section / substantive content. This is the orientation the
Phase 2 reviewers (Claude + Codex) read first — a map of where the document
is thin, not a findings file. Write it to
`$AUDIT_DIR/tooling-raw/section-map.md`:

```markdown
# PRD Section Map — <prd_title>

Source: <source_kind> — <source_ref>
Word count: <N>   Headings: <N>

| Dimension | Present? | Where (heading / quote) | First-glance note |
|---|---|---|---|
| Problem / why | yes/no/partial | <heading or "—"> | <terse> |
| Users & non-users | … | | |
| Goals & non-goals | … | | |
| Success metrics | … | | |
| Functional requirements | … | | |
| Acceptance criteria / testability | … | | |
| Edge cases / error states | … | | |
| Dependencies & assumptions | … | | |
| Constraints (incl. privacy/security) | … | | |
| Open questions | … | | |
| Scope / over-engineering signals | … | | |
| Feasibility | … | | |
```

This is a *presence* map only — judging quality is Phase 2's job. Don't write
findings here.

### 2. Reviewability gate (emergency check)

Compute cheap signals and decide whether the source is worth a full audit.

```bash
WORDS=$(wc -w < "$SRC" | tr -d ' ')
HEADINGS=$(grep -cE '^#{1,6} ' "$SRC" || true)
EMERGENCY=0
# Heuristic floor: a genuine PRD has substance. Tune with judgment.
if [ "$WORDS" -lt 80 ]; then EMERGENCY=1; fi
```

Beyond the word floor, take the `emergency` edge if **manual inspection**
shows the source is not a reviewable PRD: it's a title with no body, a link
dump, meeting notes, or a different document type entirely. Use judgment —
a short-but-real PRD (clear problem + a handful of crisp requirements) should
**proceed**, not emergency-exit. When uncertain, `proceed` and let the
reviewers flag thinness as findings rather than halting.

### 3. Survey (conversational, not persisted)

Note for the user's situational awareness: resolved source, PRD title, word
count, which dimensions the section map found present vs. missing, and the
fact that the PRD itself will not be modified (read-only audit).

### 4. Persist state

```bash
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "$EMERGENCY"
test -s "$AUDIT_DIR/tooling-raw/section-map.md" \
  || bail "section-map.md not written — refusing to transition"
```

## Outputs

- `$AUDIT_DIR/tooling-raw/section-map.md` — present/missing dimension map
- Walker state has `emergency_exit` set

## Outgoing edges

- **`proceed`** → `independent_reviews`. Normal path: source is a reviewable PRD.
- **`emergency`** → `emergency_exit`. Source is empty / a stub / not a PRD.

```bash
if [ "$EMERGENCY" -eq 1 ]; then
  scripts/walk.sh transition --state "$STATE" --from orient --to emergency_exit --condition emergency
else
  scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
fi
```

## Failure modes

- `prd-source.md` missing → init bug; bail (init should have caught it).
- Borderline thin PRD → human judgment call; prefer `proceed` and let the
  reviewers rate completeness as findings rather than halting the audit.
