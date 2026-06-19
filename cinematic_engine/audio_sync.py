"""
cinematic_engine/audio_sync.py

Audio Sync Engine

Responsibilities:
    - Map narration audio segments to scene timeline
    - Compute per-scene audio start/end offsets
    - Detect timing mismatches between audio + video
    - Provide sync metadata to video_creator
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ==========================================================
# AUDIO DURATION READER
# ==========================================================

def get_audio_duration(audio_path: str) -> float:
    """
    Read audio file duration in seconds.
    Uses MoviePy AudioFileClip (safe, no ffprobe required).
    """

    try:
        from moviepy.editor import AudioFileClip
    except ImportError:
        from moviepy import AudioFileClip

    clip = None
    try:
        clip = AudioFileClip(audio_path)
        duration = clip.duration or 0.0
        return float(duration)
    finally:
        if clip:
            try:
                clip.close()
            except Exception:
                pass


# ==========================================================
# SYNC BUILDER
# ==========================================================

def build_audio_sync(
    timeline: List[Dict[str, Any]],
    audio_path: str
) -> List[Dict[str, Any]]:
    """
    Map audio segments to each scene in the timeline.

    Logic:
        - Compute total video duration from timeline
        - Compute audio duration
        - Proportionally map audio start/end to each scene
        - Flag mismatches (audio longer/shorter than video)

    Returns:
        List of sync dicts, one per scene:
        {
            scene_id     : str
            video_start  : float
            video_end    : float
            audio_start  : float
            audio_end    : float
            audio_ratio  : float   (1.0 = perfect sync)
        }
    """

    if not timeline:
        raise ValueError("Empty timeline — cannot build audio sync.")

    if not Path(audio_path).exists():
        raise FileNotFoundError(f"Audio not found: {audio_path}")

    audio_duration = get_audio_duration(audio_path)
    video_duration = sum(s["duration"] for s in timeline)

    if audio_duration <= 0:
        raise ValueError("Invalid audio duration.")

    ratio = audio_duration / video_duration if video_duration > 0 else 1.0

    sync_map: List[Dict[str, Any]] = []

    logger.info(
        f"🎧 Audio sync | "
        f"audio={audio_duration:.2f}s | "
        f"video={video_duration:.2f}s | "
        f"ratio={ratio:.3f}"
    )

    if ratio < 0.90:
        logger.warning(
            "Audio is shorter than video — "
            "last scenes may have silence."
        )
    elif ratio > 1.10:
        logger.warning(
            "Audio is longer than video — "
            "narration will be cut off."
        )

    for scene in timeline:

        v_start = scene["start"]
        v_end   = scene["end"]

        # Map proportionally to audio timeline
        a_start = round(v_start * ratio, 3)
        a_end   = round(v_end   * ratio, 3)

        # Clamp to audio bounds
        a_start = min(a_start, audio_duration)
        a_end   = min(a_end,   audio_duration)

        sync_map.append({
            "scene_id"   : scene["scene_id"],
            "video_start": v_start,
            "video_end"  : v_end,
            "audio_start": a_start,
            "audio_end"  : a_end,
            "audio_ratio": round(ratio, 4),
        })

        logger.info(
            f"  {scene['scene_id']} | "
            f"video {v_start:.2f}→{v_end:.2f}s | "
            f"audio {a_start:.2f}→{a_end:.2f}s"
        )

    logger.info("✅ Audio sync map complete.")

    return sync_map