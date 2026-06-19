"""
main.py — Cinematic AI Director Engine

Usage:
    # Google Veo mode (real AI video generation)
    $env:MODE = "ai_video"
    $env:GOOGLE_API_KEY = "your-key-here"
    python main.py

    # Local Ken Burns mode (no API needed)
    python main.py
"""

from __future__ import annotations

# FFmpeg patch — must be first
try:
    import ffmpeg_patch  # noqa: F401
except ImportError:
    pass

# BUG 1 FIX: Load .env file so GOOGLE_API_KEY and MODE survive across
# terminal sessions without re-setting env vars every time.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed — env vars must be set manually

import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

from prompts.prompts import SCENES, SCRIPT
from utils.image_generator import generate_images
from utils.tts_generator import generate_narration
from cinematic_engine.timeline_builder import build_timeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

MODE = os.getenv("MODE", "ken_burns").lower()

# ==========================================================
# SETUP
# ==========================================================

def setup_environment() -> None:
    Path("assets/images").mkdir(parents=True, exist_ok=True)
    Path("assets/audio").mkdir(parents=True, exist_ok=True)
    Path("assets/videos").mkdir(parents=True, exist_ok=True)
    Path("output").mkdir(parents=True, exist_ok=True)

# ==========================================================
# VALIDATION
# ==========================================================

def validate_configuration() -> None:

    if not isinstance(SCENES, list) or not SCENES:
        raise ValueError("SCENES must be a non-empty list.")

    if not isinstance(SCRIPT, str) or not SCRIPT.strip():
        raise ValueError("SCRIPT must be a non-empty string.")

    if MODE == "ai_video":
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError(
                "\nGOOGLE_API_KEY not set.\n"
                "Get key: https://aistudio.google.com/apikey\n"
                "PowerShell : $env:GOOGLE_API_KEY = 'your-key-here'\n"
                "Or create a .env file with: GOOGLE_API_KEY=your-key-here"
            )

# ==========================================================
# KEN BURNS PIPELINE (local, no API)
# ==========================================================

def run_ken_burns_pipeline() -> str:

    logger.info("Building cinematic timeline...")
    timeline = build_timeline(SCENES, SCRIPT)

    logger.info("Generating scene images...")
    image_paths = generate_images(timeline)

    logger.info("Generating narration...")
    audio_path = generate_narration(SCRIPT)

    logger.info("Rendering cinematic video (Ken Burns)...")
    from utils.video_creator import create_video
    return create_video(
        image_paths=image_paths,
        audio_path=audio_path,
        timeline=timeline,
    )

# ==========================================================
# AI VIDEO PIPELINE (Google Veo)
# ==========================================================

def run_ai_video_pipeline() -> str:

    logger.info("Building cinematic timeline...")
    timeline = build_timeline(SCENES, SCRIPT)

    logger.info("Generating scene images...")
    image_paths = generate_images(timeline)

    logger.info("Generating narration audio...")
    audio_path = generate_narration(SCRIPT)

    logger.info("Sending images to Google Veo...")
    from utils.video_generator import generate_scene_videos
    video_clip_paths = generate_scene_videos(timeline, image_paths)

    logger.info("Assembling final film with narration...")
    return assemble_clips(video_clip_paths, audio_path)

# ==========================================================
# ASSEMBLER — join Veo clips + add narration
# MoviePy 1.0.3 compatible
# ==========================================================

def assemble_clips(
    video_clip_paths: List[str],
    audio_path: str,
) -> str:

    from moviepy.editor import (
        VideoFileClip,
        AudioFileClip,
        concatenate_videoclips,
    )

    output_path = Path("output/freedom_fighter_video.mp4")

    clips : List[VideoFileClip]      = []
    audio : Optional[AudioFileClip]  = None
    video : Optional[VideoFileClip]  = None

    try:
        logger.info(f"Loading {len(video_clip_paths)} video clips...")

        for p in video_clip_paths:
            if not Path(p).exists():
                raise FileNotFoundError(f"Clip not found: {p}")
            clips.append(VideoFileClip(p))

        # BUG 2 FIX: concatenate_videoclips with method="compose" can
        # silently produce a black video when clips have different
        # resolutions (Veo can return mixed resolutions).
        # "chain" method is safer for mixed-resolution clips from an API.
        logger.info("Concatenating clips...")
        video = concatenate_videoclips(clips, method="chain")

        logger.info("Adding narration audio...")
        audio = AudioFileClip(audio_path)

        # BUG 3 FIX: original code only trimmed audio longer than video.
        # If audio is shorter, video plays in silence at the end.
        # Correct fix: always clamp audio to video duration either way.
        audio_duration = audio.duration
        video_duration = video.duration

        if audio_duration != video_duration:
            # Trim or pad: always use the shorter of the two as the
            # final duration so nothing plays in silence or gets cut off.
            final_duration = min(audio_duration, video_duration)
            audio = audio.subclip(0, final_duration)
            video = video.subclip(0, final_duration)   # MoviePy 1.0.3

        video = video.set_audio(audio)

        logger.info(f"Rendering final video ({video.duration:.1f}s)...")

        video.write_videofile(
            str(output_path),
            codec="libx264",
            audio_codec="aac",
            fps=24,
            threads=4,
            # BUG 4 FIX: verbose=False alone does not suppress all
            # MoviePy 1.x output — must also pass logger="bar" or
            # logger=None. Use logger=None to fully suppress spam.
            verbose=False,
            logger=None,
        )

        size_mb = output_path.stat().st_size / (1024 * 1024)

        if size_mb < 0.1:
            raise RuntimeError(
                f"Output video too small ({size_mb:.2f} MB) — render failed"
            )

        logger.info(f"Final video: {output_path} ({size_mb:.1f} MB)")
        return str(output_path)

    finally:
        for c in clips:
            try:
                c.close()
            except Exception:
                pass
        if video is not None:
            try:
                video.close()
            except Exception:
                pass
        if audio is not None:
            try:
                audio.close()
            except Exception:
                pass

# ==========================================================
# MAIN
# ==========================================================

def main() -> int:

    start = time.perf_counter()

    try:
        print("\n" + "=" * 60)
        if MODE == "ai_video":
            print("CINEMATIC AI DIRECTOR — GOOGLE VEO MODE")
            print("AI Video Generation")
        else:
            print("CINEMATIC AI DIRECTOR — KEN BURNS MODE")
        print(f"MODE   : {MODE}")
        print("=" * 60)

        setup_environment()
        validate_configuration()

        if MODE == "ai_video":
            video_path = run_ai_video_pipeline()
        else:
            video_path = run_ken_burns_pipeline()

        elapsed = time.perf_counter() - start

        print("\n" + "=" * 60)
        print("VIDEO GENERATED SUCCESSFULLY")
        print("=" * 60)
        print(f"OUTPUT : {video_path}")
        print(f"TIME   : {elapsed:.1f}s")
        print("=" * 60 + "\n")

        return 0

    except KeyboardInterrupt:
        logger.warning("Interrupted by user.")
        return 130

    except Exception as e:
        logger.exception("Pipeline failed.")
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())