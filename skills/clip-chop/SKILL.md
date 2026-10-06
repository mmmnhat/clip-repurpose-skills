---
name: clip-chop
description: Split compilation videos into clean individual incidents and strip blurred pillarbox/letterbox backgrounds. Use when the user wants to extract clips, split video scenes without over-cutting, remove blurred backgrounds, or restore true native aspect ratios from YouTube/TikTok compilation videos.
---

# Clip Chop

Extracts standalone incidents from compilation videos and restores their true native aspect ratios (9:16, 1:1, 4:3, 16:9) with zero blurred background and zero transition bleed.

## Features

1. **Auto-Dependency Installation**: Detects missing `ffmpeg`, `opencv-python`, `scenedetect`, `numpy`, or `yt-dlp` and installs them automatically.
2. **Anti-Bleed Accurate Seeking**:
   - Frame-accurate decoded seeking (`-i` before `-ss`).
   - Trims a 0.15s buffer (~4-5 frames) from start and end to eliminate whip-pan, fade, and dissolve transition artifacts.
3. **Multi-Checkpoint Tightest Native Crop**:
   - Samples 5 checkpoints across each incident to handle dynamic zoom changes.
   - Automatically determines the tightest bounding box across all checkpoints, guaranteeing zero blurred background leakage at any second.
   - Preserves pure native dimensions (e.g., vertical clips export as vertical, square clips as square, 16:9 as 16:9).
4. **Hardware-Accelerated Encoding**: Automatically selects `h264_videotoolbox` (Apple Silicon), `h264_nvenc` (NVIDIA), or `libx264`.

## Usage

```bash
python3 skills/clip-chop/scripts/split_unblur.py <input.mp4_or_URL> [limit]
```

Output clips are saved into `output_chop/`.
