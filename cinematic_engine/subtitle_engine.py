"""
cinematic_engine/subtitle_engine.py

Subtitle Engine — Documentary Layer

Responsibilities:
    - Split narration SCRIPT into subtitle segments
    - Align segments to scene timeline timing
    - Export .srt subtitle file
    - Optional: burn subtitles into video (future)
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# ==========================================================
# SRT TIME FORMATTER
# ==========================================================

def seconds_to_srt(seconds: float) -> str:
    """
    Convert float seconds to SRT timestamp.
    Format: HH:MM:SS,mmm
    """
    hours   = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs    = int(seconds % 60)
    millis  = int(round((seconds % 1) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


# ==========================================================
# SCRIPT SPLITTER
# ==========================================================

def split_script(
    script: str,
    n_segments: int
) -> List[str]:
    """
    Split narration script into n_segments chunks.

    Strategy:
        1. Split by sentences first
        2. Group into n_segments evenly
        3. Fallback: word-level split
    """

    # Clean script
    script = script.strip()

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', script)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        # Fallback: word split
        words     = script.split()
        chunk     = max(1, len(words) // n_segments)
        sentences = [
            " ".join(words[i:i+chunk])
            for i in range(0, len(words), chunk)
        ]

    # Group sentences into n_segments
    total     = len(sentences)
    segments  : List[str] = []

    if total <= n_segments:
        # Pad with empty if fewer sentences than scenes
        for i in range(n_segments):
            segments.append(sentences[i] if i < total else "")
    else:
        # Group multiple sentences per segment
        per_seg = total / n_segments
        for i in range(n_segments):
            start = int(i * per_seg)
            end   = int((i + 1) * per_seg)
            segments.append(" ".join(sentences[start:end]))

    return segments


# ==========================================================
# GENERATE SUBTITLES
# ==========================================================

def generate_subtitles(
    script: str,
    timeline: List[Dict[str, Any]],
    output_path: str = "output/subtitles.srt"
) -> str:
    """
    Generate .srt subtitle file aligned to cinematic timeline.

    Args:
        script      : full narration SCRIPT string
        timeline    : enriched timeline from build_timeline()
        output_path : where to save .srt file

    Returns:
        Path to generated .srt file
    """

    if not script.strip():
        raise ValueError("Empty script — cannot generate subtitles.")

    if not timeline:
        raise ValueError("Empty timeline — cannot generate subtitles.")

    n           = len(timeline)
    segments    = split_script(script, n)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"📝 Generating {n} subtitle segments...")

    srt_lines: List[str] = []

    for i, (scene, text) in enumerate(zip(timeline, segments), start=1):

        if not text.strip():
            continue

        start_ts = seconds_to_srt(scene["start"])
        end_ts   = seconds_to_srt(scene["end"])

        srt_lines.append(str(i))
        srt_lines.append(f"{start_ts} --> {end_ts}")
        srt_lines.append(text.strip())
        srt_lines.append("")   # blank line between entries

        logger.info(
            f"  [{i}] {scene['scene_id']} | "
            f"{scene['start']:.2f}→{scene['end']:.2f}s | "
            f"{text[:50]}..."
        )

    srt_content = "\n".join(srt_lines)
    output_file.write_text(srt_content, encoding="utf-8")

    logger.info(f"✅ Subtitles saved → {output_file}")

    return str(output_file)