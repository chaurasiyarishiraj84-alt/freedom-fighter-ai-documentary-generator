"""
debug_pipeline.py
Run: python debug_pipeline.py
"""

import os
import sys
import subprocess
from pathlib import Path

print("\n" + "="*60)
print("PIPELINE DIAGNOSTIC")
print("="*60)

errors   = []
warnings = []

# ==========================================================
# 1. PYTHON VERSION
# ==========================================================
print(f"\n[1] Python: {sys.version}")

# ==========================================================
# 2. PACKAGES
# ==========================================================
print("\n[2] Package versions:")

packages = {
    "moviepy"       : "moviepy",
    "PIL (Pillow)"  : "PIL",
    "numpy"         : "numpy",
    "requests"      : "requests",
    "gtts"          : "gtts",
    "imageio_ffmpeg": "imageio_ffmpeg",
}

for name, mod in packages.items():
    try:
        m   = __import__(mod)
        ver = getattr(m, "__version__", "installed")
        print(f"    OK  {name:20s} {ver}")
    except ImportError:
        print(f"    MISSING  {name}")
        errors.append(f"{name} not installed — pip install {mod}")

# ==========================================================
# 3. FFMPEG CHECK (system + imageio bundle)
# ==========================================================
print("\n[3] FFmpeg check:")

ffmpeg_exe = None

# Check system ffmpeg
try:
    result = subprocess.run(
        ["ffmpeg", "-version"],
        capture_output=True, text=True, timeout=5
    )
    print(f"    System ffmpeg: OK — {result.stdout.split(chr(10))[0]}")
    ffmpeg_exe = "ffmpeg"
except FileNotFoundError:
    print("    System ffmpeg: NOT IN PATH")

# Check imageio-ffmpeg bundle
try:
    import imageio_ffmpeg
    path = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"    imageio ffmpeg: OK — {path}")
    if ffmpeg_exe is None:
        ffmpeg_exe = path
except Exception as e:
    print(f"    imageio ffmpeg: FAILED — {e}")

if ffmpeg_exe is None:
    errors.append(
        "No ffmpeg found anywhere.\n"
        "   Fix: pip install imageio-ffmpeg\n"
        "   Then: python install_ffmpeg_python.py"
    )
else:
    print(f"    Using: {ffmpeg_exe}")

# ==========================================================
# 4. MOVIEPY 1.0.3 API CHECK (correct API for 1.x)
# ==========================================================
print("\n[4] MoviePy 1.0.3 API check:")

try:
    # MoviePy 1.0.3 uses moviepy.editor — NOT moviepy root
    from moviepy.editor import VideoClip, AudioFileClip, concatenate_videoclips
    print("    moviepy.editor import: OK")

    import numpy as np

    # MoviePy 1.0.3 uses set_fps NOT with_fps
    clip = VideoClip(
        lambda t: np.zeros((100, 100, 3), dtype="uint8"),
        duration=0.5
    )
    clip = clip.set_fps(24)       # 1.0.3 API
    print("    VideoClip + set_fps(24): OK")

    # Test render using imageio ffmpeg path if available
    test_out = str(Path("output/_test.mp4"))
    Path("output").mkdir(exist_ok=True)

    # Patch ffmpeg path before write
    if ffmpeg_exe and ffmpeg_exe != "ffmpeg":
        try:
            import moviepy.config as _cfg
            _cfg.FFMPEG_BINARY = ffmpeg_exe
        except Exception:
            pass
        try:
            import moviepy.config_defaults as _cd
            _cd.FFMPEG_BINARY = ffmpeg_exe
        except Exception:
            pass

    clip.write_videofile(
        test_out,
        fps=24,
        codec="libx264",
        audio=False,
        verbose=False,
        logger=None,
    )
    clip.close()

    size = Path(test_out).stat().st_size
    if size > 5000:
        print(f"    write_videofile: OK ({size // 1024} KB)")
    else:
        print(f"    write_videofile: output too small ({size} bytes)")
        errors.append("Video render produced empty file — ffmpeg path issue")

except Exception as e:
    print(f"    FAILED: {e}")
    errors.append(f"MoviePy render test failed: {e}")

# ==========================================================
# 5. PIL LANCZOS CHECK (Pillow 12.x)
# ==========================================================
print("\n[5] PIL LANCZOS check:")

try:
    from PIL import Image as PILImage
    import numpy as np

    # Pillow 10+ moved LANCZOS to Resampling enum
    try:
        _R = PILImage.LANCZOS
        print("    PILImage.LANCZOS: OK")
    except AttributeError:
        _R = PILImage.Resampling.LANCZOS
        print("    PILImage.Resampling.LANCZOS: OK (Pillow 10+)")

    # Test actual resize
    arr    = np.zeros((100, 100, 3), dtype="uint8")
    img    = PILImage.fromarray(arr)
    resized = img.resize((200, 200), _R)
    print(f"    Resize test: OK — {resized.size}")

except Exception as e:
    print(f"    FAILED: {e}")
    errors.append(f"PIL LANCZOS issue: {e}")

# ==========================================================
# 6. FULL KEN BURNS RENDER TEST
# ==========================================================
print("\n[6] Ken Burns render test (real zoom motion):")

try:
    from PIL import Image as PILImage
    import numpy as np
    from moviepy.editor import VideoClip, concatenate_videoclips

    try:
        _R = PILImage.LANCZOS
    except AttributeError:
        _R = PILImage.Resampling.LANCZOS

    # Gradient image so zoom is visible
    img = np.zeros((720, 1280, 3), dtype="uint8")
    for x in range(1280):
        img[:, x, 0] = int(x / 1280 * 200)
    for y in range(720):
        img[y, :, 1] = int(y / 720 * 150)

    def make_frame(t):
        progress = t / 3.0
        scale    = 1.0 + 0.20 * progress
        h, w     = img.shape[:2]
        cw, ch   = int(w / scale), int(h / scale)
        x0, y0   = (w - cw) // 2, (h - ch) // 2
        cropped  = img[y0:y0+ch, x0:x0+cw]
        return np.array(
            PILImage.fromarray(cropped).resize((1280, 720), _R)
        )

    clip     = VideoClip(make_frame, duration=3.0)
    clip     = clip.set_fps(24)                    # MoviePy 1.0.3
    test_out = "output/_ken_burns_test.mp4"

    clip.write_videofile(
        test_out,
        fps=24,
        codec="libx264",
        audio=False,
        verbose=False,
        logger=None,
    )
    clip.close()

    size = Path(test_out).stat().st_size
    if size > 50_000:
        print(f"    Ken Burns render: OK — {size // 1024} KB")
        print(f"    >>> Open {test_out} to verify zoom motion <<<")
    else:
        print(f"    Ken Burns render: output too small ({size} bytes)")
        errors.append("Ken Burns test failed — empty output")

except Exception as e:
    print(f"    FAILED: {e}")
    errors.append(f"Ken Burns render: {e}")

# ==========================================================
# 7. PROJECT STRUCTURE
# ==========================================================
print("\n[7] Project structure:")

required = [
    "main.py",
    "ffmpeg_patch.py",
    "prompts/prompts.py",
    "utils/image_generator.py",
    "utils/tts_generator.py",
    "utils/video_creator.py",
    "cinematic_engine/__init__.py",
    "cinematic_engine/scene_analyzer.py",
    "cinematic_engine/timeline_builder.py",
    "cinematic_engine/motion_engine.py",
]

for f in required:
    p = Path(f)
    status = "OK     " if p.exists() else "MISSING"
    print(f"    {status}  {f}")
    if not p.exists():
        errors.append(f"Missing: {f}")

# ==========================================================
# 8. ASSETS
# ==========================================================
print("\n[8] Assets:")

img_dir   = Path("assets/images")
audio_dir = Path("assets/audio")

images = list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png")) \
         if img_dir.exists() else []
audios = list(audio_dir.glob("*")) if audio_dir.exists() else []

print(f"    Images : {len(images)}")
for im in images:
    kb = im.stat().st_size / 1024
    ok = "OK" if kb > 10 else "SMALL"
    print(f"      {ok:5s}  {im.name} ({kb:.1f} KB)")
    if kb < 10:
        errors.append(f"Image too small: {im.name} ({kb:.1f} KB)")

print(f"    Audio  : {len(audios)}")
for a in audios:
    kb = a.stat().st_size / 1024
    ok = "OK" if kb > 5 else "SMALL"
    print(f"      {ok:5s}  {a.name} ({kb:.1f} KB)")

# ==========================================================
# 9. OUTPUT
# ==========================================================
print("\n[9] Output folder:")

out_dir = Path("output")
if out_dir.exists():
    files = [f for f in out_dir.iterdir() if not f.name.startswith("_")]
    if files:
        for f in files:
            mb = f.stat().st_size / (1024 * 1024)
            print(f"    {f.name} ({mb:.2f} MB)")
            if mb < 0.01 and f.suffix == ".mp4":
                errors.append(f"Video {f.name} is empty — render failed")
    else:
        warnings.append("output/ is empty — not generated yet")
        print("    (empty)")
else:
    print("    output/ does not exist yet")

# ==========================================================
# SUMMARY
# ==========================================================
print("\n" + "="*60)
if not errors:
    print("ALL CHECKS PASSED — run: python main.py")
else:
    print(f"{len(errors)} ERROR(S) — fix these:\n")
    for i, e in enumerate(errors, 1):
        print(f"  {i}. {e}\n")

if warnings:
    print(f"{len(warnings)} warning(s):")
    for w in warnings:
        print(f"  - {w}")

print("="*60 + "\n")