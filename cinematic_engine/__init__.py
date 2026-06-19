"""
cinematic_engine/

Cinematic AI Director Engine

Modules:
    scene_analyzer  — emotion + motion intelligence
    timeline_builder— cinematic pacing + story arc
    motion_engine   — per-scene camera motion presets
    audio_sync      — narration-to-scene mapping
    subtitle_engine — SRT subtitle generation
"""

from cinematic_engine.scene_analyzer  import analyze_scenes
from cinematic_engine.timeline_builder import build_timeline
from cinematic_engine.motion_engine   import apply_motion
from cinematic_engine.audio_sync      import build_audio_sync
from cinematic_engine.subtitle_engine import generate_subtitles

__all__ = [
    "analyze_scenes",
    "build_timeline",
    "apply_motion",
    "build_audio_sync",
    "generate_subtitles",
]