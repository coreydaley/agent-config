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

## Prerequisites

- `.env` file at the repo root with `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` set
- `.venv/` virtualenv at the repo root with required packages:
  ```bash
  python3 -m venv .venv && .venv/bin/pip install anthropic openai requests
  ```
- `scripts/optimize-images.sh` present (handles WebP conversion and thumbnails)
- `cwebp` or `imagemagick` installed for WebP conversion:
  ```bash
  brew install webp       # macOS (preferred)
  brew install imagemagick  # fallback
  ```

## Usage

```bash
python3 scripts/generate-post-image.py content/posts/YYYY/MM/$SLUG/index.md
```

The script self-re-execs with `.venv/bin/python3` automatically — no manual activation needed.

## What the script does

1. **Reads the post** and calls Claude API (`claude-sonnet-4-6`) to derive a 2-3 sentence concrete visual concept from the content
2. **Calls DALL-E 3** to generate a 1792×1024 HD image using the concept plus the blog's house style
3. **Downloads the PNG** to the post's bundle directory as `$SLUG.png`
4. **Runs `./scripts/optimize-images.sh`** to convert the PNG to WebP and generate a thumbnail in `thumbs/`
5. **Calls Claude vision** on the resulting WebP to generate accurate alt text (10-15 words)
6. **Inserts into the post**:
   - `image = "$SLUG.webp"` frontmatter field after `categories`
   - `{{< figure-float src="$SLUG.webp" alt="..." >}}` shortcode after closing `+++`

## Output files (inside the post bundle directory)

```
content/posts/YYYY/MM/$SLUG/
├── index.md          ← updated with image field + shortcode
├── $SLUG.png         ← original PNG (preserve locally; CI can strip)
├── $SLUG.webp        ← optimized WebP (used in post body + og:image)
└── thumbs/
    └── $SLUG.webp    ← thumbnail used in post list
```

## Image style

The blog's house style is baked into the script:

> Flat vector illustration. Dark navy or charcoal background. Electric blue and warm amber as primary accent colors. Clean lines, minimal detail, no photorealism. No text, letters, words, or numbers anywhere in the image. Modern SaaS marketing illustration aesthetic, similar to Stripe or Linear. Landscape orientation, 16:9 ratio.

## Fallback (if script fails)

If the script fails (missing API keys, network error, or missing tools), fall back to manual:

1. Output an image generation prompt using the post's central visual metaphor and the house style above
2. Remind the user to:
   - Place the downloaded image in `content/posts/YYYY/MM/$SLUG/`
   - Run `./scripts/optimize-images.sh` from the repo root
   - Manually insert `{{< figure-float src="$SLUG.webp" alt="..." >}}` after closing `+++` in `index.md`
   - Manually add `image = "$SLUG.webp"` to the frontmatter

## optimize-images.sh

Handles all image optimization for the blog:
- PNG/JPG/GIF → creates optimized `.webp` alongside original (original preserved)
- WebP → resizes in-place if wider than 1600px
- Generates thumbnails in `thumbs/` subdirectories:
  - `content/posts/**` → 400px thumbs
  - `static/images/avatars/` → 300px thumbs
- Skips browser icons (favicon*, apple-touch-icon*, android-chrome*)

```bash
# Run from repo root
./scripts/optimize-images.sh
```

## check-image-resize.sh

Pre-commit hook that runs `make optimize-images` and blocks the commit if it produces unstaged changes. Used to enforce that all images are optimized before committing.

```bash
# Typically invoked as a pre-commit hook, not directly
./scripts/check-image-resize.sh
```
