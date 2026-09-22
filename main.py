from pathlib import Path
import random
import textwrap

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ASSETS_DIR = BASE_DIR / "assets"
TEXTURES_DIR = ASSETS_DIR / "paper_textures"
FONTS_DIR = ASSETS_DIR / "fonts"
HIGHLIGHTERS_DIR = ASSETS_DIR / "highlighter"

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# VIDEO SETTINGS
# ============================================================

ASPECT_RATIOS = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
}

DEFAULT_ASPECT_RATIO = "9:16"

FPS = 30

SCENE_DURATION = 2.2

TRANSITION_DURATION = 0.25

NUMBER_OF_SCENES = 6


# ============================================================
# DEMO PARAGRAPHS
# ============================================================

# Later ye Django/database/user-defined paragraph templates
# se aa sakte hain.

DEMO_PARAGRAPHS = [
    """
    Ideas are often hidden inside ordinary moments. Sometimes we notice
    them immediately and sometimes they stay quietly in the background
    until the right moment brings them forward.
    """,

    """
    Creativity is not always about inventing something completely new.
    It can also mean looking at familiar things differently and finding
    connections that were previously unnoticed.
    """,

    """
    Every page carries information in its own visual rhythm. Typography,
    spacing, texture and positioning can completely change how the same
    sentence feels to the reader.
    """,

    """
    Design becomes interesting when structure and randomness work
    together. Some elements remain predictable while others change
    slightly every time they appear.
    """,

    """
    A simple sentence can attract attention when typography, contrast
    and movement guide the eye toward it at exactly the right moment.
    """,

    """
    Stories are built from small fragments of information. A word,
    photograph, handwritten note or highlighted sentence may become
    the most memorable part of an entire page.
    """,
]


# ============================================================
# ASSET DISCOVERY
# ============================================================

def find_image_files(directory: Path):
    extensions = {".png", ".jpg", ".jpeg", ".webp"}

    return [
        file
        for file in directory.rglob("*")
        if file.is_file() and file.suffix.lower() in extensions
    ]


def find_font_files(directory: Path):
    extensions = {".ttf", ".otf"}

    return [
        file
        for file in directory.rglob("*")
        if file.is_file() and file.suffix.lower() in extensions
    ]


def load_assets():
    textures = find_image_files(TEXTURES_DIR)
    highlighters = find_image_files(HIGHLIGHTERS_DIR)
    fonts = find_font_files(FONTS_DIR)

    print()
    print("========== ASSETS ==========")
    print(f"Paper textures : {len(textures)}")
    print(f"Fonts          : {len(fonts)}")
    print(f"Highlighters   : {len(highlighters)}")
    print("============================")
    print()

    if not textures:
        raise RuntimeError(
            f"No paper textures found inside: {TEXTURES_DIR}"
        )

    if not fonts:
        raise RuntimeError(
            f"No fonts found inside: {FONTS_DIR}"
        )

    if not highlighters:
        print(
            "WARNING: No highlighter images found. "
            "Fallback rectangle highlight will be used."
        )

    return textures, fonts, highlighters


# ============================================================
# IMAGE HELPERS
# ============================================================

def cover_resize(image: Image.Image, target_width: int, target_height: int):
    """
    Resize image exactly like CSS object-fit: cover.
    """

    image = image.convert("RGB")

    original_width, original_height = image.size

    scale = max(
        target_width / original_width,
        target_height / original_height
    )

    new_width = int(original_width * scale)
    new_height = int(original_height * scale)

    image = image.resize(
        (new_width, new_height),
        Image.Resampling.LANCZOS
    )

    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2

    image = image.crop(
        (
            left,
            top,
            left + target_width,
            top + target_height,
        )
    )

    return image


def add_soft_overlay(image):
    """
    Slight white overlay so text remains readable over textured pages.
    """

    overlay = Image.new(
        "RGBA",
        image.size,
        (255, 255, 255, 18)
    )

    image = image.convert("RGBA")

    return Image.alpha_composite(image, overlay)


# ============================================================
# FONT HELPERS
# ============================================================

def load_font(font_path: Path, size: int):
    try:
        return ImageFont.truetype(str(font_path), size=size)
    except Exception as error:
        print(f"Could not load font: {font_path}")
        print(error)

        return ImageFont.load_default()


# ============================================================
# TEXT HELPERS
# ============================================================

def wrap_text_by_pixels(
    draw: ImageDraw.ImageDraw,
    text: str,
    font,
    max_width: int
):
    """
    Pixel-aware word wrapping.
    """

    words = text.split()

    lines = []
    current_line = ""

    for word in words:

        test_line = (
            word
            if not current_line
            else f"{current_line} {word}"
        )

        bbox = draw.textbbox(
            (0, 0),
            test_line,
            font=font
        )

        width = bbox[2] - bbox[0]

        if width <= max_width:

            current_line = test_line

        else:

            if current_line:
                lines.append(current_line)

            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def text_width(draw, text, font):
    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font
    )

    return bbox[2] - bbox[0]


def text_height(draw, text, font):
    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font
    )

    return bbox[3] - bbox[1]


# ============================================================
# BACKGROUND PARAGRAPH
# ============================================================

def draw_background_paragraph(
    image,
    paragraph,
    font_path,
    position_mode
):

    draw = ImageDraw.Draw(image)

    width, height = image.size

    font_size = max(28, int(width * 0.033))

    font = load_font(
        font_path,
        font_size
    )

    margin_x = int(width * 0.08)

    max_text_width = int(width * 0.80)

    lines = wrap_text_by_pixels(
        draw,
        paragraph.strip(),
        font,
        max_text_width
    )

    line_spacing = int(font_size * 1.55)

    paragraph_height = len(lines) * line_spacing

    if position_mode == "top":

        start_y = int(height * 0.12)

    elif position_mode == "bottom":

        start_y = int(
            height * 0.78 -
            paragraph_height
        )

    else:

        start_y = int(
            height * 0.50 -
            paragraph_height / 2
        )

    for index, line in enumerate(lines):

        y = start_y + index * line_spacing

        draw.text(
            (margin_x, y),
            line,
            font=font,
            fill=(45, 45, 45, 185)
        )


# ============================================================
# TARGET TEXT POSITION
# ============================================================

def calculate_target_position(
    width,
    height,
    text_width_value,
    scene_index
):

    layouts = [
        "center",
        "left",
        "right",
        "upper",
        "lower"
    ]

    layout = layouts[
        scene_index % len(layouts)
    ]

    margin = int(width * 0.08)

    if layout == "left":

        x = margin
        y = int(height * 0.55)

    elif layout == "right":

        x = width - text_width_value - margin
        y = int(height * 0.42)

    elif layout == "upper":

        x = (width - text_width_value) // 2
        y = int(height * 0.30)

    elif layout == "lower":

        x = (width - text_width_value) // 2
        y = int(height * 0.67)

    else:

        x = (width - text_width_value) // 2
        y = int(height * 0.50)

    x = max(
        margin,
        min(
            x,
            width - text_width_value - margin
        )
    )

    return x, y


# ============================================================
# HIGHLIGHT
# ============================================================

def draw_highlighter(
    canvas,
    highlighter_path,
    x,
    y,
    width,
    height,
    progress
):
    """
    progress:
        0.0 -> invisible
        1.0 -> completely drawn

    PNG gets revealed from left to right.
    """

    if progress <= 0:
        return canvas

    progress = min(
        max(progress, 0.0),
        1.0
    )

    if highlighter_path is None:

        draw = ImageDraw.Draw(
            canvas,
            "RGBA"
        )

        reveal_width = int(
            width * progress
        )

        draw.rounded_rectangle(
            (
                x,
                y,
                x + reveal_width,
                y + height
            ),
            radius=8,
            fill=(255, 224, 60, 120)
        )

        return canvas

    highlight = Image.open(
        highlighter_path
    ).convert("RGBA")

    highlight = highlight.resize(
        (
            max(1, width),
            max(1, height)
        ),
        Image.Resampling.LANCZOS
    )

    reveal_width = int(
        highlight.width * progress
    )

    if reveal_width <= 0:
        return canvas

    visible = highlight.crop(
        (
            0,
            0,
            reveal_width,
            highlight.height
        )
    )

    canvas.alpha_composite(
        visible,
        (
            x,
            y
        )
    )

    return canvas


# ============================================================
# SCENE CREATION
# ============================================================

def render_scene_frame(
    width,
    height,
    texture_path,
    font_path,
    highlighter_path,
    user_text,
    paragraph,
    scene_index,
    animation_progress
):

    # --------------------------------------------------------
    # Background
    # --------------------------------------------------------

    background = Image.open(
        texture_path
    )

    background = cover_resize(
        background,
        width,
        height
    )

    background = add_soft_overlay(
        background
    )

    # --------------------------------------------------------
    # Background paragraph
    # --------------------------------------------------------

    paragraph_positions = [
        "top",
        "middle",
        "bottom"
    ]

    paragraph_position = paragraph_positions[
        scene_index %
        len(paragraph_positions)
    ]

    draw_background_paragraph(
        background,
        paragraph,
        font_path,
        paragraph_position
    )

    # --------------------------------------------------------
    # Target text
    # --------------------------------------------------------

    draw = ImageDraw.Draw(
        background
    )

    target_font_size = max(
        52,
        int(width * 0.072)
    )

    target_font = load_font(
        font_path,
        target_font_size
    )

    maximum_width = int(
        width * 0.82
    )

    target_lines = wrap_text_by_pixels(
        draw,
        user_text,
        target_font,
        maximum_width
    )

    line_height = int(
        target_font_size * 1.20
    )

    complete_text_height = (
        len(target_lines) *
        line_height
    )

    # target block base position

    base_y_positions = [
        0.25,
        0.38,
        0.50,
        0.62
    ]

    base_y = int(
        height *
        base_y_positions[
            scene_index %
            len(base_y_positions)
        ]
    )

    base_y -= (
        complete_text_height // 2
    )

    # --------------------------------------------------------
    # Render each target line
    # --------------------------------------------------------

    for line_index, line in enumerate(
        target_lines
    ):

        line_width = text_width(
            draw,
            line,
            target_font
        )

        horizontal_modes = [
            "center",
            "left",
            "center",
            "right"
        ]

        mode = horizontal_modes[
            scene_index %
            len(horizontal_modes)
        ]

        margin = int(
            width * 0.08
        )

        if mode == "left":

            x = margin

        elif mode == "right":

            x = (
                width -
                margin -
                line_width
            )

        else:

            x = (
                width -
                line_width
            ) // 2

        y = (
            base_y +
            line_index *
            line_height
        )

        measured_height = text_height(
            draw,
            line,
            target_font
        )

        highlight_padding_x = int(
            target_font_size * 0.18
        )

        highlight_padding_y = int(
            target_font_size * 0.12
        )

        highlight_x = (
            x -
            highlight_padding_x
        )

        highlight_y = (
            y +
            measured_height * 0.50
        )

        highlight_width = (
            line_width +
            highlight_padding_x * 2
        )

        highlight_height = max(
            20,
            int(
                target_font_size * 0.55
            )
        )

        # Highlighter goes BEHIND text

        draw_highlighter(
            background,
            highlighter_path,
            int(highlight_x),
            int(highlight_y),
            int(highlight_width),
            int(highlight_height),
            animation_progress
        )

        # recreate draw after compositing

        draw = ImageDraw.Draw(
            background
        )

        # User target text

        draw.text(
            (x, y),
            line,
            font=target_font,
            fill=(18, 18, 18, 255)
        )

    return background.convert("RGB")


# ============================================================
# TRANSITION
# ============================================================

def blend_frames(
    frame_a,
    frame_b,
    progress
):

    progress = min(
        max(progress, 0),
        1
    )

    return Image.blend(
        frame_a,
        frame_b,
        progress
    )


# ============================================================
# VIDEO GENERATOR
# ============================================================

def generate_video(
    user_text,
    aspect_ratio="9:16",
    scenes=NUMBER_OF_SCENES
):

    if aspect_ratio not in ASPECT_RATIOS:
        raise ValueError(
            f"Invalid aspect ratio: {aspect_ratio}"
        )

    width, height = ASPECT_RATIOS[
        aspect_ratio
    ]

    textures, fonts, highlighters = (
        load_assets()
    )

    output_path = (
        OUTPUT_DIR /
        "paper_animation.mp4"
    )

    fourcc = cv2.VideoWriter_fourcc(
        *"mp4v"
    )

    video = cv2.VideoWriter(
        str(output_path),
        fourcc,
        FPS,
        (width, height)
    )

    if not video.isOpened():

        raise RuntimeError(
            "Could not create video writer."
        )

    print(
        f"Generating {width}x{height} video..."
    )

    print(
        f"Text: {user_text}"
    )

    print()

    # --------------------------------------------------------
    # Preselect scene styles so they stay stable
    # --------------------------------------------------------

    scene_configs = []

    for scene_index in range(scenes):

        texture_path = random.choice(
            textures
        )

        font_path = random.choice(
            fonts
        )

        paragraph = random.choice(
            DEMO_PARAGRAPHS
        )

        highlighter_path = (
            random.choice(highlighters)
            if highlighters
            else None
        )

        scene_configs.append(
            {
                "texture": texture_path,
                "font": font_path,
                "paragraph": paragraph,
                "highlighter": highlighter_path,
            }
        )

        print(
            f"Scene {scene_index + 1}"
        )

        print(
            f"  Texture    : {texture_path.name}"
        )

        print(
            f"  Font       : {font_path.name}"
        )

        if highlighter_path:

            print(
                f"  Highlighter: {highlighter_path.name}"
            )

    print()

    frames_per_scene = int(
        SCENE_DURATION * FPS
    )

    transition_frames = int(
        TRANSITION_DURATION * FPS
    )

    previous_final_frame = None

    for scene_index, config in enumerate(
        scene_configs
    ):

        print(
            f"Rendering scene "
            f"{scene_index + 1}/{scenes}"
        )

        for frame_number in range(
            frames_per_scene
        ):

            scene_progress = (
                frame_number /
                max(
                    frames_per_scene - 1,
                    1
                )
            )

            # Highlight animation starts slightly
            # after scene enters

            if scene_progress < 0.15:

                highlight_progress = 0

            elif scene_progress < 0.55:

                highlight_progress = (
                    scene_progress - 0.15
                ) / 0.40

            else:

                highlight_progress = 1

            current_frame = (
                render_scene_frame(
                    width=width,
                    height=height,
                    texture_path=config[
                        "texture"
                    ],
                    font_path=config[
                        "font"
                    ],
                    highlighter_path=config[
                        "highlighter"
                    ],
                    user_text=user_text,
                    paragraph=config[
                        "paragraph"
                    ],
                    scene_index=scene_index,
                    animation_progress=(
                        highlight_progress
                    )
                )
            )

            # -----------------------------------------------
            # Crossfade
            # -----------------------------------------------

            if (
                previous_final_frame
                is not None
                and frame_number
                < transition_frames
            ):

                transition_progress = (
                    frame_number /
                    max(
                        transition_frames,
                        1
                    )
                )

                current_frame = blend_frames(
                    previous_final_frame,
                    current_frame,
                    transition_progress
                )

            # PIL RGB -> OpenCV BGR

            frame_array = np.array(
                current_frame
            )

            frame_array = cv2.cvtColor(
                frame_array,
                cv2.COLOR_RGB2BGR
            )

            video.write(
                frame_array
            )

        previous_final_frame = (
            render_scene_frame(
                width=width,
                height=height,
                texture_path=config[
                    "texture"
                ],
                font_path=config[
                    "font"
                ],
                highlighter_path=config[
                    "highlighter"
                ],
                user_text=user_text,
                paragraph=config[
                    "paragraph"
                ],
                scene_index=scene_index,
                animation_progress=1
            )
        )

    video.release()

    print()
    print("============================")
    print("VIDEO GENERATED")
    print("============================")
    print(output_path)
    print()

    return output_path


# ============================================================
# CLI
# ============================================================

def choose_aspect_ratio():

    print()
    print("Select aspect ratio")
    print()
    print("1. 9:16  - Reels / Shorts")
    print("2. 16:9  - YouTube")
    print("3. 1:1   - Square")
    print("4. 4:5   - Instagram Post")
    print()

    choice = input(
        "Enter option [1]: "
    ).strip()

    mapping = {
        "1": "9:16",
        "2": "16:9",
        "3": "1:1",
        "4": "4:5",
    }

    return mapping.get(
        choice,
        DEFAULT_ASPECT_RATIO
    )


def main():

    print()
    print(
        "================================"
    )
    print(
        "     PAPER TEXT ANIMATION"
    )
    print(
        "================================"
    )

    print()

    user_text = input(
        "Enter the text to highlight: "
    ).strip()

    if not user_text:

        user_text = (
            "Automate your workflow"
        )

    aspect_ratio = (
        choose_aspect_ratio()
    )

    print()

    generate_video(
        user_text=user_text,
        aspect_ratio=aspect_ratio,
        scenes=NUMBER_OF_SCENES
    )


if __name__ == "__main__":
    main()