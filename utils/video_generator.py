"""
utils/video_generator.py

Real AI Video Generator — Google Veo (via google-genai SDK)

Image hosting: Cloudinary (free tier) — kept for upload, but Veo itself
is given the local image bytes directly (Veo does not take a Cloudinary URL).
Video generation: Google Veo
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List

import requests
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("assets/videos")


# ==========================================================
# UPLOAD LOCAL IMAGE TO CLOUDINARY → GET PUBLIC URL
# (kept available in case you still want it elsewhere, but
#  generate_via_veo no longer uses it for the Veo call itself)
# ==========================================================

def upload_to_cloudinary(image_path: str) -> str:

    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key    = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")

    if not all([cloud_name, api_key, api_secret]):
        raise ValueError(
            "Cloudinary credentials missing in .env\n"
            "  CLOUDINARY_CLOUD_NAME=xxx\n"
            "  CLOUDINARY_API_KEY=xxx\n"
            "  CLOUDINARY_API_SECRET=xxx"
        )

    logger.info(f"  Uploading {Path(image_path).name} to Cloudinary...")

    with open(image_path, "rb") as f:
        resp = requests.post(
            f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload",
            auth=(api_key, api_secret),
            files={"file": f},
            data={"folder": "freedom_fighter"},
            timeout=60,
        )

    if resp.status_code != 200:
        raise RuntimeError(
            f"Cloudinary upload failed {resp.status_code}: {resp.text}"
        )

    public_url = resp.json().get("secure_url")
    if not public_url:
        raise RuntimeError(f"No URL in Cloudinary response: {resp.json()}")

    logger.info(f"  Public URL: {public_url}")
    return public_url


# ==========================================================
# GOOGLE VEO — image to video
# ==========================================================

def generate_via_veo(
    image_path: str,
    prompt: str,
    motion: str = "slow_zoom_in",
) -> str:

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not set.\n"
            "Add to .env: GOOGLE_API_KEY=your-key\n"
            "Get key: https://aistudio.google.com/apikey"
        )

    motion_prompts = {
        "slow_zoom_in"  : "camera slowly zooms in, documentary style",
        "slow_zoom_out" : "camera slowly pulls back, cinematic reveal",
        "slow_pan_right": "camera slowly pans right, tracking shot",
        "slow_pan_left" : "camera slowly pans left, tracking shot",
        "static"        : "static camera, documentary still shot",
    }

    motion_text = motion_prompts.get(motion, "slow cinematic camera movement")
    full_prompt = (
        f"{prompt}, {motion_text}, "
        "35mm film grain, dramatic lighting, cinematic documentary"
    )

    # Step 1: build client
    client = genai.Client(api_key=api_key)

    # Step 2: load local image directly — Veo wants the file, not a URL.
    # types.Image.from_file infers the mime type for you.
    image = types.Image.from_file(location=image_path)

    logger.info("  Submitting to Google Veo...")

    operation = client.models.generate_videos(
        model="veo-3.0-fast-generate-001",
        prompt=full_prompt,
        image=image,
        config=types.GenerateVideosConfig(
            aspect_ratio="16:9",
            number_of_videos=1,
        ),
    )

    logger.info("  Generation submitted — polling...")

    # Step 3: poll until complete
    attempt = 0
    while not operation.done:
        attempt += 1
        time.sleep(10)
        operation = client.operations.get(operation)
        logger.info(f"  [{attempt}] waiting...")

    # Step 4: get the generated video object
    try:
        generated_video = operation.response.generated_videos[0]
    except (IndexError, AttributeError) as e:
        raise RuntimeError(
            f"Veo generation completed but no video found: {e}\n"
            f"Response: {operation.response}"
        )

    logger.info("  Video ready — downloading...")
    return _download_video(client, generated_video, image_path)


# ==========================================================
# DOWNLOAD COMPLETED CLIP
# Veo returns a file object, not a plain HTTP URL — must use
# client.files.download(), not requests.get().
# ==========================================================

def _download_video(client: genai.Client, generated_video, image_path: str) -> str:

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{Path(image_path).stem}.mp4"

    client.files.download(file=generated_video.video)
    generated_video.video.save(str(output_path))

    size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"  Saved: {output_path} ({size_mb:.1f} MB)")

    if size_mb < 0.1:
        raise RuntimeError(f"Video too small ({size_mb:.2f} MB)")

    return str(output_path)


# ==========================================================
# MAIN API — called by main.py
# ==========================================================

def generate_scene_videos(
    scenes: List[Dict[str, Any]],
    image_paths: List[str],
) -> List[str]:

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    video_paths : List[str] = []
    total       = len(image_paths)

    logger.info(f"Generating {total} clips via Google Veo...")

    for i, (scene, img_path) in enumerate(zip(scenes, image_paths), start=1):

        logger.info(f"\n[{i}/{total}] {scene.get('scene_id', f'scene{i}')}")

        if not Path(img_path).exists():
            raise FileNotFoundError(f"Image not found: {img_path}")

        video_path = generate_via_veo(
            image_path=img_path,
            prompt=scene.get("prompt", "cinematic documentary scene, historical India"),
            motion=scene.get("motion", "slow_zoom_in"),
        )

        video_paths.append(video_path)
        logger.info(f"  Clip {i} done: {video_path}")

    logger.info(f"\nAll {total} clips generated.")
    return video_paths