"""
install_ffmpeg_python.py
Run: python install_ffmpeg_python.py
"""

import subprocess
import sys

print("Installing imageio-ffmpeg...")
subprocess.check_call([
    sys.executable, "-m", "pip", "install",
    "imageio-ffmpeg", "--upgrade"
])

import imageio_ffmpeg
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
print(f"ffmpeg found at: {ffmpeg_path}")

# Write patch WITHOUT emojis to avoid Windows cp1252 error
patch = (
    "# ffmpeg_patch.py - auto-generated\n"
    "import os\n"
    "import moviepy.config as _cfg\n"
    f'_cfg.FFMPEG_BINARY = r"{ffmpeg_path}"\n'
    "try:\n"
    "    import moviepy.config_defaults as _cd\n"
    f'    _cd.FFMPEG_BINARY = r"{ffmpeg_path}"\n'
    "except Exception:\n"
    "    pass\n"
    f'print("FFmpeg patched: {ffmpeg_path}")\n'
)

with open("ffmpeg_patch.py", "w", encoding="utf-8") as f:
    f.write(patch)

print("Created ffmpeg_patch.py")
print("Now run: python main.py")