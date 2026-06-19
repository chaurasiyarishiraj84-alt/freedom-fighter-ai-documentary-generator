"""
tts_generator.py

Generate narration audio from script text
using Google Text-to-Speech (gTTS).
"""

import logging
import time
from pathlib import Path

from gtts import gTTS
from gtts.tts import gTTSError


# ==========================================================
# CONFIGURATION
# ==========================================================

OUTPUT_DIR = Path("assets/audio")

OUTPUT_FILE = "narration.mp3"

LANGUAGE = "en"

SLOW_SPEECH = False

MAX_RETRIES = 3

RETRY_DELAY = 2


# ==========================================================
# LOGGER
# ==========================================================

logger = logging.getLogger(__name__)


# ==========================================================
# DIRECTORY
# ==========================================================

def create_output_directory() -> None:
    """
    Ensure audio directory exists.
    """

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


# ==========================================================
# VALIDATION
# ==========================================================

def validate_script(
    script: str
) -> str:
    """
    Validate narration text.

    Returns cleaned script.
    """

    if not isinstance(
        script,
        str
    ):
        raise TypeError(
            "Narration script must be a string."
        )

    cleaned_script = script.strip()

    if not cleaned_script:

        raise ValueError(
            "Narration script is empty."
        )

    if len(cleaned_script) < 10:

        raise ValueError(
            "Narration script is too short."
        )

    return cleaned_script


# ==========================================================
# SPEECH GENERATION
# ==========================================================

def generate_speech(
    script: str,
    output_path: Path
) -> None:
    """
    Generate narration MP3.
    """

    last_error = None

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            logger.info(
                f"TTS Attempt {attempt}"
            )

            tts = gTTS(
                text=script,
                lang=LANGUAGE,
                slow=SLOW_SPEECH
            )

            tts.save(
                str(output_path)
            )

            if not output_path.exists():

                raise RuntimeError(
                    "Audio file was not created."
                )

            if output_path.stat().st_size == 0:

                raise RuntimeError(
                    "Generated audio file is empty."
                )

            logger.info(
                f"Audio saved -> "
                f"{output_path}"
            )

            return

        except (
            gTTSError,
            RuntimeError,
            OSError
        ) as error:

            last_error = error

            logger.warning(
                f"TTS attempt "
                f"{attempt} failed: "
                f"{error}"
            )

            if output_path.exists():

                try:
                    output_path.unlink()
                except OSError:
                    pass

            time.sleep(
                RETRY_DELAY
            )

    raise RuntimeError(
        "Failed to generate narration "
        "after all retry attempts."
    ) from last_error


# ==========================================================
# MAIN API
# ==========================================================

def generate_narration(
    script: str
) -> str:
    """
    Generate narration audio file.

    Args:
        script:
            Narration text.

    Returns:
        Path to generated MP3.
    """

    cleaned_script = validate_script(
        script
    )

    create_output_directory()

    output_path = (
        OUTPUT_DIR /
        OUTPUT_FILE
    )

    logger.info(
        "Starting narration generation..."
    )

    generate_speech(
        cleaned_script,
        output_path
    )

    logger.info(
        "Narration generation completed."
    )

    return str(
        output_path
    )