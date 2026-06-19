"""
video_creator.py

Cinematic AI Director Engine
LOCKED TO: MoviePy 1.0.3 + Python 3.13
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from PIL import Image as PILImage

# MoviePy 1.0.3 — always use moviepy.editor
from moviepy.editor import (
    AudioFileClip,
    VideoClip,
    concatenate_videoclips,
)

# PIL LANCZOS safe for Pillow 12.x
try:
    _RESAMPLE = PILImage.LANCZOS
except AttributeError:
    _RESAMPLE = PILImage.Resampling.LANCZOS

# ==========================================================
# CONFIG
# ==========================================================

OUTPUT_DIR   = Path("output")
OUTPUT_VIDEO = "freedom_fighter_video.mp4"

FPS         = 24
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"

TARGET_W = 1280
TARGET_H = 720

DEFAULT_SCENE_DURATION     = 4.0
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# ==========================================================
# LOGGER
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ==========================================================
# SETUP
# ==========================================================

def create_output_directory() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================================
# VALIDATION
# ==========================================================

def validate_inputs(image_paths: List[str], audio_path: str) -> None:

    if not image_paths:
        raise ValueError("No images provided.")

    for p in image_paths:
        path = Path(p)
        if not path.exists():
            raise FileNotFoundError(f"Missing image: {p}")
        if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            raise ValueError(f"Unsupported format: {path.name}")
        if path.stat().st_size == 0:
            raise ValueError(f"Empty image file: {p}")

    audio = Path(audio_path)
    if not audio.exists():
        raise FileNotFoundError(f"Missing audio: {audio_path}")
    if audio.stat().st_size == 0:
        raise ValueError("Audio file is empty.")

# ==========================================================
# IMAGE LOADER
# ==========================================================

def load_image(image_path: str) -> np.ndarray:
    img = PILImage.open(image_path).convert("RGB")
    img = img.resize((TARGET_W, TARGET_H), _RESAMPLE)
    return np.array(img)

# ==========================================================
# MOTION FRAME FUNCTIONS (numpy crop+resize — real Ken Burns)
# ==========================================================

def _zoom_in(img: np.ndarray, t: float, duration: float) -> np.ndarray:
    progress = t / max(duration, 0.001)
    scale    = 1.0 + 0.20 * progress
    h, w     = img.shape[:2]
    cw, ch   = int(w / scale), int(h / scale)
    x0, y0   = (w - cw) // 2, (h - ch) // 2
    cropped  = img[y0:y0+ch, x0:x0+cw]
    return np.array(PILImage.fromarray(cropped).resize((TARGET_W, TARGET_H), _RESAMPLE))

def _zoom_out(img: np.ndarray, t: float, duration: float) -> np.ndarray:
    progress = t / max(duration, 0.001)
    scale    = max(1.20 - 0.20 * progress, 1.0)
    h, w     = img.shape[:2]
    cw, ch   = int(w / scale), int(h / scale)
    x0, y0   = (w - cw) // 2, (h - ch) // 2
    cropped  = img[y0:y0+ch, x0:x0+cw]
    return np.array(PILImage.fromarray(cropped).resize((TARGET_W, TARGET_H), _RESAMPLE))

def _pan_right(img: np.ndarray, t: float, duration: float) -> np.ndarray:
    progress = t / max(duration, 0.001)
    h, w     = img.shape[:2]
    cw, ch   = int(w * 0.80), int(h * 0.80)
    x0       = int((w - cw) * progress)
    y0       = (h - ch) // 2
    cropped  = img[y0:y0+ch, x0:x0+cw]
    return np.array(PILImage.fromarray(cropped).resize((TARGET_W, TARGET_H), _RESAMPLE))

def _pan_left(img: np.ndarray, t: float, duration: float) -> np.ndarray:
    progress = t / max(duration, 0.001)
    h, w     = img.shape[:2]
    cw, ch   = int(w * 0.80), int(h * 0.80)
    x0       = int((w - cw) * (1.0 - progress))
    y0       = (h - ch) // 2
    cropped  = img[y0:y0+ch, x0:x0+cw]
    return np.array(PILImage.fromarray(cropped).resize((TARGET_W, TARGET_H), _RESAMPLE))

def _static(img: np.ndarray, t: float, duration: float) -> np.ndarray:
    return img

MOTION_FN = {
    "slow_zoom_in"   : _zoom_in,
    "zoom_in"        : _zoom_in,
    "slow_zoom_out"  : _zoom_out,
    "zoom_out"       : _zoom_out,
    "slow_pan_right" : _pan_right,
    "pan_right"      : _pan_right,
    "slow_pan_left"  : _pan_left,
    "pan_left"       : _pan_left,
    "static"         : _static,
    "none"           : _static,
}

# ==========================================================
# BUILD ONE CINEMATIC SCENE CLIP (MoviePy 1.0.3 compatible)
# ==========================================================

def build_scene_clip(
    image_path: str,
    duration: float,
    motion: str = "slow_zoom_in",
) -> VideoClip:

    img       = load_image(image_path)
    motion_fn = MOTION_FN.get(motion.lower().strip(), _zoom_in)

    def make_frame(t: float) -> np.ndarray:
        return motion_fn(img, t, duration)

    # MoviePy 1.0.3: set_fps (not with_fps)
    clip = VideoClip(make_frame, duration=duration)
    clip = clip.set_fps(FPS)

    return clip

# ==========================================================
# DURATION RESOLVER
# ==========================================================

def resolve_durations(
    image_paths: List[str],
    timeline: Optional[List[Dict[str, Any]]],
    audio_duration: float,
) -> List[float]:

    n = len(image_paths)

    if not audio_duration or audio_duration <= 0:
        audio_duration = n * DEFAULT_SCENE_DURATION

    if timeline and len(timeline) == n:
        logger.info("Using cinematic timeline durations.")
        return [float(s.get("duration", DEFAULT_SCENE_DURATION)) for s in timeline]

    equal = max(audio_duration / n, DEFAULT_SCENE_DURATION)
    logger.info(f"Equal duration fallback: {equal:.2f}s/scene")
    return [equal] * n

# ==========================================================
# MAIN: CREATE VIDEO
# ==========================================================

def create_video(
    image_paths: List[str],
    audio_path: str,
    timeline: Optional[List[Dict[str, Any]]] = None,
) -> str:

    validate_inputs(image_paths, audio_path)
    create_output_directory()

    output_path  = OUTPUT_DIR / OUTPUT_VIDEO
    audio_clip   : Optional[AudioFileClip] = None
    video        : Optional[VideoClip]     = None
    clips        : List[VideoClip]         = []

    try:

        # --- AUDIO ---
        logger.info("Loading narration audio...")
        audio_clip     = AudioFileClip(audio_path)
        audio_duration = audio_clip.duration or 0.0

        if audio_duration <= 0:
            raise ValueError("Invalid audio duration.")

        logger.info(f"Audio: {audio_duration:.2f}s | Scenes: {len(image_paths)}")

        # --- DURATIONS ---
        durations = resolve_durations(image_paths, timeline, audio_duration)

        # --- BUILD CLIPS ---
        logger.info("Building cinematic scene clips...")

        for i, (img_path, dur) in enumerate(zip(image_paths, durations)):

            motion = "slow_zoom_in"
            if timeline and i < len(timeline):
                motion = timeline[i].get("motion", "slow_zoom_in")

            logger.info(
                f"  [{i+1}/{len(image_paths)}] "
                f"{Path(img_path).name} | {dur:.2f}s | {motion}"
            )

            clip = build_scene_clip(img_path, dur, motion)
            clips.append(clip)

        if not clips:
            raise RuntimeError("No clips generated.")

        # --- ASSEMBLE ---
        logger.info("Assembling film timeline...")
        video = concatenate_videoclips(clips, method="compose")

        # --- BIND AUDIO (MoviePy 1.0.3: set_audio) ---
        video = video.set_audio(audio_clip)

        # --- RENDER ---
        logger.info(f"Rendering {TARGET_W}x{TARGET_H} @ {FPS}fps...")

        video.write_videofile(
            str(output_path),
            fps=FPS,
            codec=VIDEO_CODEC,
            audio_codec=AUDIO_CODEC,
            threads=4,
            logger=None,            # suppress MoviePy 1.x progress spam
        )

        # --- VERIFY ---
        if not output_path.exists():
            raise RuntimeError("Video file not created.")
        if output_path.stat().st_size < 10_000:
            raise RuntimeError(
                f"Video file too small ({output_path.stat().st_size} bytes) "
                "— ffmpeg may not be installed correctly."
            )

        logger.info(f"Video saved -> {output_path}")
        return str(output_path)

    finally:
        if video is not None:
            try:
                video.close()
            except Exception:
                pass
        if audio_clip is not None:
            try:
                audio_clip.close()
            except Exception:
                pass
        for c in clips:
            if c is not None:
                try:
                    c.close()
                except Exception:
                    pass