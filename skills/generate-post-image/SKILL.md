---
name: generate-post-image
description: >-
  Generate, optimize, and insert a hero image into a Hugo blog post leaf bundle.
  Uses Claude API to derive a visual concept, DALL-E 3 to generate the image,
  optimize-images.sh to convert to WebP, and Claude vision to write alt text.
  Trigger when the user asks to generate an image for a blog post, or as Phase 7
  of the create-blog-post workflow.
---

# Generate Post Image

Automatically generate and insert a hero image for a Hugo blog post (leaf bundle layout).

## Scripts

All scripts live alongside this file in `~/.claude/skills/generate-post-image/scripts/`:

- `generate-post-image.py` — main pipeline: concept → DALL-E 3 → download → optimize → alt text → insert
- `optimize-images.sh` — converts PNG/JPG to WebP, resizes oversized images, generates `thumbs/`

Both scripts accept a `BLOG_REPO_ROOT` environment variable so they can be invoked from outside
the blog repo. Always set this when running from the skill directory.

## Prerequisites

- `.env` file at the blog repo root with `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` set
- `.venv/` virtualenv at the blog repo root with required packages:
  ```bash
  python3 -m venv .venv && .venv/bin/pip install anthropic openai requests
  ```
- `cwebp` or `imagemagick` installed for WebP conversion:
  ```bash
  brew install webp       # macOS (preferred)
  brew install imagemagick  # fallback
  ```

## Usage

Run from the blog repo root (`pwd` becomes `BLOG_REPO_ROOT`):

```bash
BLOG_REPO_ROOT=$(pwd) python3 ~/.claude/skills/generate-post-image/scripts/generate-post-image.py \
  content/posts/YYYY/MM/$SLUG/index.md
```

The script self-re-execs with the blog repo's `.venv/bin/python3` automatically — no manual activation needed.

## What the script does

1. **Reads the post** and calls Claude API (`claude-sonnet-4-6`) to derive a 2-3 sentence concrete visual concept from the content
2. **Calls DALL-E 3** to generate a 1792×1024 HD image using the concept plus the blog's house style
3. **Downloads the PNG** to the post's bundle directory as `$SLUG.png`
4. **Runs `optimize-images.sh`** (from this skill's scripts dir) to convert the PNG to WebP and generate a thumbnail in `thumbs/`, then deletes the source PNG
5. **Calls Claude vision** on the resulting WebP to generate accurate alt text (10-15 words)
6. **Inserts into the post**:
   - `image = "$SLUG.webp"` frontmatter field after `categories`
   - `{{< figure-float src="$SLUG.webp" alt="..." >}}` shortcode after closing `+++`

## Output files (inside the post bundle directory)

```
content/posts/YYYY/MM/$SLUG/
├── index.md          ← updated with image field + shortcode
├── $SLUG.webp        ← optimized WebP (used in post body + og:image)
└── thumbs/
    └── $SLUG.webp    ← thumbnail used in post list
```

The source PNG is deleted automatically after the WebP is confirmed on disk.

## Image style

The blog's house style is baked into the script:

> Flat vector illustration. Dark navy or charcoal background. Electric blue and warm amber as primary accent colors. Clean lines, minimal detail, no photorealism. No text, letters, words, or numbers anywhere in the image. Modern SaaS marketing illustration aesthetic, similar to Stripe or Linear. Landscape orientation, 16:9 ratio.

## Fallback (if script fails)

If the script fails (missing API keys, network error, or missing tools), fall back to manual:

1. Output an image generation prompt using the post's central visual metaphor and the house style above
2. Remind the user to:
   - Place the downloaded image in `content/posts/YYYY/MM/$SLUG/`
   - Run `BLOG_REPO_ROOT=$BLOG_ROOT ~/.claude/skills/generate-post-image/scripts/optimize-images.sh`
   - Manually insert `{{< figure-float src="$SLUG.webp" alt="..." >}}` after closing `+++` in `index.md`
   - Manually add `image = "$SLUG.webp"` to the frontmatter
