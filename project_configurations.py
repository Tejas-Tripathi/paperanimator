# ============================================================
# PROJECT CONFIGURATIONS
# ============================================================
# Default configuration dictionary. 
# Tasks and UI merge their custom settings into this default config.

DEFAULT_CONFIG = {
    # main.py settings
    "MAIN_ASPECT_RATIOS": {
        "9:16": (1080, 1920),
        "16:9": (1920, 1080),
        "1:1": (1080, 1080),
        "4:5": (1080, 1350),
    },
    "DEFAULT_ASPECT_RATIO": "9:16",
    "MAIN_FPS": 30,
    "SCENE_DURATION": 2.2,
    "TRANSITION_DURATION": 0.25,
    "NUMBER_OF_SCENES": 6,

    # Blur Configuration (Module 1)
    "BLUR_ENABLED": True,
    "BLUR_RADIUS": 12,
    "FOCUS_RADIUS": 80,
    "FEATHER_RADIUS": 250,

    # Highlight Configuration (Module 1)
    "HIGHLIGHT_ENABLED": True,
    "HIGHLIGHT_COLOR": "#FFF200",
    "HIGHLIGHT_OPACITY": 180,
    "HIGHLIGHT_PADDING_X": 10,
    "HIGHLIGHT_PADDING_Y": 13,
    "HIGHLIGHT_WOBBLE": 3,
    "HIGHLIGHT_OFFSET_Y": 4,

    # Aspect Ratios (Module 1 & 2)
    "M1_ASPECT_RATIOS": {
        "1": {"name": "9:16", "width": 1080, "height": 1920},
        "2": {"name": "16:9", "width": 1920, "height": 1080},
        "3": {"name": "1:1", "width": 1080, "height": 1080},
        "4": {"name": "4:5", "width": 1080, "height": 1350},
    },

    # Module 2 Configuration
    "NUMBER_OF_IMAGES": 12,
    "TEST_FRAME_COUNT": 5,
    "MODULE_2_FPS": 30,
    "IMAGE_DURATION": 0.1,
    "SOURCE_SCALE": 2.0,
}

# For backwards compatibility with any existing imports, we unpack them to globals
globals().update(DEFAULT_CONFIG)

def get_merged_config(overrides=None):
    """
    Returns a complete config dictionary safely merged with user overrides.
    """
    config = DEFAULT_CONFIG.copy()
    if overrides and isinstance(overrides, dict):
        config.update(overrides)
    return config
