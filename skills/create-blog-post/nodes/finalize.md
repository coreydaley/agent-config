# Node: finalize (Claude)

Apply the editorial feedback and write the publication-ready final post as a leaf bundle in the repo. This is the first and only node that writes into `content/`. It is also the last work node — once the post is written, the workflow ends.

## Inputs

- `drafts_dir`, `slug`, `yyyy_mm`, `repo_root` (walker state)
- `$DRAFTS_DIR/$SLUG-draft.md`
- `$DRAFTS_DIR/$SLUG-draft-editorial-critique.md`

## Steps

1. **Evaluate the editorial critique**:
   - Which line-level and structural notes improve the post?
   - What will you apply vs. push back on, and why?

2. **Write the final post** as a leaf bundle at `content/posts/$YYYY/$MM/$SLUG/index.md`:
   - Create the bundle directory first: `mkdir -p content/posts/$YYYY/$MM/$SLUG`
   - Apply accepted editorial feedback — tighten pacing, fix seams, cut or rewrite flagged sections
   - Set `draft = false`, unless `orient` made it a held draft (then `draft = true` and the far-future date)
   - Follow all CLAUDE.md conventions precisely (frontmatter, `summary` shape, closing italic question, exactly 1 category, ≤4 approved tags, Accuracy rules)
   - Add `aliases = ["/posts/$SLUG/"]` to the frontmatter for redirect compatibility
   - **Set `date` to the publish date chosen in `orient`.** For today, use a time a few minutes before now (`date '+%Y-%m-%dT%H:%M:%S%z'`); Hugo hides future-dated posts, so a later time would hide it from local preview. For a later day, use `T08:00:00` Eastern so the morning publish job picks it up.

3. **Build-check it**: `hugo --quiet -D -F -d <scratch dir>` must succeed, the post's page must exist in the output, and every internal link in the post must resolve. Delete the scratch build afterwards.

## Outputs

- `content/posts/$YYYY/$MM/$SLUG/index.md` (in the repo, `draft = false`)

## Outgoing edges

- → `terminal` (always — single outgoing edge). The post is complete; nothing is committed, pushed, or published.

```bash
scripts/walk.sh transition --state "$STATE" --from finalize --to terminal
```
