# Node: file-findings

File P0 and P1 audit findings from `REPORT.md` as `type/bug` issues in the
project's GitHub repository via the `gh` CLI. Deferred findings are **skipped**.
Runs after `verify` confirms all artifacts are valid.

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

`gh` targets the `$OWNER/$REPO` slug via `--repo`; it authenticates with your
existing `gh auth` credential, so there is no token file to read.

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
issue creation, write an empty `github.md`, and continue to handoff.

### 4. Ensure required labels exist

`gh label create` errors if a label already exists, so swallow that error
(`|| true`) and **never edit or recolour an existing label**.

Required labels:

| Name | Color |
|---|---|
| `type/bug` | `d73a4a` |
| `priority/p0` | `b60205` |
| `priority/p1` | `e4e669` |
| `audit:<domain>` | `0075ca` |

```bash
for label_name in "type/bug" "priority/p0" "priority/p1" "$DOMAIN_LABEL"; do
  case "$label_name" in
    type/bug)     color="d73a4a" ;;
    priority/p0)  color="b60205" ;;
    priority/p1)  color="e4e669" ;;
    *)            color="0075ca" ;;
  esac
  gh label create "$label_name" --color "$color" --repo "$OWNER/$REPO" 2>/dev/null || true
done
```

### 5. Create one issue per finding

For each finding, create one self-assigned issue. Write the finding body to a
temp file (`--body-file`) to avoid shell-escaping the multi-line Markdown:

- **Title**: `[$DOMAIN_LABEL] $human_title`
- **Body**: the full finding block from REPORT.md, plus a footer:
  ```

  ---
  _Audit: `$AUDIT_NAME` · report: `$AUDIT_DIR/REPORT.md`_
  ```
- **Labels**: `type/bug` + `priority/<tier>` + `$DOMAIN_LABEL`
- **Assignee**: `@me`

```bash
BODY_FILE=$(mktemp)
{
  printf '%s\n\n' "$body"
  printf -- '---\n'
  printf '_Audit: `%s` · report: `%s`_\n' "$AUDIT_NAME" "$AUDIT_DIR/REPORT.md"
} > "$BODY_FILE"

ISSUE_URL=$(gh issue create \
  --repo "$OWNER/$REPO" \
  --title "[$DOMAIN_LABEL] $human_title" \
  --body-file "$BODY_FILE" \
  --label "type/bug" --label "priority/$tier" --label "$DOMAIN_LABEL" \
  --assignee "@me")
rm -f "$BODY_FILE"
```

`gh issue create` prints the new issue's URL on stdout — capture it for
`github.md`.

### 6. Write `github.md`

Write `$AUDIT_DIR/github.md`:

```markdown
# GitHub Filing — <AUDIT_NAME>

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

- `$AUDIT_DIR/github.md` written (always — empty table if no findings)
- GitHub issues created (one per P0/P1 finding)
- Walker state has `filed_count` set

## Outgoing edges

- → `handoff` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from file_findings --to handoff
```

## Failure modes

- **`gh` not authenticated / GitHub unreachable**: warn, write `github.md`
  with `status: skipped — GitHub unavailable`, continue to `handoff`.
  Never abort the audit for a filing failure.
- **API error on a single issue**: log the error in `github.md`, continue
  filing remaining findings. Partial success is acceptable.
- **REPORT.md missing P0/P1 sections** (all-green audit): write empty
  `github.md` and continue.
- **`org_repo` resolves to a non-GitHub / unknown host**: warn in
  `github.md`, skip filing, continue to `handoff`.
