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
   - Set `draft = false`
   - Follow all CLAUDE.md conventions precisely (frontmatter, `summary` shape, closing italic question, exactly 1 category, ≤4 approved tags)
   - Add `aliases = ["/posts/$SLUG/"]` to the frontmatter for redirect compatibility
   - **Set `date` to a few minutes before the current local time** — run `date '+%Y-%m-%dT%H:%M:%S%z'` and subtract ~5 minutes. Hugo will not serve a post whose timestamp is in the future, so a midnight or templated time makes the post invisible during local preview.

## Outputs

- `content/posts/$YYYY/$MM/$SLUG/index.md` (in the repo, `draft = false`)

## Outgoing edges

- → `terminal` (always — single outgoing edge). The post is complete; nothing is committed, pushed, or published.

```bash
scripts/walk.sh transition --state "$STATE" --from finalize --to terminal
```
