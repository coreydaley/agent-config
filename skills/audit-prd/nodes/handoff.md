# Node: handoff

**Verify already passed.** This node writes the **companion copy** of the
report beside the PRD source, then prints the hand-off (verdict, counts,
report path, verify output, next step).

## Inputs

- Walker state: `audit_dir`, `verify_output`, `da_status`, `codex_status`,
  `source_kind`, `source_ref`, `companion_kind`, `companion_target`, `prd_title`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
VERIFY_OUTPUT=$(scripts/walk.sh get --state "$STATE" --key verify_output)
COMPANION_KIND=$(scripts/walk.sh get --state "$STATE" --key companion_kind)
COMPANION_TARGET=$(scripts/walk.sh get --state "$STATE" --key companion_target)
SOURCE_REF=$(scripts/walk.sh get --state "$STATE" --key source_ref)
```

## Step 1 — Write the companion copy beside the source

The canonical report stays under `~/Reports/...`. A **copy** lands next to
the PRD so the review is discoverable where the PRD lives. The companion is
the `REPORT.md` content with a one-line header noting the canonical location.

Build the companion body once:

```bash
COMPANION_BODY="$AUDIT_DIR/.companion.md"
{
  echo "> Canonical audit: $AUDIT_DIR/REPORT.md"
  echo "> Source audited: $SOURCE_REF (not modified by this audit)"
  echo ""
  cat "$AUDIT_DIR/REPORT.md"
} > "$COMPANION_BODY"
```

### file — beside the PRD on disk

`companion_target` is the absolute path resolved by `prd-runner.sh`, with the
audit run's timestamp baked in (`<base>-review-<TS>.md`, or
`<base> Review <TS>.md` for vault notes), so repeat audits accumulate rather
than overwrite.

```bash
if [ "$COMPANION_KIND" = "file" ]; then
  cp "$COMPANION_BODY" "$COMPANION_TARGET" \
    && echo "Companion review written: $COMPANION_TARGET" \
    || echo "⚠️ failed to write companion beside source: $COMPANION_TARGET"
fi
```

### wiki — a `<Page> Review <TScompact>` Forgejo wiki page

`companion_target` is the page title (`<SourcePage> Review <TScompact>`, spaces +
a hyphen-free timestamp — Forgejo escapes literal `-` in titles as `.-`). Create it via
the Forgejo API (the wiki has no local checkout). Derive owner/repo from the
manifest's `source_ref` (`<owner>/<repo>:<Page>`).

```bash
if [ "$COMPANION_KIND" = "wiki" ]; then
  TOKEN=$(awk '/name: homelab/{f=1} f&&/token:/{print $2; exit}' \
    "$HOME/Library/Application Support/tea/config.yml")
  OWNER_REPO="${SOURCE_REF%%:*}"          # owner/repo
  OWNER="${OWNER_REPO%%/*}"; REPO="${OWNER_REPO#*/}"
  B64=$(base64 < "$COMPANION_BODY" | tr -d '\n')
  API="https://mac-mini.example:3000/api/v1/repos/$OWNER/$REPO/wiki"
  # Try create; if the page already exists, edit it instead.
  HTTP=$(curl -sk -o /dev/null -w '%{http_code}' -X POST "$API/new" \
    -H "Authorization: token $TOKEN" -H 'Content-Type: application/json' \
    -d "$(jq -nc --arg t "$COMPANION_TARGET" --arg c "$B64" \
          '{title:$t, content_base64:$c, message:"Add PRD audit review"}')")
  if [ "$HTTP" = "409" ] || [ "$HTTP" = "422" ]; then
    PAGE_ENC="${COMPANION_TARGET// /%20}"
    curl -sk -o /dev/null -X PATCH "$API/page/$PAGE_ENC" \
      -H "Authorization: token $TOKEN" -H 'Content-Type: application/json' \
      -d "$(jq -nc --arg t "$COMPANION_TARGET" --arg c "$B64" \
            '{title:$t, content_base64:$c, message:"Update PRD audit review"}')"
  fi
  echo "Companion review page: $OWNER/$REPO wiki → $COMPANION_TARGET (HTTP $HTTP)"
fi
```

If the companion write fails (permissions, token, network), **don't fail the
audit** — the canonical report is already on disk. Note the failure in the
hand-off so the user can copy it manually.

## Step 2 — Extract verdict + counts from REPORT.md

Parse the `## Verdict:` line and the Summary table for the hand-off.

## Step 3 — Print the hand-off

```
> ✅ PRD Audit complete — <Verdict>.
>
> **PRD:** <prd_title>
> **Report:** <$AUDIT_DIR/REPORT.md>
> **Companion:** <companion_target>   (beside the source)
>
> **Findings:** Blocker: X, Major: Y, Minor: Z, Nit: W.
> Top issue: <one-line description of the highest-severity finding>.
>
> **Verification output:**
> <verify_output verbatim>
>
> **The PRD was not modified.** To apply the suggested revisions:
> `update the PRD at <source_ref> based on <$AUDIT_DIR/REPORT.md>`
```

If `CODEX_STATUS=failed`, add: `- **Degraded run**: Codex review unavailable;
single-agent audit. Consider re-running once codex is reachable.`

If `DA_STATUS=failed`, add: `- **Degraded run**: Devil's advocate pass did not
complete; synthesis was not stress-tested.`

If the companion write failed, add a line pointing the user at the canonical
report to copy manually.

## Step 4 — Mark complete

```bash
scripts/walk.sh set --state "$STATE" --key handoff_printed --value "yes"
scripts/walk.sh transition --state "$STATE" --from handoff --to terminal
```

## Outputs

- Companion copy written beside the source (or failure noted)
- Hand-off message printed; walker state updated

## Failure modes

- REPORT.md unparseable for counts → fall back to "see REPORT.md" without
  numbers.
- Companion write fails → audit still succeeds; surface the failure and the
  canonical path.
