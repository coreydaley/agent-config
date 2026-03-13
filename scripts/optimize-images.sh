#!/usr/bin/env bash
# Renamed from: resize-images.sh
#
# For each image in static/images:
#   PNG/JPG/GIF  → creates an optimized .webp alongside the original (original
#                  is NOT deleted). If the .webp already exists it is skipped,
#                  so the script is safe to re-run. Resize to ≤1600px is baked
#                  into the conversion step rather than modifying the source.
#                  1600px covers the ~700px content column at 2x DPI (retina).
#   WebP         → resized in-place if wider than 1600px (it is already the
#                  target format, so there is no separate "original" to keep).
#   Browser icons (favicon*, apple-touch-icon*, android-chrome*) → skipped.
#
# Thumbnails (created only when the source was just processed, or when missing):
#   static/images/posts/   → thumbs/ at 400px  (covers 180px display at 2x DPR)
#   static/images/avatars/ → thumbs/ at 300px  (covers 150px desktop display at 2x DPR)
#
# Requires one of the following for WebP conversion:
#   macOS:   brew install webp   (cwebp, preferred)
#            brew install imagemagick  (fallback)
#   Ubuntu:  sudo apt-get install webp
#            sudo apt-get install imagemagick  (fallback)

set -e

# Configuration
MAX_WIDTH=1600
WEBP_QUALITY=82      # Full-size quality; imperceptibly different from 85, ~10-15% smaller
THUMB_QUALITY=75     # Thumbnail quality; artifacts invisible at small display sizes
IMAGE_DIR="static/images"
CONTENT_POSTS_DIR="content/posts"  # leaf bundle post directories (YYYY/MM/slug/)
THUMB_WIDTH_POSTS=400    # 180px display × 2x DPR, rounded up
THUMB_WIDTH_AVATARS=300  # 150px display (desktop default) × 2x DPR
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# --- Tool detection ---

# Resize tool
USE_TOOL=""
MAGICK_CMD=""
IDENTIFY_CMD=""
if command -v magick &> /dev/null; then
    USE_TOOL="magick"
    MAGICK_CMD="magick"
    IDENTIFY_CMD="magick identify"
elif command -v convert &> /dev/null; then
    USE_TOOL="imagemagick"
    MAGICK_CMD="convert"
    IDENTIFY_CMD="identify"
elif command -v sips &> /dev/null; then
    USE_TOOL="sips"
else
    echo -e "${RED}Error: No image processing tool found.${NC}"
    echo ""
    echo "Please install one of the following:"
    echo "  macOS:   brew install imagemagick  (or use built-in sips)"
    echo "  Ubuntu:  sudo apt-get install imagemagick"
    echo "  Fedora:  sudo dnf install imagemagick"
    exit 1
fi

# WebP conversion tool (separate from resize tool — sips cannot output WebP)
WEBP_TOOL=""
if command -v cwebp &> /dev/null; then
    WEBP_TOOL="cwebp"
elif [ "$USE_TOOL" = "magick" ]; then
    WEBP_TOOL="magick"
elif [ "$USE_TOOL" = "imagemagick" ]; then
    WEBP_TOOL="imagemagick"
fi

# --- Setup ---

cd "$PROJECT_ROOT"

if [ ! -d "$IMAGE_DIR" ]; then
    echo -e "${RED}Error: Directory $IMAGE_DIR does not exist.${NC}"
    exit 1
fi

echo -e "${BLUE}==================================${NC}"
echo -e "${BLUE}Image Resize & WebP Conversion${NC}"
echo -e "${BLUE}==================================${NC}"
echo ""
echo -e "Resize tool:     ${GREEN}${USE_TOOL}${NC}"
if [ -n "$WEBP_TOOL" ]; then
    echo -e "WebP tool:       ${GREEN}${WEBP_TOOL}${NC}"
else
    echo -e "WebP tool:       ${YELLOW}none${NC}"
fi
echo -e "Maximum width:   ${GREEN}${MAX_WIDTH}px${NC}"
echo -e "WebP quality:    ${GREEN}${WEBP_QUALITY}${NC} (thumbs: ${THUMB_QUALITY})"
echo -e "Image directory: ${GREEN}${IMAGE_DIR}${NC}"
echo -e "Content bundles: ${GREEN}${CONTENT_POSTS_DIR}${NC}"
echo -e "Post thumbs:     ${GREEN}${THUMB_WIDTH_POSTS}px${NC} (in thumbs/ subdir)"
echo -e "Avatar thumbs:   ${GREEN}${THUMB_WIDTH_AVATARS}px${NC} (in avatars/thumbs/) — covers 150px display @ 2x DPR"
echo ""

# --- Counters ---
total_images=0
resized_images=0
skipped_images=0
converted_images=0
thumb_images=0
failed_images=0

# --- Helpers ---

# Returns 0 (true) if the file is a favicon/manifest icon that must not be converted to WebP
is_reserved_icon() {
    local name
    name=$(basename "$1")
    [[ "$name" == favicon* ]] || [[ "$name" == apple-touch-icon* ]] || [[ "$name" == android-chrome* ]]
}

# Creates an optimized WebP from a PNG/JPG/GIF. The original is NOT deleted.
# Optionally resizes to max_width during conversion (0 = no resize).
# Usage: convert_to_webp <input_file> [max_width]
# Returns 0 on success, 1 on failure.
convert_to_webp() {
    local input="$1"
    local max_width="${2:-0}"
    local output="${input%.*}.webp"
    local success=1

    if [ "$WEBP_TOOL" = "cwebp" ]; then
        # -m 6: max compression effort (no quality loss, just slower)
        # -metadata none: strip EXIF/color profile (not needed on the web)
        if [ "$max_width" -gt 0 ]; then
            cwebp -q "$WEBP_QUALITY" -m 6 -metadata none -resize "$max_width" 0 "$input" -o "$output" 2>/dev/null && success=0
        else
            cwebp -q "$WEBP_QUALITY" -m 6 -metadata none "$input" -o "$output" 2>/dev/null && success=0
        fi
    elif [ "$WEBP_TOOL" = "magick" ]; then
        # webp:method=6: max compression effort; -strip: remove metadata
        if [ "$max_width" -gt 0 ]; then
            magick "$input" -resize "${max_width}x>" -quality "$WEBP_QUALITY" -strip -define webp:method=6 "$output" 2>/dev/null && success=0
        else
            magick "$input" -quality "$WEBP_QUALITY" -strip -define webp:method=6 "$output" 2>/dev/null && success=0
        fi
    elif [ "$WEBP_TOOL" = "imagemagick" ]; then
        if [ "$max_width" -gt 0 ]; then
            convert "$input" -resize "${max_width}x>" -quality "$WEBP_QUALITY" -strip -define webp:method=6 "$output" 2>/dev/null && success=0
        else
            convert "$input" -quality "$WEBP_QUALITY" -strip -define webp:method=6 "$output" 2>/dev/null && success=0
        fi
    fi

    if [ $success -eq 0 ] && [ -f "$output" ]; then
        return 0
    else
        [ -f "$output" ] && rm -f "$output"  # clean up partial output
        return 1
    fi
}

# Generates a resized copy of a WebP image in a thumbs/ subdirectory.
# Usage: generate_thumb <source_file> <max_width>
# Returns 0 on success, 1 on failure.
generate_thumb() {
    local source="$1"
    local thumb_width="$2"
    local dir
    dir=$(dirname "$source")
    local basename
    basename=$(basename "$source")
    local thumb_dir="${dir}/thumbs"
    local thumb_file="${thumb_dir}/${basename}"

    mkdir -p "$thumb_dir"

    # Read source width
    local img_width
    if [ "$USE_TOOL" = "sips" ]; then
        img_width=$(sips -g pixelWidth "$source" 2>/dev/null | grep pixelWidth | awk '{print $2}')
    else
        img_width=$($IDENTIFY_CMD -format "%w" "$source" 2>/dev/null || echo "0")
    fi

    if [ -z "$img_width" ] || [ "$img_width" = "0" ]; then
        echo -e "   ${RED}✗${NC} Thumb failed (unreadable): ${basename}"
        return 1
    fi

    # Copy source into thumbs/ then resize the copy
    cp "$source" "$thumb_file"

    if [ "$img_width" -le "$thumb_width" ]; then
        echo -e "   ${CYAN}↳${NC} Thumb (already ≤${thumb_width}px, copied): thumbs/${basename}"
        return 0
    fi

    local resize_success=0
    if [ "$USE_TOOL" = "sips" ]; then
        sips -Z "$thumb_width" "$thumb_file" &>/dev/null
        resize_success=$?
    elif [ "$USE_TOOL" = "magick" ]; then
        magick "$thumb_file" -resize "${thumb_width}x>" -quality "$THUMB_QUALITY" -strip -define webp:method=6 "$thumb_file" 2>/dev/null
        resize_success=$?
    else
        convert "$thumb_file" -resize "${thumb_width}x>" -quality "$THUMB_QUALITY" -strip -define webp:method=6 "$thumb_file" 2>/dev/null
        resize_success=$?
    fi

    if [ $resize_success -eq 0 ]; then
        echo -e "   ${CYAN}↳${NC} Thumb: thumbs/${basename} (max ${thumb_width}px)"
        return 0
    else
        rm -f "$thumb_file"
        echo -e "   ${YELLOW}⚠${NC} Thumb generation failed: ${basename}"
        return 1
    fi
}

# --- Main loop ---

while IFS= read -r -d '' image_file; do
    total_images=$((total_images + 1))
    relative_path="${image_file#$PROJECT_ROOT/}"
    ext_lower=$(echo "${image_file##*.}" | tr '[:upper:]' '[:lower:]')
    file_modified=0
    processed_file="$image_file"

    if [ "$ext_lower" = "webp" ]; then
        # --- Already WebP: resize in-place if oversized ---
        # WebP is already the target format; there is no separate original to keep.
        if [ "$USE_TOOL" = "sips" ]; then
            width=$(sips -g pixelWidth "$image_file" 2>/dev/null | grep pixelWidth | awk '{print $2}')
        else
            width=$($IDENTIFY_CMD -format "%w" "$image_file" 2>/dev/null || echo "0")
        fi

        if [ -z "$width" ] || [ "$width" = "0" ]; then
            echo -e "${RED}✗${NC} Failed to read: $relative_path"
            failed_images=$((failed_images + 1))
            continue
        fi

        if [ "$width" -gt "$MAX_WIDTH" ]; then
            echo -e "${YELLOW}↻${NC} Resizing WebP: $relative_path (${width}px → ${MAX_WIDTH}px)"
            resize_success=0
            if [ "$USE_TOOL" = "sips" ]; then
                sips -Z "$MAX_WIDTH" "$image_file" &>/dev/null
                resize_success=$?
            elif [ "$USE_TOOL" = "magick" ]; then
                magick "$image_file" -resize "${MAX_WIDTH}x>" -quality "$WEBP_QUALITY" -strip -define webp:method=6 "$image_file" 2>/dev/null
                resize_success=$?
            else
                convert "$image_file" -resize "${MAX_WIDTH}x>" -quality "$WEBP_QUALITY" -strip -define webp:method=6 "$image_file" 2>/dev/null
                resize_success=$?
            fi
            if [ $resize_success -eq 0 ]; then
                new_width=$($IDENTIFY_CMD -format "%w" "$image_file" 2>/dev/null || echo "?")
                echo -e "   ${GREEN}✓${NC} Resized to ${new_width}px"
                resized_images=$((resized_images + 1))
                file_modified=1
            else
                echo -e "   ${RED}✗${NC} Resize failed"
                failed_images=$((failed_images + 1))
                continue
            fi
        else
            echo -e "${GREEN}✓${NC} Already optimal: $relative_path (${width}px)"
            skipped_images=$((skipped_images + 1))
        fi

    elif is_reserved_icon "$image_file"; then
        # --- Browser icons (favicon, apple-touch-icon, android-chrome): never convert ---
        echo -e "${GREEN}✓${NC} Reserved icon (skipped): $relative_path"
        skipped_images=$((skipped_images + 1))
        continue

    else
        # --- PNG/JPG/GIF: create WebP alongside original; original is preserved ---
        webp_path="${image_file%.*}.webp"

        if [ -f "$webp_path" ]; then
            # WebP already exists — nothing to do
            echo -e "${GREEN}✓${NC} WebP exists: $relative_path"
            skipped_images=$((skipped_images + 1))
            processed_file="$webp_path"
        elif [ -n "$WEBP_TOOL" ]; then
            # Read source width to determine if a resize is needed during conversion
            if [ "$USE_TOOL" = "sips" ]; then
                width=$(sips -g pixelWidth "$image_file" 2>/dev/null | grep pixelWidth | awk '{print $2}')
            else
                width=$($IDENTIFY_CMD -format "%w" "$image_file" 2>/dev/null || echo "0")
            fi

            if [ -z "$width" ] || [ "$width" = "0" ]; then
                echo -e "${RED}✗${NC} Failed to read: $relative_path"
                failed_images=$((failed_images + 1))
                continue
            fi

            resize_width=0
            [ "$width" -gt "$MAX_WIDTH" ] && resize_width="$MAX_WIDTH"

            if [ "$resize_width" -gt 0 ]; then
                echo -e "${YELLOW}⇢${NC} Converting + resizing: $relative_path (${width}px → ${MAX_WIDTH}px → WebP)"
            else
                echo -e "${YELLOW}⇢${NC} Converting: $relative_path → WebP"
            fi

            if convert_to_webp "$image_file" "$resize_width"; then
                echo -e "   ${GREEN}✓${NC} Created: ${relative_path%.*}.webp  (original preserved)"
                converted_images=$((converted_images + 1))
                file_modified=1
                processed_file="$webp_path"
            else
                echo -e "   ${RED}✗${NC} WebP conversion failed — original unchanged"
                failed_images=$((failed_images + 1))
                continue
            fi
        else
            echo -e "${YELLOW}⚠${NC} No WebP tool available — skipping: $relative_path"
            skipped_images=$((skipped_images + 1))
            continue
        fi
    fi

    # --- Generate thumbnail in thumbs/ subdirectory ---
    # Only when the source was modified this run, or when the thumbnail is missing.
    # This keeps the hook idempotent: unchanged images don't touch their thumbs.
    dir_relative=$(dirname "${processed_file#$PROJECT_ROOT/}")
    thumb_width=0
    if [ "$dir_relative" = "static/images/posts" ]; then
        thumb_width="$THUMB_WIDTH_POSTS"
    elif [ "$dir_relative" = "static/images/avatars" ]; then
        thumb_width="$THUMB_WIDTH_AVATARS"
    elif [[ "$dir_relative" == content/posts/* ]]; then
        # Leaf bundle post directory — generate post-sized thumbnail
        thumb_width="$THUMB_WIDTH_POSTS"
    fi

    if [ "$thumb_width" -gt 0 ]; then
        thumb_file="$(dirname "$processed_file")/thumbs/$(basename "$processed_file")"
        if [ "$file_modified" -eq 1 ] || [ ! -f "$thumb_file" ]; then
            if generate_thumb "$processed_file" "$thumb_width"; then
                thumb_images=$((thumb_images + 1))
            fi
        fi
    fi

done < <(find "$IMAGE_DIR" "$CONTENT_POSTS_DIR" -type f -not -path "*/thumbs/*" \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.gif" -o -iname "*.webp" \) -print0 2>/dev/null)

# --- Summary ---
echo ""
echo -e "${BLUE}==================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}==================================${NC}"
echo -e "Total images:         ${total_images}"
echo -e "Resized:              ${GREEN}${resized_images}${NC}"
echo -e "Already optimal:      ${GREEN}${skipped_images}${NC}"
echo -e "Converted to WebP:    ${GREEN}${converted_images}${NC}"
echo -e "Thumbnails generated: ${GREEN}${thumb_images}${NC}"
if [ "$failed_images" -gt 0 ]; then
    echo -e "Failed:               ${RED}${failed_images}${NC}"
fi
echo ""

if [ -z "$WEBP_TOOL" ]; then
    echo -e "${YELLOW}⚠ WebP conversion skipped — no conversion tool found.${NC}"
    echo -e "  To enable WebP conversion, install one of the following:"
    echo -e "    macOS:   ${CYAN}brew install imagemagick${NC}  or  ${CYAN}brew install webp${NC}"
    echo -e "    Ubuntu:  ${CYAN}sudo apt-get install imagemagick${NC}  or  ${CYAN}sudo apt-get install webp${NC}"
    echo ""
fi

if [ "$converted_images" -gt 0 ]; then
    echo -e "${YELLOW}Next steps after WebP conversion:${NC}"
    echo -e "  1. Update image references in post frontmatter from .png/.jpg to .webp"
    echo -e "  2. Update hugo.toml avatar/coverImage paths if converted"
    echo -e "  Original files are preserved — delete them manually once references are updated."
    echo ""
fi

if [ "$resized_images" -gt 0 ] || [ "$converted_images" -gt 0 ] || [ "$thumb_images" -gt 0 ]; then
    echo -e "${GREEN}✓ Image processing completed successfully!${NC}"
else
    echo -e "${BLUE}All images are already optimized.${NC}"
fi
