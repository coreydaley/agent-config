---
description: Create a blog post draft by writing a Claude draft, spawning a Codex competing draft, critiquing each other's work, synthesizing, getting a Codex editorial review, then producing the final post following project conventions.
---

# Create Blog Post: Competitive Draft Workflow

You are orchestrating a workflow to produce a high-quality blog post through competitive ideation, mutual critique, synthesis, and editorial review with Codex.

## Topic

$ARGUMENTS

## Workflow Overview

1. **Orient** - Research the topic and review project conventions
2. **Draft** - Write your Claude draft
3. **Compete** - Codex creates an independent draft and critiques yours; Claude critiques Codex's draft
4. **Synthesize** - Compare and merge both drafts into a synthesized draft
5. **Editorial Review** - Codex reviews the synthesized draft as a professional editor
6. **Finalize** - Apply editorial feedback and write the final post
7. **Image** - Generate and insert the hero image

Use TodoWrite to track progress through each phase.

---

## Phase 1: Orient

**Goal**: Understand the topic deeply and internalize the project's content conventions.

### Steps:

1. Read `AGENTS.md` to internalize frontmatter requirements, image workflow, category rules, and tone conventions.
2. Read 2-3 recent posts from `content/posts/` to calibrate voice, tone, structure, and length.
3. Research the topic using available tools (WebSearch if helpful).
4. Derive a URL-safe slug from the topic (lowercase, hyphenated, e.g. `my-post-topic`). Store this as `SLUG`.
5. Determine the current year and month (e.g. `2026/03`). Store this as `YYYY/MM`. The final post path will be `content/posts/YYYY/MM/$SLUG/index.md`.

### Deliverable:

Write a brief **Orientation Summary** covering:
- Core argument or angle for the post
- Target audience
- 3-5 key points to cover
- Proposed slug, title, tags, and 3 categories

---

## Phase 2: Draft (Claude)

**Goal**: Write a complete, publication-ready draft following all project conventions.

### Write to: `drafts/$SLUG-claude-draft.md`

Create the drafts directory if needed:
```bash
mkdir -p drafts
```

> **Note:** Drafts are flat `.md` files stored in `drafts/` at the repo root (outside `content/` so Hugo never renders them). Only the final post becomes a leaf bundle.

The draft must include:

- **Full TOML frontmatter** (`+++` delimiters, double quotes, all required fields):
  ```toml
  +++
  author = "Claude Code (Claude Sonnet 4.6)"
  date = "YYYY-MM-DDTHH:MM:SS-05:00"
  draft = true
  title = "..."
  description = "..."
  summary = """Hook paragraph — 2-3 sentences on the problem or angle.

What the post covers — key insight or main content, 2-3 sentences.

Closing question or CTA?

Read more at https://coreydaley.dev/posts/YYYY/MM/$SLUG/"""
  tags = ["...", "..."]
  categories = ["...", "...", "..."]
  +++
  ```
  - `description`: SEO-friendly, ~75 words
  - `summary`: Triple-quoted multi-line TOML (`"""`). 2–3 short paragraphs formatted for direct LinkedIn copy-paste: (1) hook/problem, (2) what the post covers, (3) closing question or CTA. Final line is always `Read more at https://coreydaley.dev/posts/YYYY/MM/$SLUG/`. Closing `"""` on its own line with no trailing blank line before it.
  - `tags`: lowercase, hyphenated, specific
  - `categories`: exactly 3, Title Case
  - No `image` field in the draft (images are added after the image optimization workflow)

- **Body**:
  - Engaging introduction that hooks the reader
  - Well-structured sections with headers
  - Concrete examples, analogies, or code snippets where appropriate
  - 800–1500 words (conversational but substantive)
  - Closing italicized question directly related to the post content

---

## Phase 3: Compete (Codex)

**Goal**: Get Codex's independent take and critique of your draft; write your critique of Codex's draft.

### Execute Codex:

```bash
codex exec "Please read drafts/$SLUG-claude-draft.md. This is a Claude-written draft for a personal tech blog. Also read CLAUDE.md for the project content conventions. Then: (1) Write your own independent draft to drafts/$SLUG-codex-draft.md — same topic, same TOML frontmatter format with double-quote strings, but your own angle, structure, and voice. Only AFTER your draft is complete, (2) read Claude's draft again and write a critique to drafts/$SLUG-claude-draft-codex-critique.md — what works, what's weak, what's missing, what you'd change."
```

### Wait for Codex to complete.

Codex will produce:
- `drafts/$SLUG-codex-draft.md` — Independent draft
- `drafts/$SLUG-claude-draft-codex-critique.md` — Critique of your draft

### Read both files once Codex finishes.

### Write your critique of the Codex draft:

After reading the Codex draft, write your own critique to `drafts/$SLUG-codex-draft-claude-critique.md`. Evaluate:
- What angle or framing did Codex take that differs from yours?
- What does Codex do better — structure, conciseness, voice, examples?
- What is weak, missing, or wrong in Codex's draft?
- What would you defend from your own draft that Codex missed or handled worse?

This critique is your editorial brief going into synthesis — be specific and opinionated.

---

## Phase 4: Synthesize

**Goal**: Merge the best of both drafts into a synthesized draft for editorial review.

### Synthesis process:

1. **Evaluate both critiques**:
   - Codex's critique of your draft: which criticisms are valid? What will you defend?
   - Your critique of Codex's draft: what from Codex is worth taking? What should be left behind?

2. **Compare the two drafts**:
   - Angle/framing differences
   - Structural differences
   - Examples or analogies unique to each
   - Tone and voice differences

3. **Write merge notes** to `drafts/$SLUG-merge-notes.md`:
   ```markdown
   # Merge Notes: [Post Title]

   ## Claude Draft Strengths
   - ...

   ## Codex Draft Strengths
   - ...

   ## Valid Critiques Accepted (from Codex's critique of Claude draft)
   - ...

   ## Valid Critiques Accepted (from Claude's critique of Codex draft)
   - ...

   ## Critiques Rejected (with reasoning)
   - ...

   ## Final Decisions
   - ...
   ```

4. **Write the synthesized draft** to `drafts/$SLUG-synthesized-draft.md`:
   - Incorporate the best angle, structure, examples, and phrasing from both drafts
   - Apply all valid critiques from both directions
   - Use full TOML frontmatter with `draft = true`
   - Follow all CLAUDE.md conventions (closing question, etc.)
   - Do NOT set `draft = false` yet — the editorial review comes next

---

## Phase 5: Editorial Review (Codex)

**Goal**: Have Codex review the synthesized draft as a professional editor before finalizing.

### Execute Codex:

```bash
codex exec "Please read drafts/$SLUG-synthesized-draft.md. This is a synthesized blog post draft for a personal tech blog. Also read CLAUDE.md for the project content conventions. Act as a professional editor. Write an editorial critique to drafts/$SLUG-synthesized-draft-editorial-critique.md covering: (1) overall clarity and argument strength, (2) pacing and structure — are any sections too long, too short, or in the wrong order?, (3) voice consistency — does the post read as one cohesive piece or does it have seams from the merge?, (4) specific lines or paragraphs to cut, rewrite, or move, (5) whether the opening hook and closing question are strong. Be direct and specific — line-level feedback where useful."
```

### Wait for Codex to complete.

Codex will produce:
- `drafts/$SLUG-synthesized-draft-editorial-critique.md` — Professional editorial critique

### Read the critique carefully before proceeding to Phase 6.

---

## Phase 6: Finalize

**Goal**: Apply the editorial feedback and write the publication-ready final post.

1. **Evaluate the editorial critique**:
   - Which line-level and structural notes improve the post?
   - What will you apply vs. push back on, and why?

2. **Write the final post** as a leaf bundle at `content/posts/YYYY/MM/$SLUG/index.md`:
   - Create the bundle directory first: `mkdir -p content/posts/YYYY/MM/$SLUG`
   - Apply accepted editorial feedback — tighten pacing, fix seams, cut or rewrite flagged sections
   - Set `draft = false`
   - Follow all CLAUDE.md conventions precisely (frontmatter, closing question, etc.)
   - Add `aliases = ["/posts/$SLUG/"]` to the frontmatter for redirect compatibility
   - Do NOT include an `image` field yet (image is added in Phase 7)
   - **Set `date` to a few minutes before the current local time** — run `date '+%Y-%m-%dT%H:%M:%S%z'` and subtract ~5 minutes. Hugo will not serve a post whose timestamp is in the future, so a midnight or templated time will cause the post to be invisible during local preview.

3. **Proceed immediately to Phase 7** — do not pause for user approval.

---

## Phase 7: Generate Hero Image

**Goal**: Automatically generate, optimize, and insert a hero image into the final post using the `generate-post-image` skill.

### Invoke the generate-post-image skill:

Use the `generate-post-image` skill to run the full image pipeline for the post:

```bash
python3 scripts/generate-post-image.py content/posts/YYYY/MM/$SLUG/index.md
```

The skill will:
1. Call the Claude API to derive a visual concept from the post content
2. Call DALL-E 3 (OpenAI API) to generate a 1792×1024 HD image
3. Download the PNG to the **post's bundle directory** (`content/posts/YYYY/MM/$SLUG/$SLUG.png`)
4. Optimize to WebP via `./scripts/optimize-images.sh` (creates `$SLUG.webp` and `thumbs/$SLUG.webp` in the bundle)
5. Call Claude vision to generate accurate alt text from the actual image
6. Insert the `figure-float` shortcode and `image` frontmatter field into `index.md`

The skill handles prerequisite checks, fallback instructions, and all file placement details. Refer to the `generate-post-image` skill for full documentation.

### After the image pipeline completes (success or fallback):

Output the following block verbatim so the user can copy/paste directly into LinkedIn, X, or other social media. No labels, no extra text — just the content between the rules:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<full text of the `summary` frontmatter field, verbatim — it is already paragraph-formatted with the permalink as the last line>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

> **Important:** Always use the canonical URL in the `summary` field (`/posts/YYYY/MM/$SLUG/`) for social sharing, not the short alias (`/posts/$SLUG/`). LinkedIn and other social scrapers do not follow `<meta http-equiv=refresh>` redirects, so the alias URL results in no preview image.

---

## File Structure

After this workflow completes, you'll have:

```
drafts/                              ← gitignored, outside content/ (Hugo never renders these)
├── $SLUG-claude-draft.md
├── $SLUG-codex-draft.md
├── $SLUG-claude-draft-codex-critique.md
├── $SLUG-codex-draft-claude-critique.md
├── $SLUG-merge-notes.md
├── $SLUG-synthesized-draft.md
└── $SLUG-synthesized-draft-editorial-critique.md

content/posts/
└── YYYY/
    └── MM/
        └── $SLUG/               ← leaf bundle (Hugo page bundle)
            ├── index.md         ← final post (image field + shortcode inserted)
            ├── $SLUG.png        ← original PNG (preserved locally, stripped by CI)
            ├── $SLUG.webp       ← optimized WebP (used in post body + og:image)
            └── thumbs/
                └── $SLUG.webp   ← thumbnail used in post list
```

> All post images live **inside the leaf bundle directory**, not in `static/images/posts/`.
> The `image` frontmatter field and shortcode `src` use the **filename only** (e.g. `"hero.webp"`), not a path.

---

## Output Checklist

- [ ] CLAUDE.md read and conventions internalized
- [ ] Recent posts reviewed for tone/voice calibration
- [ ] Orientation summary written (slug, angle, key points, categories)
- [ ] Claude draft written to `drafts/$SLUG-claude-draft.md`
- [ ] Codex executed and completed
- [ ] Codex draft received (`$SLUG-codex-draft.md`)
- [ ] Codex critique received (`$SLUG-claude-draft-codex-critique.md`)
- [ ] Claude critique of Codex draft written (`$SLUG-codex-draft-claude-critique.md`)
- [ ] Merge notes written (`$SLUG-merge-notes.md`)
- [ ] Synthesized draft written to `drafts/$SLUG-synthesized-draft.md`
- [ ] Codex editorial review completed (`$SLUG-synthesized-draft-editorial-critique.md`)
- [ ] Final post written to `content/posts/YYYY/MM/$SLUG/index.md` with `draft = false`
- [ ] `aliases = ["/posts/$SLUG/"]` added to frontmatter
- [ ] Hero image generated and inserted via `generate-post-image` skill (`python3 scripts/generate-post-image.py content/posts/YYYY/MM/$SLUG/index.md`)
- [ ] Post URL and social caption output for copy/paste
