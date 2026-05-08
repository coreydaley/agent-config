# Node: fetch-context

Pull everything we need before review can run: PR metadata, the diff, and CI status.

## Inputs

- `pr_number`, `pr_dir` from walker state (`scripts/walk.sh get`)

## Steps

```bash
STATE="$PR_DIR/.walk-state.json"
PR_NUMBER=$(scripts/walk.sh get --state "$STATE" --key pr_number)
PR_DIR=$(scripts/walk.sh get --state "$STATE" --key pr_dir)
```

1. **Fetch PR metadata** and capture for the review header:
   ```bash
   gh pr view "$PR_NUMBER" --json number,title,body,author,baseRefName,headRefName,additions,deletions,files,labels,state,headRefOid \
     > "$PR_DIR/metadata.json"
   ```
2. **Save the diff:**
   ```bash
   gh pr diff "$PR_NUMBER" > "$PR_DIR/diff.patch"
   ```
3. **Capture CI status** (truncated to keep output manageable):
   ```bash
   gh pr checks "$PR_NUMBER" 2>&1 | head -40 > "$PR_DIR/ci-status.txt"
   ```
4. **Print a brief orient summary** (3–5 bullets): PR title, author, base branch, scope (files / +adds / -dels), CI status.

## Outputs

- `$PR_DIR/metadata.json`
- `$PR_DIR/diff.patch`
- `$PR_DIR/ci-status.txt`

## Outgoing edges

- → `decide-prior` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from fetch_context --to decide_prior
```

## Failure modes

- `gh pr diff` fails (e.g. PR with no diff, very rare): bail with a clear message — there's nothing to review.
- `gh pr view` returns a non-PR (maybe an issue number was passed by mistake): bail.
- CI status command timing out or returning nothing: not fatal, save what we got and move on.
