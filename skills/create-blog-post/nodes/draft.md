# Node: draft (Claude)

Write a complete, publication-ready draft following all project conventions.

## Inputs

- `drafts_dir`, `slug`, `yyyy_mm` (walker state)
- The Orientation Summary from `orient`
- `CLAUDE.md` conventions

## Write to: `$DRAFTS_DIR/$SLUG-draft.md`

`$DRAFTS_DIR` was created in `orient` (`~/Reports/<org>/<repo>/blog-posts/$SLUG/`). All intermediate drafts are flat `.md` files there, **outside the repo entirely** — process artifacts follow the project-wide `~/Reports/` convention and never clutter the working tree. Only the final post (in `finalize`) becomes a leaf bundle inside `content/`.

## The draft must include

- **Full TOML frontmatter** (`+++` delimiters, double quotes, all required fields):
  ```toml
  +++
  author = "Corey Daley"
  date = "YYYY-MM-DDTHH:MM:SS-05:00"
  draft = true
  title = "..."
  description = "..."
  summary = "Tight 1-2 sentence excerpt of the post, ~40-60 words."
  tags = ["...", "..."]
  categories = ["..."]
  +++
  ```
  - `description`: one or two sentences, **170 characters max** (the site trims post-card summaries past that). Drives `<meta>`/og description, social previews, Pagefind search, and the post-list excerpts. If the repo `CLAUDE.md` sets a different limit, follow it.
  - `summary`: A single tight excerpt — 1–2 sentences, ~40–60 words — used as the RSS feed item description. Plain prose, no multi-paragraph structure, no "Read more" line (RSS clients link the post themselves). This is the only place `summary` is consumed.
  - `tags`: lowercase, hyphenated. **From the approved list in CLAUDE.md only. Cap at 4.**
  - `categories`: **exactly 1**, Title Case, from the fixed list in CLAUDE.md.
  - `author`: always `"Corey Daley"`. Never the agent or model name.
  - No `image` field.

- **Body**:
  - Engaging introduction that hooks the reader
  - Well-structured sections with headers
  - Concrete examples, analogies, or code snippets where appropriate
  - 800–1500 words (conversational but substantive)
  - Closing italicized question directly related to the post content

## Outputs

- `$DRAFTS_DIR/$SLUG-draft.md`

## Outgoing edges

- → `editorial_review` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from draft --to editorial_review
```
