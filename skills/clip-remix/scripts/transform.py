#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import random

def get_vcodec():
    try:
        res = subprocess.run(["ffmpeg", "-encoders"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        if "h264_videotoolbox" in res.stdout:
            return "h264_videotoolbox"
        if "h264_nvenc" in res.stdout:
            return "h264_nvenc"
    except Exception:
        pass
    return "libx264"

def remix_clip(input_path, output_path, speed=1.02, rotate_deg=2.0, crop_ratio=0.82):
    """
    Applies Tier 1 (Geometry: hflip, rotate 1.5-2.5°, deep crop 18%) 
    and Tier 2 (Temporal: optical flow motion retiming, audio atempo).
    """
    if not shutil.which("ffmpeg"):
        sys.exit("Error: 'ffmpeg' not found on PATH.")
        
    rad = rotate_deg * 3.14159265 / 180.0
    vf = (
        f"[0:v]hflip,"
        f"rotate={rad}:ow=rotw({rad}):oh=roth({rad}):fillcolor=black,"
        f"crop=trunc(iw*{crop_ratio}/2)*2:trunc(ih*{crop_ratio}/2)*2,"
        f"setpts=PTS/{speed},"
        f"minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc[v];"
        f"[0:a]atempo={speed}[a]"
    )
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-filter_complex', vf,
        '-map', '[v]', '-map', '[a]',
        '-c:v', get_vcodec(), '-b:v', '3500k',
        '-c:a', 'aac', output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path

if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else 'input.mp4'
    dst = sys.argv[2] if len(sys.argv) > 2 else 'output.mp4'
    spd = random.uniform(0.97, 1.03)
    deg = random.choice([-2.0, 2.0])
    remix_clip(src, dst, speed=spd, rotate_deg=deg)
    print(f"✓ Remixed {src} -> {dst} (speed={spd:.2f}, rot={deg}°)")
