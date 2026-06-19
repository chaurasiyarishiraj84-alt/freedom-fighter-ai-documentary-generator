"""
cinematic_engine/timeline_builder.py

Timeline Builder — Cinematic Director Engine

Responsibilities:
    - Build full film timeline from scenes + script
    - Compute absolute start/end times per scene
    - Apply story arc pacing (intro → rise → climax → outro)
    - Feed structured timeline to video_creator + audio_sync
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from cinematic_engine.scene_analyzer import analyze_scenes

logger = logging.getLogger(__name__)

# ==========================================================
# STORY ARC PACING MULTIPLIERS
# Adjusts scene duration based on position in story arc
# ==========================================================

def arc_multiplier(index: int, total: int) -> float:
    """
    Apply documentary story arc timing:
        - Intro (first)       : slightly slower  (1.15x)
        - Rising action (25%) : normal           (1.00x)
        - Climax    (50-75%)  : slightly faster  (0.90x)
        - Outro (last)        : slowest          (1.25x)
    """
    ratio = index / max(total - 1, 1)

    if index == 0:
        return 1.15         # intro — let audience settle
    elif index == total - 1:
        return 1.25         # outro — emotional landing
    elif ratio < 0.35:
        return 1.00         # rising action — steady pace
    elif ratio < 0.70:
        return 0.90         # climax — faster cuts
    else:
        return 1.05         # resolution — slowing down


# ==========================================================
# BUILD TIMELINE
# ==========================================================

def build_timeline(
    scenes: List[Dict[str, Any]],
    script: str
) -> List[Dict[str, Any]]:
    """
    Main API — called by main.py

    Input:
        scenes  : raw SCENES list from prompts.py
        script  : SCRIPT narration string

    Output:
        List of enriched timeline dicts, each containing:
            scene_id, story, emotion, energy,
            motion, camera, visual_style,
            duration, start, end,
            importance, keywords,
            image_file, prompt
    """

    if not scenes:
        raise ValueError("Cannot build timeline: no scenes provided.")

    if not script or not script.strip():
        raise ValueError("Cannot build timeline: empty script.")

    # Step 1: Analyze scenes (emotion, energy, motion)
    analyzed = analyze_scenes(scenes)

    total          = len(analyzed)
    timeline       : List[Dict[str, Any]] = []
    cursor         = 0.0

    logger.info(f"🎬 Building cinematic timeline for {total} scenes...")

    for i, scene in enumerate(analyzed):

        # Step 2: Apply story arc pacing to base duration
        base_duration  = scene["duration"]
        arc_mult       = arc_multiplier(i, total)
        final_duration = round(base_duration * arc_mult, 2)

        start = round(cursor, 3)
        end   = round(cursor + final_duration, 3)

        # Step 3: Assemble timeline entry
        entry: Dict[str, Any] = {
            # identity
            "scene_id"    : scene["scene_id"],
            "image_file"  : scene.get("image_file", f"scene{i+1}.jpg"),

            # story
            "story"       : scene.get("story", ""),
            "prompt"      : scene.get("prompt", ""),

            # cinematic intelligence
            "emotion"     : scene["emotion"],
            "energy"      : scene["energy"],
            "motion"      : scene["motion"],
            "camera"      : scene.get("camera", "medium shot"),
            "visual_style": scene["visual_style"],
            "importance"  : scene["importance"],
            "keywords"    : scene["keywords"],

            # timing
            "duration"    : final_duration,
            "start"       : start,
            "end"         : end,
        }

        timeline.append(entry)
        cursor = end

        logger.info(
            f"  [{i+1}/{total}] {entry['scene_id']} | "
            f"{entry['emotion']:10s} | "
            f"{entry['duration']:.2f}s | "
            f"{start:.2f}s → {end:.2f}s"
        )

    total_duration = round(cursor, 2)
    logger.info(f"✅ Timeline built — total duration: {total_duration}s")

    return timeline