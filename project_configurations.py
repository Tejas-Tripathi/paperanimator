# ============================================================
# MAIN.PY SETTINGS
# ============================================================

MAIN_ASPECT_RATIOS = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
}

DEFAULT_ASPECT_RATIO = "9:16"
MAIN_FPS = 30
SCENE_DURATION = 2.2
TRANSITION_DURATION = 0.25
NUMBER_OF_SCENES = 6

# ============================================================
# BLUR CONFIGURATION (MODULE 1)
# ============================================================

# Set to False to compare output without blur effect
BLUR_ENABLED = True

# Maximum Gaussian blur radius applied to the outer region
BLUR_RADIUS = 12

# Pixel radius around the target text that stays 100% sharp
FOCUS_RADIUS = 80

# Pixel distance over which the image transitions from
# sharp to maximum blur (feathering zone)
FEATHER_RADIUS = 250

# ============================================================
# HIGHLIGHT CONFIGURATION (MODULE 1)
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
# ASPECT RATIOS (MODULE 1 & 2)
# ============================================================

M1_ASPECT_RATIOS = {
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
# MODULE 2 CONFIGURATION
# ============================================================

NUMBER_OF_IMAGES = 12
TEST_FRAME_COUNT = 5

MODULE_2_FPS = 30
IMAGE_DURATION = 0.1

SOURCE_SCALE = 2.0
