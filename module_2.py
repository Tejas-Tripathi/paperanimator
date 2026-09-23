"""
MODULE 2 — PAPER ANIMATION VIDEO
=================================

Alignment principle
-------------------
For every frame:

    1. Module 1 renders a LARGE source canvas (SOURCE_SCALE ×
       the final output size) and returns:
           source_image  — complete rendered page
           target_bbox   — where the target word landed

    2. We calculate the combined target+highlight bounding box,
       and find its centre in source coordinates:
           src_cx = (combined_x1 + combined_x2) / 2
           src_cy = (combined_y1 + combined_y2) / 2

    3. We define ONE fixed video point (always the same):
           fixed_x = output_width  / 2   (e.g. 540 for 1080)
           fixed_y = output_height / 2   (e.g. 960 for 1920)

    4. We translate the ENTIRE source image so the target lands
       at (fixed_x, fixed_y):
           crop_left = src_cx - fixed_x
           crop_top  = src_cy - fixed_y

    5. After this crop, the target always sits at (fixed_x,
       fixed_y) — identically, frame after frame.
"""

from pathlib import Path
import random
import shutil

import cv2
from PIL import Image, ImageOps, ImageFilter

# ============================================================
# IMPORT FROM MODULE 1
# ============================================================

from module_1 import (
    OUTPUT_DIR,
    get_paper_textures,
    get_paragraphs,
    get_fonts,
    create_page,
)


# ============================================================
# SETTINGS IMPORTS
# ============================================================

from project_configurations import get_merged_config, DEFAULT_CONFIG

FRAMES_DIR    = OUTPUT_DIR / "module_2_frames"
DEFAULT_VIDEO_OUTPUT  = OUTPUT_DIR / "module_2_output.mp4"


# ============================================================
# ALIGN FRAME
# ============================================================

def align_frame(
    source_image,
    src_target_cx,
    src_target_cy,
    fixed_x,
    fixed_y,
    output_width,
    output_height,
):
    """
    Crop `source_image` so that the point (src_target_cx, src_target_cy)
    in the source lands exactly at (fixed_x, fixed_y) in the returned frame.
    """
    src_w, src_h = source_image.size

    crop_left   = src_target_cx - fixed_x
    crop_top    = src_target_cy - fixed_y

    # We use exact float coordinates for translation to avoid subpixel drift.
    # The affine transform allows subpixel precision.
    
    # Affine transform matrix: (a, b, c, d, e, f)
    # x_src = a * x_out + b * y_out + c
    # y_src = d * x_out + e * y_out + f
    # We want (fixed_x, fixed_y) to map to (src_target_cx, src_target_cy).
    # c = crop_left
    # f = crop_top
    
    matrix = (1, 0, crop_left, 0, 1, crop_top)
    
    cropped = source_image.transform(
        (output_width, output_height),
        Image.AFFINE,
        matrix,
        resample=Image.Resampling.BICUBIC
    )

    return cropped, crop_left, crop_top


# ============================================================
# ASSET COMBINATION SELECTOR
# ============================================================

def generate_asset_configs(papers, paragraphs, fonts, n):
    configs = []
    prev    = None
    for _ in range(n):
        for _attempt in range(100):
            combo = (
                random.choice(papers),
                random.choice(paragraphs),
                random.choice(fonts),
            )
            if combo != prev:
                break
        configs.append(combo)
        prev = combo
    return configs


# ============================================================
# FRAME DIRECTORY MANAGEMENT
# ============================================================

def prepare_frames_dir():
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# FRAME GENERATION
# ============================================================

def generate_module_2_frames(
    target_text,
    aspect_ratio,
    n_images,
    is_test=False,
    config=None
):
    config = get_merged_config(config)
    SOURCE_SCALE = config["SOURCE_SCALE"]
    HIGHLIGHT_PADDING_X = config["HIGHLIGHT_PADDING_X"]
    HIGHLIGHT_PADDING_Y = config["HIGHLIGHT_PADDING_Y"]
    HIGHLIGHT_OFFSET_Y = config["HIGHLIGHT_OFFSET_Y"]

    out_w = aspect_ratio["width"]
    out_h = aspect_ratio["height"]

    fixed_x = out_w / 2.0
    fixed_y = out_h / 2.0

    src_w = int(out_w * SOURCE_SCALE)
    src_h = int(out_h * SOURCE_SCALE)

    source_aspect = {
        "name"  : aspect_ratio["name"],
        "width" : src_w,
        "height": src_h,
    }

    papers     = get_paper_textures()
    paragraphs = get_paragraphs()
    fonts      = get_fonts()

    if not papers: raise RuntimeError("No paper textures found.")
    if not paragraphs: raise RuntimeError("No paragraph files found.")
    if not fonts: raise RuntimeError("No fonts found.")

    configs = generate_asset_configs(papers, paragraphs, fonts, n_images)

    frame_paths = []
    
    print()
    print("-" * 60)
    print(f"GENERATING {'TEST ' if is_test else ''}FRAMES")
    print(f"Target locked to: ({fixed_x:.1f}, {fixed_y:.1f})")
    print("-" * 60)
    print()

    for index, (paper_path, para_path, font_path) in enumerate(configs, start=1):
        source_image, target_bbox = create_page(
            paper_path     = paper_path,
            paragraph_path = para_path,
            font_path      = font_path,
            target_text    = target_text,
            aspect_ratio   = source_aspect,
            config         = config,
        )

        if target_bbox is not None:
            x1, y1, x2, y2 = target_bbox
            
            # Highlight combined bbox
            hx1 = x1 - HIGHLIGHT_PADDING_X
            hy1 = y1 - HIGHLIGHT_PADDING_Y + HIGHLIGHT_OFFSET_Y
            hx2 = x2 + HIGHLIGHT_PADDING_X
            hy2 = y2 + HIGHLIGHT_PADDING_Y + HIGHLIGHT_OFFSET_Y
            
            combined_x1 = min(x1, hx1)
            combined_y1 = min(y1, hy1)
            combined_x2 = max(x2, hx2)
            combined_y2 = max(y2, hy2)
            
            src_cx = (combined_x1 + combined_x2) / 2.0
            src_cy = (combined_y1 + combined_y2) / 2.0
        else:
            src_cx = src_w / 2.0
            src_cy = src_h / 2.0
            print(f"  [WARNING] target_bbox is None for frame {index}")

        # Create a blurred background using the current paper texture
        bg_paper = Image.open(paper_path).convert("RGB")
        bg_paper = ImageOps.fit(bg_paper, (out_w, out_h), Image.Resampling.LANCZOS)
        bg_paper = bg_paper.filter(ImageFilter.GaussianBlur(radius=60)).convert("RGBA")

        # Ensure source_image is RGBA so transformed out-of-bounds areas are transparent
        source_image = source_image.convert("RGBA")

        aligned_rgba, crop_left, crop_top = align_frame(
            source_image  = source_image,
            src_target_cx = src_cx,
            src_target_cy = src_cy,
            fixed_x       = fixed_x,
            fixed_y       = fixed_y,
            output_width  = out_w,
            output_height = out_h,
        )

        final_frame = Image.alpha_composite(bg_paper, aligned_rgba).convert("RGB")

        final_cx = src_cx - crop_left
        final_cy = src_cy - crop_top

        print(
            f"  Frame {index:>2}:  "
            f"orig_center=({src_cx:7.1f}, {src_cy:7.1f})  "
            f"FINAL target center=({final_cx:.1f}, {final_cy:.1f})"
        )

        name_prefix = "test" if is_test else "frame"
        frame_path = FRAMES_DIR / f"{name_prefix}_{index:04d}.png"
        final_frame.save(str(frame_path), "PNG")
        frame_paths.append(frame_path)

    return frame_paths


# ============================================================
# PREVIEW IMAGE GENERATION
# ============================================================

def generate_preview_image(target_text, aspect_ratio_key, config=None):
    """
    Generate a single PIL Image representing the final cropped frame 
    using the provided configuration. Useful for real-time preview APIs.
    """
    config = get_merged_config(config)
    aspect_ratios = config["M1_ASPECT_RATIOS"]
    if aspect_ratio_key not in aspect_ratios:
        aspect_ratio_key = "1"
    aspect_ratio = aspect_ratios[aspect_ratio_key]

    SOURCE_SCALE = config["SOURCE_SCALE"]
    HIGHLIGHT_PADDING_X = config["HIGHLIGHT_PADDING_X"]
    HIGHLIGHT_PADDING_Y = config["HIGHLIGHT_PADDING_Y"]
    HIGHLIGHT_OFFSET_Y = config["HIGHLIGHT_OFFSET_Y"]

    out_w = aspect_ratio["width"]
    out_h = aspect_ratio["height"]

    fixed_x = out_w / 2.0
    fixed_y = out_h / 2.0

    src_w = int(out_w * SOURCE_SCALE)
    src_h = int(out_h * SOURCE_SCALE)

    source_aspect = {
        "name"  : aspect_ratio["name"],
        "width" : src_w,
        "height": src_h,
    }

    papers     = get_paper_textures()
    paragraphs = get_paragraphs()
    fonts      = get_fonts()

    if not papers or not paragraphs or not fonts:
        raise RuntimeError("Missing assets")

    paper_path = papers[0]
    para_path = paragraphs[0]
    font_path = fonts[0]

    source_image, target_bbox = create_page(
        paper_path     = paper_path,
        paragraph_path = para_path,
        font_path      = font_path,
        target_text    = target_text,
        aspect_ratio   = source_aspect,
        config         = config,
    )

    if target_bbox is not None:
        x1, y1, x2, y2 = target_bbox
        hx1 = x1 - HIGHLIGHT_PADDING_X
        hy1 = y1 - HIGHLIGHT_PADDING_Y + HIGHLIGHT_OFFSET_Y
        hx2 = x2 + HIGHLIGHT_PADDING_X
        hy2 = y2 + HIGHLIGHT_PADDING_Y + HIGHLIGHT_OFFSET_Y
        
        combined_x1 = min(x1, hx1)
        combined_y1 = min(y1, hy1)
        combined_x2 = max(x2, hx2)
        combined_y2 = max(y2, hy2)
        
        src_cx = (combined_x1 + combined_x2) / 2.0
        src_cy = (combined_y1 + combined_y2) / 2.0
    else:
        src_cx = src_w / 2.0
        src_cy = src_h / 2.0

    bg_paper = Image.open(paper_path).convert("RGB")
    bg_paper = ImageOps.fit(bg_paper, (out_w, out_h), Image.Resampling.LANCZOS)
    bg_paper = bg_paper.filter(ImageFilter.GaussianBlur(radius=60)).convert("RGBA")

    source_image = source_image.convert("RGBA")

    aligned_rgba, crop_left, crop_top = align_frame(
        source_image  = source_image,
        src_target_cx = src_cx,
        src_target_cy = src_cy,
        fixed_x       = fixed_x,
        fixed_y       = fixed_y,
        output_width  = out_w,
        output_height = out_h,
    )

    final_frame = Image.alpha_composite(bg_paper, aligned_rgba).convert("RGB")
    return final_frame


# ============================================================
# VIDEO CREATION
# ============================================================

def create_video(frame_paths, output_width, output_height, output_path=None, config=None):
    if output_path is None:
        output_path = DEFAULT_VIDEO_OUTPUT
    
    config = get_merged_config(config)
    FPS = config["MODULE_2_FPS"]
    IMAGE_DURATION = config["IMAGE_DURATION"]
        
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(
        str(output_path),
        fourcc,
        FPS,
        (output_width, output_height),
    )
    frames_per_image = max(1, int(round(FPS * IMAGE_DURATION)))
    for frame_path in frame_paths:
        bgr = cv2.imread(str(frame_path))
        if bgr is None: continue
        for _ in range(frames_per_image):
            writer.write(bgr)
    writer.release()


# ============================================================
# SELECTION HELPERS
# ============================================================

def select_aspect_ratio_m2(config):
    aspect_ratios = config["M1_ASPECT_RATIOS"]
    print()
    print("=" * 60)
    print("SELECT ASPECT RATIO")
    print("=" * 60)
    for key, value in aspect_ratios.items():
        print(f"  {key}. {value['name']} ({value['width']} x {value['height']})")
    print()
    while True:
        choice = input("Select number: ").strip()
        if choice in aspect_ratios:
            return aspect_ratios[choice]
        print("Invalid selection.")


def select_number_of_images(config):
    NUMBER_OF_IMAGES = config["NUMBER_OF_IMAGES"]
    print()
    print("=" * 60)
    print("NUMBER OF IMAGES")
    print("=" * 60)
    raw = input(f"Enter number of images [{NUMBER_OF_IMAGES}]: ").strip()
    if not raw: return NUMBER_OF_IMAGES
    try:
        val = int(raw)
        return val if val >= 1 else NUMBER_OF_IMAGES
    except ValueError:
        return NUMBER_OF_IMAGES


# ============================================================
# MAIN
# ============================================================

def generate_animation_video(target_text, aspect_ratio_key, n_images, output_filename=None, config=None):
    config = get_merged_config(config)
    aspect_ratios = config["M1_ASPECT_RATIOS"]
    if aspect_ratio_key not in aspect_ratios:
        raise ValueError(f"Invalid aspect ratio key: {aspect_ratio_key}")
        
    aspect_ratio = aspect_ratios[aspect_ratio_key]
    
    prepare_frames_dir()

    # Run full generation
    frame_paths = generate_module_2_frames(
        target_text=target_text,
        aspect_ratio=aspect_ratio,
        n_images=n_images,
        is_test=False,
        config=config,
    )

    out_w = aspect_ratio["width"]
    out_h = aspect_ratio["height"]
    
    if output_filename:
        if not output_filename.endswith('.mp4'):
            output_filename += '.mp4'
        output_path = OUTPUT_DIR / output_filename
    else:
        import uuid
        output_path = OUTPUT_DIR / f"paper_animation_{uuid.uuid4().hex[:8]}.mp4"
        
    create_video(frame_paths, out_w, out_h, output_path=output_path, config=config)
    return str(output_path)

def main():
    print()
    print("=" * 60)
    print("MODULE 2 - PAPER ANIMATION VIDEO")
    print("=" * 60)
    
    config = get_merged_config()
    aspect_ratios = config["M1_ASPECT_RATIOS"]
    
    aspect_ratio = select_aspect_ratio_m2(config)
    # Find the key for the selected aspect ratio
    aspect_ratio_key = next((k for k, v in aspect_ratios.items() if v == aspect_ratio), "1")
    
    n_images     = select_number_of_images(config)
    
    print()
    target_text = input("Enter target text: ").strip()
    if not target_text:
        raise ValueError("Target text cannot be empty.")
        
    print()
    print("=" * 60)
    print("CREATING VIDEO")
    print("=" * 60)
    
    output_path = generate_animation_video(target_text, aspect_ratio_key, n_images, config=config)
    print(f"\nMODULE 2 COMPLETED\nVideo saved to: {output_path}")

if __name__ == "__main__":
    main()
