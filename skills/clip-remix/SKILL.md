---
name: clip-remix
description: Apply 2-tier video transformations (geometric distortion + temporal optical flow retiming) to alter video fingerprints. Use when the user wants to re-purpose video, bypass fingerprint detection, deep crop, rotate, flip, or retime video using motion-compensated optical flow.
---

# Clip Remix

Applies two-tier transformations to make clips unique against automated content fingerprinting:

## Tier 1: Geometric Distortion
- **Horizontal Flip (`hflip`)**: Inverts spatial coordinates.
- **Subtle Rotation (1.5° - 2.5°)**: Tilts horizons and vertical lines with zero letterbox gap.
- **Deep Crop (15% - 20%)**: Crops static background and edges where matching algorithms focus.
- **Dimension Safety**: Automatically truncates crop width/height to even dimensions for codec compatibility.

## Tier 2: Temporal Disruption
- **Optical Flow Motion Vector Retiming**: Re-synthesizes every single frame using FFmpeg `minterpolate` (AOBMC mode, 97% - 103% speed), ensuring no frame matches the original source.
- **Pitch-Preserving Audio Retiming**: Retimes audio using `atempo` to stay synchronized without pitch shift.

## Usage

```bash
python3 skills/clip-remix/scripts/transform.py <input_clip.mp4> <output_clip.mp4>
```
