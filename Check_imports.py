"""
check_imports.py
Run this in your project root to see EXACTLY which files are loading
"""
import sys
from pathlib import Path

print("\n" + "="*60)
print("IMPORT TRACE")
print("="*60)

# 1. Which video_creator.py is actually being loaded?
print("\n[1] video_creator.py location:")
try:
    import utils.video_creator as vc
    print(f"    Loading from: {vc.__file__}")
    
    # Check if it has build_scene_clip (new) or create_image_clips (old)
    if hasattr(vc, 'build_scene_clip'):
        print("    Version: ✅ NEW (real Ken Burns motion)")
    elif hasattr(vc, 'create_image_clips'):
        print("    Version: ❌ OLD (static ImageClip) — this is why output looks same!")
    else:
        print("    Version: ❓ Unknown")
except Exception as e:
    print(f"    ERROR: {e}")

# 2. MoviePy version
print("\n[2] MoviePy being used:")
try:
    import moviepy
    print(f"    Version: {moviepy.__version__}")
    print(f"    Path: {moviepy.__file__}")
except Exception as e:
    print(f"    ERROR: {e}")

# 3. Check if __pycache__ has stale .pyc files
print("\n[3] Stale cache check:")
cache_dirs = list(Path(".").rglob("__pycache__"))
pyc_files  = list(Path(".").rglob("*.pyc"))
print(f"    __pycache__ dirs: {len(cache_dirs)}")
print(f"    .pyc files: {len(pyc_files)}")
if pyc_files:
    print("    ⚠️  Stale cache may be loading OLD code!")
    print("    Fix: python check_imports.py will show — then delete __pycache__")

# 4. Show utils/ folder contents
print("\n[4] utils/ folder contents:")
utils_dir = Path("utils")
if utils_dir.exists():
    for f in sorted(utils_dir.iterdir()):
        size_kb = f.stat().st_size / 1024
        print(f"    {f.name:30s} {size_kb:6.1f} KB")
else:
    print("    ❌ utils/ folder not found!")

# 5. Check video_creator.py first few lines
print("\n[5] Your current video_creator.py (first 20 lines):")
vc_path = Path("utils/video_creator.py")
if vc_path.exists():
    lines = vc_path.read_text().split("\n")[:20]
    for i, line in enumerate(lines, 1):
        print(f"    {i:3d}: {line}")
else:
    print("    ❌ utils/video_creator.py NOT FOUND")

print("\n" + "="*60 + "\n")