"""
test.py

Pipeline Verification Script

Purpose:
    Validate the complete Freedom Fighter
    AI Video Generation Pipeline.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

from prompts.prompts import SCENES, SCRIPT
from utils.image_generator import generate_images
from utils.tts_generator import generate_narration
from utils.video_creator import create_video


# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ==========================================================
# CONFIG TEST
# ==========================================================

def test_configuration() -> None:

    logger.info("Testing configuration...")

    if not isinstance(SCENES, list):
        raise TypeError("SCENES must be a list.")

    if not SCENES:
        raise ValueError("SCENES cannot be empty.")

    if not isinstance(SCRIPT, str):
        raise TypeError("SCRIPT must be a string.")

    if not SCRIPT.strip():
        raise ValueError("SCRIPT cannot be empty.")

    required_keys = {
        "scene_id",
        "image_file",
        "prompt"
    }

    for scene in SCENES:

        missing_keys = required_keys - set(scene.keys())

        if missing_keys:
            raise ValueError(
                f"Missing scene keys: {missing_keys}"
            )

        if not scene["prompt"].strip():
            raise ValueError(
                f"Empty prompt in {scene['scene_id']}"
            )

        if not scene["image_file"].strip():
            raise ValueError(
                f"Empty image filename in {scene['scene_id']}"
            )

    logger.info("Configuration test passed.")


# ==========================================================
# IMAGE TEST
# ==========================================================

def test_image_generation() -> list[str]:

    logger.info("Testing image generation...")

    image_paths = generate_images(SCENES)

    if len(image_paths) != len(SCENES):
        raise RuntimeError("Image count mismatch.")

    for image_path in image_paths:

        image_file = Path(image_path)

        if not image_file.exists():
            raise FileNotFoundError(
                f"Image not found: {image_path}"
            )

        if image_file.stat().st_size < 1024:
            raise ValueError(
                f"Image appears corrupted: {image_path}"
            )

    logger.info("Image generation test passed.")

    return image_paths


# ==========================================================
# AUDIO TEST
# ==========================================================

def test_narration() -> str:

    logger.info("Testing narration generation...")

    audio_path = generate_narration(SCRIPT)

    audio_file = Path(audio_path)

    if not audio_file.exists():
        raise FileNotFoundError(
            "Narration file missing."
        )

    if audio_file.stat().st_size < 1024:
        raise ValueError(
            "Narration file appears corrupted."
        )

    logger.info("Narration generation test passed.")

    return audio_path


# ==========================================================
# VIDEO TEST
# ==========================================================

def test_video_creation(
    image_paths: list[str],
    audio_path: str
) -> str:

    logger.info("Testing video rendering...")

    video_path = create_video(
        image_paths=image_paths,
        audio_path=audio_path
    )

    video_file = Path(video_path)

    if not video_file.exists():
        raise FileNotFoundError(
            "Video file missing."
        )

    if video_file.stat().st_size < 1024:
        raise ValueError(
            "Video file appears corrupted."
        )

    logger.info("Video rendering test passed.")

    return video_path


# ==========================================================
# MAIN
# ==========================================================

def main() -> int:

    start_time = time.perf_counter()

    try:

        print("\n====================================")
        print("Freedom Fighter Pipeline Test")
        print("====================================")

        test_configuration()

        image_paths = test_image_generation()

        audio_path = test_narration()

        video_path = test_video_creation(
            image_paths,
            audio_path
        )

        execution_time = (
            time.perf_counter() - start_time
        )

        print("\n====================================")
        print("[SUCCESS] ALL TESTS PASSED")
        print(f"Video Output: {video_path}")
        print(f"Execution Time: {execution_time:.2f}s")
        print("====================================")

        return 0

    except Exception as error:

        logger.exception(
            f"Pipeline test failed: {error}"
        )

        print("\n[FAILED] TEST EXECUTION FAILED")
        print(error)

        return 1


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":
    sys.exit(main())