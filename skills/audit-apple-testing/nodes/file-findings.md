# Node: file-findings

File P0 and P1 audit findings from `REPORT.md` as `type/bug` issues in the
project's Forgejo repository. Deferred findings are **skipped**. Runs after
`verify` confirms all artifacts are valid.

## Inputs

- Walker state: `audit_dir`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Steps

### 1. Read MANIFEST.json

```bash
MANIFEST="$AUDIT_DIR/MANIFEST.json"
AUDIT_NAME=$(python3 -c "import json; print(json.load(open('$MANIFEST'))['audit_name'])")
ORG_REPO=$(python3 -c "import json; print(json.load(open('$MANIFEST'))['org_repo'])")
OWNER="${ORG_REPO%%/*}"
REPO="${ORG_REPO##*/}"
```

### 2. Derive the audit domain label

Strip the `apple-` or `web-` prefix from `$AUDIT_NAME` to get the domain:

| AUDIT_NAME | Domain label |
|---|---|
| `apple-testing` | `audit:testing` |
| `web-security` | `audit:security` |
| `architecture` | `audit:architecture` |

```bash
DOMAIN=$(echo "$AUDIT_NAME" | sed 's/^apple-//; s/^web-//')
DOMAIN_LABEL="audit:${DOMAIN}"
```

### 3. Parse findings from REPORT.md

Read `$AUDIT_DIR/REPORT.md`. Identify tier sections by heading prefix:

- **P0**: heading matching `^### P0`
- **P1**: heading matching `^### P1`
- **Defer / Deferred**: **skip** — do not file these

Within each tier section, individual findings begin with a bold line (`**`)
and run until the next bold finding line or the next `###` section heading.

Use Python to extract findings:

```python
import re, json, sys

audit_dir = sys.argv[1]
with open(f"{audit_dir}/REPORT.md") as f:
    text = f.read()

p0_block = re.search(r'(### P0.*?)(?=\n### |\Z)', text, re.DOTALL)
p1_block = re.search(r'(### P1.*?)(?=\n### |\Z)', text, re.DOTALL)

findings = []
for tier, block in [("p0", p0_block), ("p1", p1_block)]:
    if not block:
        continue
    segments = re.split(r'(?=^\*\*)', block.group(1), flags=re.MULTILINE)
    for seg in segments:
        seg = seg.strip()
        if not seg.startswith('**'):
            continue
        title_line = seg.splitlines()[0].strip('*').strip()
        # Strip leading "Task: " prefix if present
        title_line = re.sub(r'^Task:\s*', '', title_line)
        # "S001 — Category — Human title" → use human title (last part)
        parts = title_line.split(' — ', 2)
        human_title = parts[-1] if len(parts) >= 2 else title_line
        findings.append({"tier": tier, "title": human_title, "body": seg})

print(json.dumps(findings))
```

Run as: `python3 /dev/stdin "$AUDIT_DIR" <<'PYEOF' ... PYEOF`

If REPORT.md has no P0 or P1 sections, `findings` will be empty — skip
issue creation, write an empty `forgejo.md`, and continue to handoff.

### 4. Ensure required labels exist

Read the Forgejo token from `~/Library/Application Support/tea/config.yml`
(regex `token:\s*(\S+)`). For each required label, check
`GET /api/v1/repos/{owner}/{repo}/labels` — create only the ones that are
missing by name. **Never edit or recolour an existing label.**

Required labels:

| Name | Color |
|---|---|
| `type/bug` | `#d73a4a` |
| `priority/p0` | `#b60205` |
| `priority/p1` | `#e4e669` |
| `audit:<domain>` | `#0075ca` |

```bash
TOKEN=$(python3 -c "
import re
with open('~/Library/Application Support/tea/config.yml') as f:
    m = re.search(r'token:\s*(\S+)', f.read())
print(m.group(1) if m else '')
")

existing=$(curl -sk "https://mac-mini.example:3000/api/v1/repos/$OWNER/$REPO/labels" \
  -H "Authorization: token $TOKEN" | python3 -c "
import json,sys; print('\n'.join(l['name'] for l in json.load(sys.stdin)))
")

for label_name in "type/bug" "priority/p0" "priority/p1" "$DOMAIN_LABEL"; do
  if ! echo "$existing" | grep -qxF "$label_name"; then
    case "$label_name" in
      type/bug)          color="#d73a4a" ;;
      priority/p0)  color="#b60205" ;;
      priority/p1)  color="#e4e669" ;;
      *)            color="#0075ca" ;;
    esac
    curl -sk -X POST "https://mac-mini.example:3000/api/v1/repos/$OWNER/$REPO/labels" \
      -H "Authorization: token $TOKEN" -H "Content-Type: application/json" \
      -d "{\"name\": \"$label_name\", \"color\": \"$color\"}" > /dev/null
  fi
done
```

### 5. Create one issue per finding

Get the numeric label IDs for `type/bug`, the tier label, and `$DOMAIN_LABEL`:

```bash
LABEL_IDS=$(curl -sk "https://mac-mini.example:3000/api/v1/repos/$OWNER/$REPO/labels" \
  -H "Authorization: token $TOKEN" | python3 -c "
import json, sys
labels = json.load(sys.stdin)
by_name = {l['name']: l['id'] for l in labels}
import os
tier_label = 'priority/' + os.environ.get('TIER', 'p0')
domain = os.environ.get('DOMAIN_LABEL', '')
ids = [by_name.get('type/bug'), by_name.get(tier_label), by_name.get(domain)]
print(json.dumps([i for i in ids if i]))
" TIER="$tier" DOMAIN_LABEL="$DOMAIN_LABEL")
```

For each finding, create one self-assigned issue:

- **Title**: `[$DOMAIN_LABEL] $human_title`
- **Body**: the full finding block from REPORT.md, plus a footer:
  ```

  ---
  _Audit: `$AUDIT_NAME` · report: `$AUDIT_DIR/REPORT.md`_
  ```
- **Labels**: `type/bug` + `priority/<tier>` + `$DOMAIN_LABEL`
- **Assignee**: `coreydaley`

```bash
curl -sk -X POST "https://mac-mini.example:3000/api/v1/repos/$OWNER/$REPO/issues" \
  -H "Authorization: token $TOKEN" -H "Content-Type: application/json" \
  -d "{
    \"title\": \"[$DOMAIN_LABEL] $human_title\",
    \"body\": \"$body\n\n---\n_Audit: \`$AUDIT_NAME\` · report: \`$AUDIT_DIR/REPORT.md\`_\",
    \"labels\": $LABEL_IDS,
    \"assignees\": [\"coreydaley\"]
  }"
```

### 6. Write `forgejo.md`

Write `$AUDIT_DIR/forgejo.md`:

```markdown
# Forgejo Filing — <AUDIT_NAME>

**Repo:** <owner>/<repo>  
**Domain label:** <DOMAIN_LABEL>  
**Filed:** <ISO timestamp>

| # | Title | Priority |
|---|-------|----------|
| <issue_number> | [<title>](<issue_html_url>) | P0/P1 |
```

If zero findings were filed, write the table with a "No P0/P1 findings —
nothing filed." note beneath the header.

### 7. Record in walker state

```bash
scripts/walk.sh set --state "$STATE" --key filed_count --value "<N>"
```

## Outputs

- `$AUDIT_DIR/forgejo.md` written (always — empty table if no findings)
- Forgejo issues created (one per P0/P1 finding)
- Walker state has `filed_count` set

## Outgoing edges

- → `handoff` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from file_findings --to handoff
```

## Failure modes

- **No Forgejo token / unreachable instance**: warn, write `forgejo.md`
  with `status: skipped — Forgejo unavailable`, continue to `handoff`.
  Never abort the audit for a filing failure.
- **API error on a single issue**: log the error in `forgejo.md`, continue
  filing remaining findings. Partial success is acceptable.
- **REPORT.md missing P0/P1 sections** (all-green audit): write empty
  `forgejo.md` and continue.
- **`org_repo` resolves to a GitHub URL or unknown host**: warn in
  `forgejo.md`, skip filing, continue to `handoff`.
