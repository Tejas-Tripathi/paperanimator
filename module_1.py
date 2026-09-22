from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import math
import numpy as np
import random


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ASSETS_DIR = BASE_DIR / "assets"

PAPER_DIR = ASSETS_DIR / "paper_textures"

PARAGRAPH_DIR = ASSETS_DIR / "paragraphs"

FONT_DIR = ASSETS_DIR / "fonts"

OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# BLUR CONFIGURATION
# ============================================================

# Set to False to compare output without blur effect
BLUR_ENABLED = True

# Maximum Gaussian blur radius applied to the outer region
BLUR_RADIUS = 12

# Pixel radius around the target text that stays 100% sharp
FOCUS_RADIUS = 60

# Pixel distance over which the image transitions from
# sharp to maximum blur (feathering zone)
FEATHER_RADIUS = 250


# ============================================================
# HIGHLIGHT CONFIGURATION
# ============================================================

# Set to False to disable highlight for comparison
HIGHLIGHT_ENABLED = True

# Hex color of the highlighter stroke
HIGHLIGHT_COLOR = "#FFF200"

# Opacity of the highlight (0 = invisible, 255 = fully opaque)
HIGHLIGHT_OPACITY = 180

# Extra space added around the target text bounding box
HIGHLIGHT_PADDING_X = 10
HIGHLIGHT_PADDING_Y = 13

# Maximum random wobble in pixels on each edge of the highlight
# (0 = perfect rectangle, higher = more organic marker look)
HIGHLIGHT_WOBBLE = 3

# Vertical offset to shift the highlight downward relative to
# the target text bounding box (text position is NOT affected).
# 0 = original position, 4 = recommended, 6 = more down
HIGHLIGHT_OFFSET_Y = 4


# ============================================================
# ASPECT RATIOS
# ============================================================

ASPECT_RATIOS = {
    "1": {
        "name": "9:16",
        "width": 1080,
        "height": 1920,
    },

    "2": {
        "name": "16:9",
        "width": 1920,
        "height": 1080,
    },

    "3": {
        "name": "1:1",
        "width": 1080,
        "height": 1080,
    },

    "4": {
        "name": "4:5",
        "width": 1080,
        "height": 1350,
    },
}


# ============================================================
# FILE DISCOVERY
# ============================================================

def get_paper_textures():
    """
    Return all available paper texture files.
    """

    supported_extensions = {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    }

    return sorted(
        [
            file
            for file in PAPER_DIR.iterdir()
            if (
                file.is_file()
                and file.suffix.lower()
                in supported_extensions
            )
        ]
    )


def get_paragraphs():
    """
    Return all paragraph text files.
    """

    return sorted(
        [
            file
            for file in PARAGRAPH_DIR.iterdir()
            if (
                file.is_file()
                and file.suffix.lower() == ".txt"
            )
        ]
    )


def get_fonts():
    """
    Return all TTF/OTF font files.
    """

    supported_extensions = {
        ".ttf",
        ".otf",
    }

    return sorted(
        [
            file
            for file in FONT_DIR.rglob("*")
            if (
                file.is_file()
                and file.suffix.lower()
                in supported_extensions
            )
        ]
    )


# ============================================================
# SELECTION HELPERS
# ============================================================

def select_from_list(items, title):
    """
    Display a numbered list and return selected item.
    """

    print()
    print("=" * 60)
    print(title)
    print("=" * 60)

    for index, item in enumerate(items, start=1):

        print(
            f"{index}. {item.name}"
        )

    print()

    while True:

        choice = input(
            "Select number: "
        ).strip()

        try:

            choice = int(choice)

        except ValueError:

            print(
                "Please enter a valid number."
            )

            continue

        if 1 <= choice <= len(items):

            return items[choice - 1]

        print(
            "Invalid selection."
        )


def select_aspect_ratio():

    print()
    print("=" * 60)
    print("SELECT ASPECT RATIO")
    print("=" * 60)

    for key, value in ASPECT_RATIOS.items():

        print(
            f"{key}. {value['name']} "
            f"({value['width']}x{value['height']})"
        )

    print()

    while True:

        choice = input(
            "Select number: "
        ).strip()

        if choice in ASPECT_RATIOS:

            return ASPECT_RATIOS[choice]

        print(
            "Invalid selection."
        )


# ============================================================
# TEXT WRAPPING
# ============================================================

def wrap_text(
    draw,
    text,
    font,
    max_width,
):
    """
    Wrap paragraph according to actual rendered
    pixel width.
    """

    words = text.split()

    lines = []

    current_line = ""

    for word in words:

        if not current_line:

            test_line = word

        else:

            test_line = (
                current_line
                + " "
                + word
            )

        bbox = draw.textbbox(
            (0, 0),
            test_line,
            font=font,
        )

        line_width = (
            bbox[2] - bbox[0]
        )

        if line_width <= max_width:

            current_line = test_line

        else:

            if current_line:

                lines.append(
                    current_line
                )

            current_line = word

    if current_line:

        lines.append(
            current_line
        )

    return lines


# ============================================================
# TARGET INSERTION
# ============================================================

def insert_target_into_paragraph(
    paragraph_text,
    target_text,
):
    """
    Insert target_text into the middle of paragraph_text
    at word-level so the final rendered paragraph
    contains the target as a natural part of the text.

    Returns the modified paragraph string.
    """

    words = paragraph_text.split()

    insert_index = len(words) // 2

    words.insert(insert_index, target_text)

    return " ".join(words)


# ============================================================
# PARAGRAPH LAYOUT
# ============================================================

def draw_paragraph(
    image,
    paragraph_text,
    font_path,
    target_text=None,
):
    """
    Draw the complete paragraph over the full page.

    - Paragraph fills the page (small safe margins only).
    - Left-aligned text.
    - Font size auto-calculated so text occupies 90-94%
      of vertical space.
    - Target text is already embedded in paragraph_text,
      so no separate target rendering is needed.

    Returns:
        (target_bbox, paragraph_font):
            target_bbox  : (x1, y1, x2, y2) pixel bounding box
                           of the target_text in the rendered
                           paragraph. None if not found.
            paragraph_font: the ImageFont object used, so
                           callers can re-draw the target word
                           on a separate layer (e.g. highlight).
    """

    draw = ImageDraw.Draw(image)

    width, height = image.size

    # --------------------------------------------------------
    # Safe margins  (small — only 3% each side)
    # --------------------------------------------------------

    horizontal_margin = int(width * 0.03)

    vertical_margin = int(height * 0.03)

    paragraph_width = width - horizontal_margin * 2

    # --------------------------------------------------------
    # Available vertical space for the paragraph block
    # --------------------------------------------------------

    available_height = height - vertical_margin * 2

    # Target: paragraph fills 90-94% of available height
    target_fill_min = 0.90
    target_fill_max = 0.94

    # --------------------------------------------------------
    # Dynamic font size: binary-search for best fit
    # --------------------------------------------------------

    low_size = int(width * 0.015)
    high_size = int(width * 0.060)
    best_size = int(width * 0.028)   # reasonable initial guess

    for _ in range(20):   # max 20 iterations — always converges

        mid_size = (low_size + high_size) // 2

        if mid_size == best_size:
            break

        best_size = mid_size

        font = ImageFont.truetype(
            str(font_path),
            best_size,
        )

        line_height = int(best_size * 1.55)

        lines = wrap_text(
            draw=draw,
            text=paragraph_text,
            font=font,
            max_width=paragraph_width,
        )

        paragraph_height = len(lines) * line_height

        fill_ratio = paragraph_height / available_height

        if fill_ratio < target_fill_min:
            # Too small — increase font
            low_size = mid_size + 1
        elif fill_ratio > target_fill_max:
            # Too large — decrease font
            high_size = mid_size - 1
        else:
            # Within target band — done
            break

    # Final font + lines with best_size
    paragraph_font = ImageFont.truetype(
        str(font_path),
        best_size,
    )

    line_height = int(best_size * 1.55)

    lines = wrap_text(
        draw=draw,
        text=paragraph_text,
        font=paragraph_font,
        max_width=paragraph_width,
    )

    # --------------------------------------------------------
    # Start from top safe margin
    # --------------------------------------------------------

    start_y = vertical_margin

    # --------------------------------------------------------
    # Draw lines — left aligned
    # Simultaneously track the rendered bounding box of
    # the target_text word(s) inside the paragraph.
    # --------------------------------------------------------

    target_bbox = None

    for line_index, line in enumerate(lines):

        x = horizontal_margin

        y = (
            start_y
            + line_index
            * line_height
        )

        draw.text(
            (x, y),
            line,
            font=paragraph_font,
            fill=(35, 35, 35),
        )

        # ------------------------------------------------
        # Locate target text within this rendered line.
        # We find the pixel offset of the target by
        # measuring the width of the text before it.
        # ------------------------------------------------

        if target_text and target_bbox is None:

            # Check if the target word(s) appear in line
            target_pos = line.find(target_text)

            if target_pos != -1:

                # Width of text before the target word
                prefix = line[:target_pos]

                if prefix:

                    prefix_bbox = draw.textbbox(
                        (0, 0),
                        prefix,
                        font=paragraph_font,
                    )

                    prefix_width = (
                        prefix_bbox[2]
                        - prefix_bbox[0]
                    )

                else:

                    prefix_width = 0

                # Width of target word itself
                t_bbox = draw.textbbox(
                    (0, 0),
                    target_text,
                    font=paragraph_font,
                )

                t_w = t_bbox[2] - t_bbox[0]
                t_h = t_bbox[3] - t_bbox[1]

                # Absolute pixel coordinates on the image
                tx1 = x + prefix_width
                ty1 = y
                tx2 = tx1 + t_w
                ty2 = ty1 + t_h

                target_bbox = (tx1, ty1, tx2, ty2)

    return target_bbox, paragraph_font



# ============================================================
# HIGHLIGHT
# ============================================================

def _hex_to_rgb(hex_color):
    """
    Convert a CSS hex color string (e.g. '#FFF200') to an
    (R, G, B) integer tuple.
    """

    hex_color = hex_color.lstrip("#")

    return tuple(
        int(hex_color[i : i + 2], 16)
        for i in (0, 2, 4)
    )


def draw_target_highlight(
    image,
    target_bbox,
    color=HIGHLIGHT_COLOR,
    opacity=HIGHLIGHT_OPACITY,
    padding_x=HIGHLIGHT_PADDING_X,
    padding_y=HIGHLIGHT_PADDING_Y,
    wobble=HIGHLIGHT_WOBBLE,
    offset_y=HIGHLIGHT_OFFSET_Y,
):
    """
    Draw a semi-transparent marker-stroke highlight behind
    the target text.

    Uses an RGBA overlay composited onto the RGB image so
    the paper texture shows faintly through the highlight
    (just like a real translucent marker).

    The four corners of the highlight rectangle are given
    tiny random offsets (controlled by `wobble`) to avoid
    a mechanical perfect-rectangle look.

    Args:
        image      : PIL Image (RGB) to draw on.
        target_bbox: (x1, y1, x2, y2) bounding box of
                     the target text as returned by
                     draw_paragraph().
        color      : Hex highlight color, e.g. '#FFF200'.
        opacity    : Alpha value 0-255 (180 ≈ 70% opaque).
        padding_x  : Extra horizontal space around text (px).
        padding_y  : Extra vertical space around text (px).
        wobble     : Max random displacement per corner (px).
        offset_y   : Pixels to shift the highlight downward
                     without moving the text (default 4).
    """

    x1, y1, x2, y2 = target_bbox

    # --------------------------------------------------------
    # Expand bbox by padding and apply vertical offset
    # (offset_y > 0 shifts the highlight downward;
    #  the target text position is completely unaffected)
    # --------------------------------------------------------

    hx1 = x1 - padding_x
    hy1 = y1 - padding_y + offset_y
    hx2 = x2 + padding_x
    hy2 = y2 + padding_y + offset_y

    # --------------------------------------------------------
    # Parse hex color → RGBA
    # --------------------------------------------------------

    r, g, b = _hex_to_rgb(color)

    highlight_rgba = (r, g, b, opacity)

    # --------------------------------------------------------
    # Build an RGBA overlay the same size as the image.
    # Drawing on a transparent layer then compositing
    # preserves the paper texture underneath.
    # --------------------------------------------------------

    overlay = Image.new(
        "RGBA",
        image.size,
        (0, 0, 0, 0),
    )

    overlay_draw = ImageDraw.Draw(overlay)

    # --------------------------------------------------------
    # Build slightly irregular polygon (marker-stroke look).
    #
    # Each of the four corners is nudged by a small random
    # amount.  The top and bottom edges are each divided into
    # three segments with a mid-point wobble so the long
    # horizontal edges look hand-drawn rather than perfectly
    # straight.
    # --------------------------------------------------------

    rng = random.Random(42)   # fixed seed → deterministic

    def jitter(base, amount):
        """Return base ± random amount."""
        return base + rng.uniform(-amount, amount)

    # Mid-x for top / bottom edge wobble
    mid_x = (hx1 + hx2) / 2.0

    # Top edge:   TL corner → mid-top → TR corner
    # Bottom edge: BL corner → mid-bottom → BR corner
    # Left / Right edges connect the corners directly.

    polygon = [
        # Top-left
        (jitter(hx1, wobble), jitter(hy1, wobble)),
        # Mid-top (wobble only vertically)
        (mid_x,               jitter(hy1, wobble)),
        # Top-right
        (jitter(hx2, wobble), jitter(hy1, wobble)),
        # Bottom-right
        (jitter(hx2, wobble), jitter(hy2, wobble)),
        # Mid-bottom
        (mid_x,               jitter(hy2, wobble)),
        # Bottom-left
        (jitter(hx1, wobble), jitter(hy2, wobble)),
    ]

    overlay_draw.polygon(
        polygon,
        fill=highlight_rgba,
    )

    # --------------------------------------------------------
    # Composite overlay onto the RGB image
    # --------------------------------------------------------

    # Convert base image to RGBA temporarily for compositing
    base_rgba = image.convert("RGBA")

    merged = Image.alpha_composite(base_rgba, overlay)

    # Convert back to RGB (matches the rest of the pipeline)
    result_rgb = merged.convert("RGB")

    # Copy result pixels back into the original image object
    # (so callers that hold a reference to `image` see the
    # update — same pattern used throughout the module).
    image.paste(result_rgb)


# ============================================================
# RADIAL BLUR
# ============================================================

def apply_radial_blur(
    image,
    target_bbox,
    blur_radius=BLUR_RADIUS,
    focus_radius=FOCUS_RADIUS,
    feather_radius=FEATHER_RADIUS,
):
    """
    Apply a smooth radial depth-of-field blur effect.

    The region around target_bbox stays completely sharp.
    Everything outside transitions smoothly to the
    maximum Gaussian blur using a smoothstep function.
    There is no visible hard circle or ring.

    Args:
        image       : PIL Image (RGB).
        target_bbox : (x1, y1, x2, y2) pixel bounding box
                      of the target text on the image.
        blur_radius : Gaussian blur radius for the outer region.
        focus_radius: Radius around target center that is
                      100% sharp (pixels).
        feather_radius: Width of the smooth transition zone
                      between sharp and fully blurred (pixels).

    Returns:
        PIL Image with radial blur applied.
    """

    width, height = image.size

    # --------------------------------------------------------
    # Radial blur center = center of target bounding box
    # --------------------------------------------------------

    cx = (target_bbox[0] + target_bbox[2]) / 2.0
    cy = (target_bbox[1] + target_bbox[3]) / 2.0

    # --------------------------------------------------------
    # Create single blurred version of the full image
    # --------------------------------------------------------

    blurred_image = image.filter(
        ImageFilter.GaussianBlur(blur_radius)
    )

    # --------------------------------------------------------
    # Build radial mask as a float32 numpy array.
    # Value 0.0 = take from sharp original
    # Value 1.0 = take from blurred image
    # --------------------------------------------------------

    # Pixel coordinate grids (vectorised — no Python loops)
    xs = np.arange(width,  dtype=np.float32)
    ys = np.arange(height, dtype=np.float32)

    # Shape: (height, width)
    grid_x, grid_y = np.meshgrid(xs, ys)

    # Euclidean distance from target center for every pixel
    dist = np.sqrt(
        (grid_x - cx) ** 2
        + (grid_y - cy) ** 2
    )

    # Normalised blend factor using smoothstep
    #   t = 0  → completely sharp  (dist <= focus_radius)
    #   t = 1  → fully blurred     (dist >= focus_radius + feather_radius)

    t = (
        dist - focus_radius
    ) / feather_radius

    t = np.clip(t, 0.0, 1.0)

    # Smoothstep: t² × (3 − 2t)  — produces an S-curve
    smooth_t = t * t * (3.0 - 2.0 * t)

    # Convert to uint8 mask  (0 = sharp, 255 = blurred)
    mask_array = (smooth_t * 255.0).astype(np.uint8)

    # PIL grayscale mask image
    mask = Image.fromarray(
        mask_array,
        mode="L",
    )

    # --------------------------------------------------------
    # Composite: where mask=0  → sharp, mask=255 → blurred
    # Image.composite(image1, image2, mask):
    #   pixel = image1 × (mask/255) + image2 × (1 - mask/255)
    # So we pass blurred as image1 and sharp as image2.
    # --------------------------------------------------------

    result = Image.composite(
        blurred_image,
        image,
        mask,
    )

    return result


# ============================================================
# CREATE PAGE
# ============================================================

def create_page(
    paper_path,
    paragraph_path,
    font_path,
    target_text,
    aspect_ratio,
):
    """
    Create one static page composition.
    """

    width = aspect_ratio["width"]

    height = aspect_ratio["height"]

    # --------------------------------------------------------
    # Load paper texture
    # --------------------------------------------------------

    paper = Image.open(
        paper_path
    ).convert("RGB")

    # --------------------------------------------------------
    # Resize paper to cover complete canvas
    # --------------------------------------------------------

    original_width, original_height = (
        paper.size
    )

    scale = max(
        width / original_width,
        height / original_height,
    )

    resized_width = int(
        original_width * scale
    )

    resized_height = int(
        original_height * scale
    )

    paper = paper.resize(
        (
            resized_width,
            resized_height,
        ),
        Image.Resampling.LANCZOS,
    )

    # --------------------------------------------------------
    # Crop center
    # --------------------------------------------------------

    left = (
        resized_width
        - width
    ) // 2

    top = (
        resized_height
        - height
    ) // 2

    paper = paper.crop(
        (
            left,
            top,
            left + width,
            top + height,
        )
    )

    # --------------------------------------------------------
    # Load paragraph
    # --------------------------------------------------------

    paragraph_text = paragraph_path.read_text(
        encoding="utf-8"
    ).strip()

    # --------------------------------------------------------
    # Insert target text into paragraph center
    # --------------------------------------------------------

    modified_paragraph = insert_target_into_paragraph(
        paragraph_text=paragraph_text,
        target_text=target_text,
    )

    # --------------------------------------------------------
    # Step 1: Draw full paragraph (target text is part of it)
    # Returns target bbox + the font used, so we can:
    #   - draw the highlight behind the target (Step 2)
    #   - redraw the target text on top (Step 3)
    # --------------------------------------------------------

    target_bbox, paragraph_font = draw_paragraph(
        image=paper,
        paragraph_text=modified_paragraph,
        font_path=font_path,
        target_text=target_text,
    )

    # --------------------------------------------------------
    # Step 2: Draw highlight behind target text
    #
    # The highlight is applied AFTER the paragraph so it
    # sits on top of the surrounding text pixels, but we
    # then redraw the target word on top in Step 3 so the
    # word itself is never covered.
    # --------------------------------------------------------

    if HIGHLIGHT_ENABLED and target_bbox is not None:

        draw_target_highlight(
            image=paper,
            target_bbox=target_bbox,
            color=HIGHLIGHT_COLOR,
            opacity=HIGHLIGHT_OPACITY,
            padding_x=HIGHLIGHT_PADDING_X,
            padding_y=HIGHLIGHT_PADDING_Y,
            wobble=HIGHLIGHT_WOBBLE,
            offset_y=HIGHLIGHT_OFFSET_Y,
        )

    # --------------------------------------------------------
    # Step 3: Redraw the target text on top of the highlight
    #
    # The paragraph already drew it once, but the highlight
    # (Step 2) painted over it.  Re-rendering at the exact
    # same position with the exact same font ensures the
    # target word stays sharp and readable.
    # --------------------------------------------------------

    if target_bbox is not None and paragraph_font is not None:

        draw_top = ImageDraw.Draw(paper)

        draw_top.text(
            (target_bbox[0], target_bbox[1]),
            target_text,
            font=paragraph_font,
            fill=(35, 35, 35),
        )

    # --------------------------------------------------------
    # Step 4: Apply radial blur (post-processing)
    # The target area (text + highlight) stays sharp;
    # the surrounding paragraph fades to blur.
    # --------------------------------------------------------

    if BLUR_ENABLED and target_bbox is not None:

        paper = apply_radial_blur(
            image=paper,
            target_bbox=target_bbox,
            blur_radius=BLUR_RADIUS,
            focus_radius=FOCUS_RADIUS,
            feather_radius=FEATHER_RADIUS,
        )

    return paper, target_bbox


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("MODULE 1 - PAPER + PARAGRAPH")
    print("=" * 60)

    # --------------------------------------------------------
    # Blur settings
    # --------------------------------------------------------

    print()
    print(f"Blur enabled      : {BLUR_ENABLED}")
    print(f"Blur radius       : {BLUR_RADIUS}")
    print(f"Focus radius      : {FOCUS_RADIUS}")
    print(f"Feather radius    : {FEATHER_RADIUS}")
    print()
    print(f"Highlight enabled : {HIGHLIGHT_ENABLED}")
    print(f"Highlight color   : {HIGHLIGHT_COLOR}")
    print(f"Highlight opacity : {HIGHLIGHT_OPACITY}")
    print(f"Highlight padding : x={HIGHLIGHT_PADDING_X}  y={HIGHLIGHT_PADDING_Y}")

    # --------------------------------------------------------
    # Load assets
    # --------------------------------------------------------

    papers = get_paper_textures()

    paragraphs = get_paragraphs()

    fonts = get_fonts()

    if not papers:

        raise RuntimeError(
            "No paper textures found."
        )

    if not paragraphs:

        raise RuntimeError(
            "No paragraph files found."
        )

    if not fonts:

        raise RuntimeError(
            "No fonts found."
        )

    # --------------------------------------------------------
    # Select paper
    # --------------------------------------------------------

    paper_path = select_from_list(
        papers,
        "SELECT PAPER TEXTURE",
    )

    # --------------------------------------------------------
    # Select aspect ratio
    # --------------------------------------------------------

    aspect_ratio = select_aspect_ratio()

    # --------------------------------------------------------
    # Select paragraph
    # --------------------------------------------------------

    paragraph_path = select_from_list(
        paragraphs,
        "SELECT PARAGRAPH",
    )

    # --------------------------------------------------------
    # Select font
    # --------------------------------------------------------

    font_path = select_from_list(
        fonts,
        "SELECT FONT",
    )

    # --------------------------------------------------------
    # Target text
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("TARGET TEXT")
    print("=" * 60)

    target_text = input(
        "Enter text: "
    ).strip()

    if not target_text:

        raise ValueError(
            "Target text cannot be empty."
        )

    # --------------------------------------------------------
    # Generate
    # --------------------------------------------------------

    output, target_bbox = create_page(
        paper_path=paper_path,
        paragraph_path=paragraph_path,
        font_path=font_path,
        target_text=target_text,
        aspect_ratio=aspect_ratio,
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    output_path = (
        OUTPUT_DIR
        / "module_1_output.png"
    )

    output.save(
        output_path,
        "PNG",
    )

    print()
    print("=" * 60)
    print("MODULE 1 COMPLETED")
    print("=" * 60)

    print(
        f"Output:\n{output_path}"
    )

    print()


if __name__ == "__main__":
    main()