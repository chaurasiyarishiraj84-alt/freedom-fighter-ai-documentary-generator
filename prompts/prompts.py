"""
prompts.py

Cinematic Story Brain — Director Engine v2

Responsibilities:
    - Story planning (not just image prompts)
    - Emotion tagging per scene
    - Motion direction per scene
    - Cinematic duration pacing
    - Narration script aligned to story arc
"""

from typing import List, Dict, Any

# ==========================================================
# PROJECT METADATA
# ==========================================================

FREEDOM_FIGHTER = "Bhagat Singh"

# ==========================================================
# NARRATION SCRIPT
# (Aligned to scene arc — intro → rise → climax → tribute)
# ==========================================================

SCRIPT = (
    "Bhagat Singh was one of India's most fearless freedom fighters. "
    "Born into a patriotic family, he was drawn to revolutionary thought "
    "from a young age — studying, planning, and refusing to accept "
    "British rule in silence. "
    "His courage in court, his sacrifice at the gallows, "
    "and his unwavering commitment to independence "
    "inspired millions across the nation. "
    "Even today, he remains a timeless symbol of "
    "patriotism, bravery, and the spirit of a free India."
)

# ==========================================================
# 🎬 CINEMATIC SCENE CONFIGURATION
# (Director Engine v2 — story blocks, not image prompts)
#
# Fields:
#   scene_id  : unique identifier
#   story     : narrative purpose of this scene
#   emotion   : emotional tone  (drives prompt + pacing)
#   prompt    : visual prompt for image generator
#   motion    : camera motion for video generator
#   duration  : scene duration in seconds (cinematic pacing)
#   image_file: output filename
# ==========================================================

SCENES: List[Dict[str, Any]] = [

    # ----------------------------------------------------------
    # SCENE 1 — INTRODUCTION
    # Arc: Establish the hero, serious and iconic
    # ----------------------------------------------------------
    {
        "scene_id"  : "scene1",
        "story"     : (
            "Introduction of Bhagat Singh — "
            "iconic revolutionary, colonial India era"
        ),
        "emotion"   : "serious",
        "camera"    : "close-up",
        "motion"    : "slow_zoom_in",
        "duration"  : 5.0,
        "prompt"    : (
            f"Ultra realistic portrait of {FREEDOM_FIGHTER}, "
            "wearing a yellow turban, "
            "Indian freedom fighter of colonial era, "
            "dramatic cinematic lighting, "
            "highly detailed facial features, "
            "4K realism, professional photography"
        ),
        "image_file": "scene1.jpg",
    },

    # ----------------------------------------------------------
    # SCENE 2 — THE THINKER
    # Arc: Revolutionary studying, ideological awakening
    # ----------------------------------------------------------
    {
        "scene_id"  : "scene2",
        "story"     : (
            "Bhagat Singh reading revolutionary literature — "
            "ideological awakening and planning"
        ),
        "emotion"   : "intense",
        "camera"    : "medium shot",
        "motion"    : "slow_pan_right",
        "duration"  : 4.5,
        "prompt"    : (
            f"{FREEDOM_FIGHTER} reading revolutionary literature, "
            "wooden desk with books and candle light, "
            "colonial India historical atmosphere, "
            "Indian independence movement, "
            "realistic documentary style, "
            "cinematic composition, 4K quality"
        ),
        "image_file": "scene2.jpg",
    },

    # ----------------------------------------------------------
    # SCENE 3 — THE HERO
    # Arc: Climax — courage, sacrifice, heroic stance
    # ----------------------------------------------------------
    {
        "scene_id"  : "scene3",
        "story"     : (
            "Bhagat Singh standing fearless — "
            "symbol of courage and ultimate sacrifice"
        ),
        "emotion"   : "patriotic",
        "camera"    : "wide shot",
        "motion"    : "slow_zoom_out",
        "duration"  : 5.5,
        "prompt"    : (
            f"{FREEDOM_FIGHTER} standing proudly, "
            "heroic pose, symbol of courage and sacrifice, "
            "patriotic atmosphere, dramatic cinematic lighting, "
            "historical realism, ultra detailed, "
            "4K documentary photography"
        ),
        "image_file": "scene3.jpg",
    },

    # ----------------------------------------------------------
    # SCENE 4 — THE TRIBUTE
    # Arc: Emotional close — legacy, freedom, hope
    # ----------------------------------------------------------
    {
        "scene_id"  : "scene4",
        "story"     : (
            "Indian tricolor at sunrise — "
            "tribute to the legacy of freedom fighters"
        ),
        "emotion"   : "hopeful",
        "camera"    : "wide shot",
        "motion"    : "slow_zoom_in",
        "duration"  : 6.0,
        "prompt"    : (
            "Indian tricolor flag waving at sunrise, "
            f"tribute to {FREEDOM_FIGHTER}, "
            "inspiring patriotic atmosphere, "
            "cinematic ending frame, "
            "golden hour sunlight, ultra realistic, "
            "highly detailed, 4K masterpiece"
        ),
        "image_file": "scene4.jpg",
    },

]

# ==========================================================
# OPTIONAL: FLAT TIMELINE
# (For future audio-sync / music intensity engine)
# ==========================================================

def build_flat_timeline() -> List[Dict[str, Any]]:
    """
    Compute absolute start/end times per scene
    for audio sync or subtitle generation.
    """

    timeline = []
    cursor = 0.0

    for scene in SCENES:
        duration = scene["duration"]
        timeline.append({
            "scene_id"         : scene["scene_id"],
            "start"            : round(cursor, 3),
            "end"              : round(cursor + duration, 3),
            "emotion"          : scene["emotion"],
            "motion"           : scene["motion"],
            "camera"           : scene["camera"],
        })
        cursor += duration

    return timeline


TIMELINE = build_flat_timeline()

# ==========================================================
# PROMPT EXPORT (backward compatibility)
# ==========================================================

PROMPTS: List[str] = [
    scene["prompt"]
    for scene in SCENES
]

# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def get_scene_count() -> int:
    return len(SCENES)


def get_image_filenames() -> List[str]:
    return [scene["image_file"] for scene in SCENES]


def get_total_duration() -> float:
    return sum(scene["duration"] for scene in SCENES)


def get_scene_by_id(scene_id: str) -> Dict[str, Any]:
    for scene in SCENES:
        if scene["scene_id"] == scene_id:
            return scene
    raise KeyError(f"Scene not found: {scene_id}")


# ==========================================================
# VALIDATION
# ==========================================================

def validate_scene_configuration() -> None:
    """
    Validate all scenes have required cinematic fields.
    """

    if not SCENES:
        raise ValueError("No scenes configured.")

    required_keys = {
        "scene_id",
        "story",
        "emotion",
        "camera",
        "motion",
        "duration",
        "prompt",
        "image_file",
    }

    for scene in SCENES:

        missing_keys = required_keys - scene.keys()

        if missing_keys:
            raise ValueError(
                f"Scene '{scene.get('scene_id', '?')}' "
                f"missing keys: {missing_keys}"
            )

        if not scene["prompt"].strip():
            raise ValueError(
                f"Empty prompt in {scene['scene_id']}"
            )

        if scene["duration"] <= 0:
            raise ValueError(
                f"Invalid duration in {scene['scene_id']}: "
                f"{scene['duration']}"
            )

    if not SCRIPT.strip():
        raise ValueError("SCRIPT is empty.")


validate_scene_configuration()