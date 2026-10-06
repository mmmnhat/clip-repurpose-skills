#!/usr/bin/env python3
import os
import sys
import subprocess

def auto_deps():
    reqs = ["opencv-python", "numpy", "scenedetect", "yt-dlp"]
    for r in reqs:
        try:
            mod = "cv2" if r == "opencv-python" else r.replace("-", "_")
            __import__(mod)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", r])

auto_deps()

import importlib.util

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
split_mod = load_module("split_unblur", os.path.join(base_dir, "clip-chop/scripts/split_unblur.py"))
remix_mod = load_module("transform", os.path.join(base_dir, "clip-remix/scripts/transform.py"))

split_and_unblur = split_mod.split_and_unblur
remix_clip = remix_mod.remix_clip
import random

def run_all(source, out_dir="output_repurposed", limit=10, transform=True):
    os.makedirs(out_dir, exist_ok=True)
    
    # If source is YouTube URL, download first
    video_file = source
    if source.startswith("http://") or source.startswith("https://"):
        print(f"Downloading {source}...")
        video_file = "downloaded_input.mp4"
        subprocess.check_call(["python3", "-m", "yt_dlp", "-f", "bv*[height<=720]+ba/b", "--merge-output-format", "mp4", source, "-o", video_file])

    temp_chop = os.path.join(out_dir, "raw_chops")
    chopped_files = split_and_unblur(video_file, out_dir=temp_chop, limit=limit)
    
    final_files = []
    if transform:
        print(f"\nApplying 2-tier transform to {len(chopped_files)} clips...")
        for i, f in enumerate(chopped_files):
            base = os.path.basename(f)
            dst = os.path.join(out_dir, f"remix_{base}")
            spd = random.uniform(0.97, 1.03)
            deg = random.choice([-2.0, 2.0])
            remix_clip(f, dst, speed=spd, rotate_deg=deg)
            final_files.append(dst)
            print(f"  ✓ [{i+1}/{len(chopped_files)}] {os.path.basename(dst)}")
    else:
        final_files = chopped_files

    print(f"\nDone! {len(final_files)} clips ready in '{out_dir}'.")
    return final_files

if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else 'full_video.mp4'
    lim = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    run_all(src, limit=lim)
