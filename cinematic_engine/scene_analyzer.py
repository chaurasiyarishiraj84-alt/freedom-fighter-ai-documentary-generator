"""
cinematic_engine/scene_analyzer.py

Scene Analyzer — AI Film Director Brain

Responsibilities:
    - Detect emotion from scene prompt + metadata
    - Assign energy level (0.0 → 1.0)
    - Suggest cinematic camera motion
    - Tag visual style per scene
    - Feed intelligence to timeline_builder
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# ==========================================================
# EMOTION KEYWORD MAP
# ==========================================================

EMOTION_KEYWORDS: Dict[str, List[str]] = {
    "intense": [
        "fight", "resist", "revolution", "struggle",
        "battle", "protest", "confrontation", "arrested",
        "charge", "British", "colonist", "defiant", "jail"
    ],
    "serious": [
        "court", "trial", "sentence", "history",
        "document", "speech", "declaration", "execution",
        "gallows", "sacrifice", "planning", "reading"
    ],
    "patriotic": [
        "flag", "independence", "freedom", "nation",
        "India", "patriot", "hero", "martyr", "salute",
        "tricolor", "motherland", "pride"
    ],
    "hopeful": [
        "sunrise", "dawn", "future", "youth",
        "dream", "light", "legacy", "inspire",
        "tribute", "remember", "symbol", "arise"
    ],
    "calm": [
        "reading", "meditation", "writing", "letter",
        "family", "village", "childhood", "young"
    ],
}

# ==========================================================
# MOTION MAP (emotion → camera motion)
# ==========================================================

EMOTION_TO_MOTION: Dict[str, str] = {
    "intense"   : "slow_zoom_in",
    "serious"   : "static",
    "patriotic" : "slow_zoom_out",
    "hopeful"   : "slow_zoom_in",
    "calm"      : "slow_pan_right",
}

# ==========================================================
# ENERGY MAP (emotion → energy level 0.0–1.0)
# ==========================================================

EMOTION_TO_ENERGY: Dict[str, float] = {
    "intense"   : 0.90,
    "serious"   : 0.65,
    "patriotic" : 0.80,
    "hopeful"   : 0.70,
    "calm"      : 0.40,
}

# ==========================================================
# VISUAL STYLE MAP
# ==========================================================

EMOTION_TO_VISUAL: Dict[str, str] = {
    "intense"   : "dark tones, high contrast, dramatic shadows",
    "serious"   : "neutral tones, documentary grain, cool light",
    "patriotic" : "warm golden tones, flag colors, epic lighting",
    "hopeful"   : "golden hour, soft glow, uplifting atmosphere",
    "calm"      : "soft natural light, warm browns, intimate frame",
}

# ==========================================================
# DURATION MAP (energy → base duration seconds)
# High energy = shorter (faster pace)
# Low energy  = longer  (slower, reflective)
# ==========================================================

def energy_to_duration(energy: float) -> float:
    if energy >= 0.85:
        return 4.0
    elif energy >= 0.70:
        return 5.0
    elif energy >= 0.50:
        return 5.5
    else:
        return 6.0


# ==========================================================
# CORE: DETECT EMOTION
# ==========================================================

def detect_emotion(scene: Dict[str, Any]) -> str:
    """
    Detect dominant emotion from scene prompt + existing tags.
    Priority: explicit 'emotion' field > keyword detection > default
    """

    # 1. Use explicit emotion if already set in prompts.py
    if scene.get("emotion"):
        return scene["emotion"].lower().strip()

    # 2. Keyword detection from prompt
    prompt = scene.get("prompt", "").lower()

    scores: Dict[str, int] = {emotion: 0 for emotion in EMOTION_KEYWORDS}

    for emotion, keywords in EMOTION_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in prompt:
                scores[emotion] += 1

    best_emotion = max(scores, key=lambda e: scores[e])

    if scores[best_emotion] > 0:
        return best_emotion

    # 3. Default fallback
    return "serious"


# ==========================================================
# CORE: ANALYZE ONE SCENE
# ==========================================================

def analyze_scene(
    scene: Dict[str, Any],
    index: int,
    total: int
) -> Dict[str, Any]:
    """
    Enrich a single scene with cinematic intelligence.

    Returns the original scene dict + analysis fields:
        emotion, energy, motion, visual_style,
        duration, importance, keywords
    """

    emotion     = detect_emotion(scene)
    energy      = EMOTION_TO_ENERGY.get(emotion, 0.65)
    motion      = scene.get("motion") or EMOTION_TO_MOTION.get(emotion, "static")
    visual      = EMOTION_TO_VISUAL.get(emotion, "cinematic documentary")
    duration    = scene.get("duration") or energy_to_duration(energy)

    # Importance: first and last scenes are highest
    if index == 0 or index == total - 1:
        importance = "high"
    elif energy >= 0.80:
        importance = "high"
    elif energy >= 0.60:
        importance = "medium"
    else:
        importance = "low"

    # Extract keywords from prompt
    prompt_words = scene.get("prompt", "").lower().split()
    stop_words   = {"a", "an", "the", "of", "in", "on", "at", "with", "and", "or"}
    keywords     = [w for w in prompt_words if len(w) > 4 and w not in stop_words][:5]

    analyzed = {
        **scene,                         # keep all original fields
        "emotion"     : emotion,
        "energy"      : round(energy, 2),
        "motion"      : motion,
        "visual_style": visual,
        "duration"    : float(duration),
        "importance"  : importance,
        "keywords"    : keywords,
    }

    return analyzed


# ==========================================================
# MAIN API: ANALYZE ALL SCENES
# ==========================================================

def analyze_scenes(
    scenes: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Analyze all scenes and return enriched list.

    Input:  raw SCENES from prompts.py
    Output: enriched scene list with emotion/motion/duration tags
    """

    if not scenes:
        raise ValueError("No scenes to analyze.")

    total = len(scenes)
    analyzed: List[Dict[str, Any]] = []

    logger.info(f"🧠 Analyzing {total} scenes...")

    for i, scene in enumerate(scenes):

        result = analyze_scene(scene, index=i, total=total)

        logger.info(
            f"  [{i+1}/{total}] {scene.get('scene_id')} → "
            f"emotion={result['emotion']} | "
            f"energy={result['energy']} | "
            f"motion={result['motion']} | "
            f"duration={result['duration']}s"
        )

        analyzed.append(result)

    logger.info("✅ Scene analysis complete.")

    return analyzed