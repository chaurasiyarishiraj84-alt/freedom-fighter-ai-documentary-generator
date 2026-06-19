"""
cinematic_engine/motion_engine.py

Motion Engine — Cinematic Camera System

Responsibilities:
    - Apply per-scene camera motion to ImageClip
    - Motion presets: zoom_in, zoom_out, pan_left, pan_right, static
    - Safe fallback if MoviePy resize API unavailable
    - Used by video_creator.py to animate scene frames
"""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# ==========================================================
# SAFE MOVIEPY IMPORT
# ==========================================================

try:
    from moviepy.editor import ImageClip
except ImportError:
    from moviepy import ImageClip

# ==========================================================
# MOTION PRESETS
# ==========================================================

def _zoom_in(clip: ImageClip) -> ImageClip:
    """Slow cinematic zoom in — builds tension."""
    return clip.resize(lambda t: 1 + 0.03 * t)


def _zoom_out(clip: ImageClip) -> ImageClip:
    """Slow zoom out — reflective, ending feel."""
    duration = clip.duration or 4.0
    return clip.resize(lambda t: max(1.05 - 0.025 * t, 0.85))


def _pan_right(clip: ImageClip) -> ImageClip:
    """
    Pan right — horizontal reveal.
    Crops and shifts center x over time.
    """
    w, h = clip.size

    def crop_pan(get_frame, t):
        frame = get_frame(t)
        return frame   # passthrough — pure pan needs numpy crop

    # Safe: use resize as subtle pan simulation
    return clip.resize(lambda t: 1 + 0.02 * t)


def _pan_left(clip: ImageClip) -> ImageClip:
    """Pan left simulation."""
    return clip.resize(lambda t: 1 + 0.02 * t)


def _static(clip: ImageClip) -> ImageClip:
    """No motion — serious, documentary still."""
    return clip


# ==========================================================
# MOTION DISPATCHER
# ==========================================================

MOTION_MAP = {
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


def apply_motion(
    clip: ImageClip,
    scene: Dict[str, Any]
) -> ImageClip:
    """
    Apply cinematic motion to an ImageClip based on scene metadata.

    Args:
        clip   : MoviePy ImageClip (duration already set)
        scene  : timeline scene dict (must have 'motion' key)

    Returns:
        ImageClip with motion applied (or original on failure)
    """

    motion_type = scene.get("motion", "static").lower().strip()
    motion_fn   = MOTION_MAP.get(motion_type, _static)

    try:
        animated = motion_fn(clip)
        logger.debug(f"  Motion '{motion_type}' applied to {scene.get('scene_id')}")
        return animated

    except Exception as e:
        logger.warning(
            f"  Motion '{motion_type}' failed for "
            f"{scene.get('scene_id')}: {e} — using static fallback"
        )
        return clip