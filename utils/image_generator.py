"""
image_generator.py

Generate cinematic scene images from prompts
using Pollinations AI.

Cinematic Engine v2:
✔ Cinematic prompt builder
✔ Style lock (35mm film consistency)
✔ Scene intent tagging (emotion + camera)
✔ Character continuity suffix
✔ Timeline-aware (accepts timeline dict)
✔ Retry logic with structured logging
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests


# ==========================================================
# CONFIGURATION
# ==========================================================

BASE_URL = "https://image.pollinations.ai/prompt/"
OUTPUT_DIR = Path("assets/images")

REQUEST_TIMEOUT = 60
MAX_RETRIES = 3

HEADERS = {
    "User-Agent": "CinematicAIDirector/2.0"
}

# ----------------------------------------------------------
# 🎬 STYLE LOCK
# Applied to every scene — ensures visual consistency
# ----------------------------------------------------------

CINEMATIC_STYLE = (
    "cinematic documentary, ultra realistic, "
    "film grain, dramatic lighting, "
    "shallow depth of field, 35mm film look, "
    "high detail, emotional storytelling, "
    "historical accuracy, cinematic color grading"
)

CHARACTER_CONTINUITY = (
    "consistent character design, "
    "same historical outfit, "
    "same face across scenes"
)


# ==========================================================
# LOGGER
# ==========================================================

logger = logging.getLogger(__name__)


# ==========================================================
# OUTPUT DIRECTORY
# ==========================================================

def create_output_directory() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================================
# 🎬 CINEMATIC PROMPT ENGINE
# ==========================================================

def build_cinematic_prompt(scene: Dict[str, Any]) -> str:
    """
    Transform a basic scene prompt into a
    film-grade cinematic prompt.

    Uses:
        - base prompt
        - emotion tag  (e.g. "intense", "hopeful")
        - camera tag   (e.g. "close-up", "wide shot")
        - style lock   (35mm film, dramatic lighting)
        - continuity   (consistent character across scenes)
    """

    base = scene["prompt"].strip()

    # --- emotion modifier ---
    emotion = scene.get("emotion", "")
    emotion_suffix = (
        f"{emotion} emotion, {emotion} mood"
        if emotion else ""
    )

    # --- camera modifier ---
    camera = scene.get("camera", "")
    camera_suffix = (
        f"{camera} shot"
        if camera else ""
    )

    # --- assemble full cinematic prompt ---
    parts = [
        base,
        emotion_suffix,
        camera_suffix,
        CINEMATIC_STYLE,
        CHARACTER_CONTINUITY,
    ]

    # Remove empty parts
    cinematic_prompt = ", ".join(
        p for p in parts if p
    )

    return cinematic_prompt


# ==========================================================
# VALIDATION
# ==========================================================

def validate_scene(scene: Dict[str, Any]) -> None:

    required_keys = {"scene_id", "image_file", "prompt"}

    missing_keys = required_keys - scene.keys()

    if missing_keys:
        raise ValueError(
            f"Missing keys in scene "
            f"'{scene.get('scene_id', '?')}': "
            f"{missing_keys}"
        )

    if not scene["prompt"].strip():
        raise ValueError(
            f"Empty prompt in {scene['scene_id']}"
        )


# ==========================================================
# URL BUILDER
# ==========================================================

def build_image_url(prompt: str) -> str:

    encoded_prompt = quote(prompt, safe="")

    return f"{BASE_URL}{encoded_prompt}"


# ==========================================================
# DOWNLOAD
# ==========================================================

def download_image(
    url: str,
    output_path: Path
) -> None:

    last_error: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            logger.info(
                f"  Attempt {attempt}/{MAX_RETRIES} | "
                f"{output_path.name}"
            )

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

            content_type = response.headers.get(
                "Content-Type", ""
            )

            if "image" not in content_type:
                raise RuntimeError(
                    "API did not return image data."
                )

            output_path.write_bytes(response.content)

            logger.info(f"  Saved → {output_path}")

            return

        except Exception as error:

            last_error = error

            logger.warning(
                f"  Failed attempt {attempt}: {error}"
            )

            time.sleep(2)

    raise RuntimeError(
        f"Could not generate image after "
        f"{MAX_RETRIES} attempts: {output_path.name}"
    ) from last_error


# ==========================================================
# 🎬 MAIN GENERATOR (CINEMATIC ENGINE v2)
# ==========================================================

def generate_images(
    scenes: List[Dict[str, Any]]
) -> List[str]:
    """
    Generate all cinematic scene images.

    Accepts:
        - List[Dict] from SCENES (legacy)
        - List[Dict] from build_timeline() (cinematic)

    Each scene dict supports:
        scene_id    : str   (required)
        image_file  : str   (required)
        prompt      : str   (required)
        emotion     : str   (optional) e.g. "intense"
        camera      : str   (optional) e.g. "close-up"
        duration    : float (optional, used by video_creator)
    """

    create_output_directory()

    generated_files: List[str] = []

    total = len(scenes)
    logger.info(f"🎬 Generating {total} cinematic scenes...")

    for i, scene in enumerate(scenes, start=1):

        validate_scene(scene)

        scene_id   = scene["scene_id"]
        filename   = scene["image_file"]
        output_path = OUTPUT_DIR / filename

        # --- build cinematic prompt ---
        cinematic_prompt = build_cinematic_prompt(scene)

        logger.info(
            f"\n[{i}/{total}] Scene: {scene_id}"
        )
        logger.info(
            f"  Emotion  : {scene.get('emotion', 'none')}"
        )
        logger.info(
            f"  Camera   : {scene.get('camera', 'none')}"
        )
        logger.info(
            f"  Prompt   : {cinematic_prompt[:80]}..."
        )

        image_url = build_image_url(cinematic_prompt)

        download_image(image_url, output_path)

        generated_files.append(str(output_path))

    logger.info(
        f"\n✅ Image generation complete. "
        f"{len(generated_files)}/{total} scenes generated."
    )

    return generated_files