#!/usr/bin/env python3
"""
Generate and insert a hero image for a Hugo blog post (leaf bundle layout).

Steps:
  1. Read the post and derive a visual concept via Claude API
  2. Generate the image with DALL-E 3
  3. Download the PNG to the post's bundle directory (alongside index.md)
  4. Optimize to WebP via ./scripts/optimize-images.sh
  5. Generate accurate alt text by reading the WebP via Claude vision
  6. Insert figure-float shortcode and image frontmatter field into the post

Requirements:
  pip install anthropic openai requests

Environment:
  Copy .env.example to .env and fill in your keys. The script loads .env
  automatically. Keys can also be set as shell environment variables.

  ANTHROPIC_API_KEY  — Anthropic API key (for concept + alt text)
  OPENAI_API_KEY     — OpenAI API key (for DALL-E 3 image generation)

Usage:
  python3 scripts/generate-post-image.py content/posts/2026/03/my-post/index.md
"""

import base64
import os
import re
import subprocess
import sys
from pathlib import Path

# Re-exec with the project's venv Python if not already using it.
# This means the script works correctly however it's invoked —
# directly, from Claude Code commands, or from a shell without activation.
_VENV_PYTHON = Path(__file__).parent.parent / ".venv" / "bin" / "python3"
if _VENV_PYTHON.exists() and Path(sys.executable).resolve() != _VENV_PYTHON.resolve():
    os.execv(str(_VENV_PYTHON), [str(_VENV_PYTHON)] + sys.argv)

try:
    import anthropic
    import openai
    import requests
except ImportError as e:
    print(f"Error: missing dependency — {e}")
    print(f"Run: {_VENV_PYTHON} -m pip install anthropic openai requests")
    sys.exit(1)

REPO_ROOT = Path(__file__).parent.parent


def load_dotenv() -> None:
    """Load key=value pairs from .env into os.environ (no external deps)."""
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:  # shell env takes precedence
            os.environ[key] = value

IMAGE_STYLE = (
    "Flat vector illustration. Dark navy or charcoal background. "
    "Electric blue and warm amber as primary accent colors. "
    "Clean lines, minimal detail, no photorealism. "
    "No text, letters, words, or numbers anywhere in the image. "
    "Modern SaaS marketing illustration aesthetic, similar to Stripe or Linear. "
    "Landscape orientation, 16:9 ratio."
)


def check_env() -> None:
    missing = [k for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY") if not os.environ.get(k)]
    if missing:
        for k in missing:
            print(f"Error: {k} environment variable is not set")
        sys.exit(1)


def read_post(post_path: Path) -> str:
    return post_path.read_text()


def already_has_image(content: str) -> bool:
    fm = re.search(r"^\+\+\+(.+?)\+\+\+", content, re.DOTALL)
    return bool(fm and 'image = ' in fm.group(1))


def generate_image_concept(post_content: str) -> str:
    """Ask Claude to derive a concrete visual concept from the post."""
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": (
                "You are art-directing a hero image for a tech blog post. "
                "Read the post and write a 2-3 sentence image description capturing "
                "the central visual metaphor. Be concrete and literal — describe "
                "specific objects, people, and actions to depict. "
                "Do NOT include style or color instructions. "
                "Return ONLY the image description, no preamble.\n\n"
                f"Post (excerpt):\n{post_content[:4000]}"
            ),
        }],
    )
    return response.content[0].text.strip()


def generate_image(concept: str) -> str:
    """Call DALL-E 3 and return the temporary image URL."""
    client = openai.OpenAI()
    full_prompt = f"{concept}\n\nStyle requirements: {IMAGE_STYLE}"
    response = client.images.generate(
        model="dall-e-3",
        prompt=full_prompt,
        size="1792x1024",
        quality="hd",
        n=1,
    )
    return response.data[0].url


def download_image(url: str, dest: Path) -> None:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    dest.write_bytes(resp.content)


def optimize_images() -> None:
    subprocess.run(
        ["./scripts/optimize-images.sh"],
        cwd=REPO_ROOT,
        check=True,
    )


def generate_alt_text(webp_path: Path) -> str:
    """Use Claude vision to describe exactly what is depicted in the image."""
    client = anthropic.Anthropic()
    image_data = base64.standard_b64encode(webp_path.read_bytes()).decode()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/webp",
                        "data": image_data,
                    },
                },
                {
                    "type": "text",
                    "text": (
                        "Write alt text for this image describing exactly what is "
                        "literally depicted — objects, people, actions, colors, layout. "
                        "Aim for 10-15 words. No preamble, just the alt text."
                    ),
                },
            ],
        }],
    )
    return response.content[0].text.strip()


def insert_into_post(post_path: Path, slug: str, alt_text: str) -> None:
    """Add image frontmatter field and figure-float shortcode to the post."""
    content = post_path.read_text()

    # Bundle-relative reference: just the filename, no path prefix
    webp_ref = f"{slug}.webp"
    # Escape any double quotes in alt text for Hugo shortcode safety
    safe_alt = alt_text.replace('"', "'")
    shortcode = f'{{{{< figure-float src="{webp_ref}" alt="{safe_alt}" >}}}}'
    image_field = f'image = "{webp_ref}"'

    # Insert image field into frontmatter after the categories line
    content = re.sub(
        r"(categories = \[.*?\])",
        rf"\1\n{image_field}",
        content,
        count=1,
    )

    # Split on +++ delimiters to insert shortcode after closing +++
    # TOML frontmatter: +++\n<fields>\n+++\n<body>
    parts = content.split("+++\n", 2)
    if len(parts) != 3:
        print("Warning: could not locate frontmatter delimiters; skipping shortcode insertion.")
        post_path.write_text(content)
        return

    body = parts[2]  # everything after the closing +++
    # Insert shortcode then preserve whatever whitespace preceded the body
    updated_body = f"\n{shortcode}\n{body.lstrip(chr(10))}\n"
    content = f"+++\n{parts[1]}+++\n{updated_body}"

    post_path.write_text(content)


def main() -> None:
    load_dotenv()

    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path-to-post.md>")
        sys.exit(1)

    post_path = Path(sys.argv[1]).resolve()
    if not post_path.exists():
        print(f"Error: {post_path} does not exist")
        sys.exit(1)

    check_env()

    # For leaf bundles (index.md), derive slug from parent directory name.
    # For legacy flat posts (slug.md), use the file stem.
    if post_path.name == "index.md":
        slug = post_path.parent.name
        bundle_dir = post_path.parent
    else:
        slug = post_path.stem
        bundle_dir = post_path.parent

    content = read_post(post_path)

    if already_has_image(content):
        print("Post already has an image field — remove it to regenerate.")
        sys.exit(0)

    png_dest = bundle_dir / f"{slug}.png"
    webp_dest = bundle_dir / f"{slug}.webp"

    print(f"Generating hero image for: {post_path.name}")
    print()

    print("1/5  Deriving visual concept from post content...")
    concept = generate_image_concept(content)
    print(f"     {concept[:120]}{'...' if len(concept) > 120 else ''}")
    print()

    print("2/5  Generating image with DALL-E 3 (this takes ~15s)...")
    image_url = generate_image(concept)
    print()

    print(f"3/5  Downloading PNG to {png_dest.relative_to(REPO_ROOT)}...")
    download_image(image_url, png_dest)
    print()

    print("4/5  Optimizing to WebP via optimize-images.sh...")
    optimize_images()
    print()

    print("5/5  Generating alt text and inserting into post...")
    alt_text = generate_alt_text(webp_dest)
    print(f"     Alt: {alt_text}")
    insert_into_post(post_path, slug, alt_text)
    print()

    print(f"Done. Image added to {post_path}")
    print(f"  PNG:  {png_dest.relative_to(REPO_ROOT)}")
    print(f"  WebP: {webp_dest.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
