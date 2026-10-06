# 🎬 Clip Repurpose Skills for AI Agents

Community Anthropic Skills for splitting long compilation videos, extracting clean native clips without blurred margin bleed, and applying mathematical 2-tier anti-fingerprinting transformations.

Designed for AI Coding Agents (Antigravity, Claude Code, Cursor) and automation pipelines.

---

## 📦 Included Skills

| Skill | Description | Location |
| :--- | :--- | :--- |
| **`clip-chop`** | Frame-accurate scene detection, unblur cropping, and SIFT RANSAC continuous incident aggregation. | [`skills/clip-chop`](skills/clip-chop) |
| **`clip-remix`** | Tier 1 (Geometry & Mirror) + Tier 2 (Optical Flow temporal synthesis) anti-fingerprint engine. | [`skills/clip-remix`](skills/clip-remix) |
| **`clip-repurpose`**| All-in-One end-to-end runner that auto-downloads, chops, and remixes video compilations. | [`skills/clip-repurpose`](skills/clip-repurpose) |

---

## ⚡ Key Highlights

### 1. Zero Blurred Background Bleed
Traditional crop algorithms assume fixed canvas shapes (like forced 16:9). `clip-chop` analyzes multi-checkpoint incident profiles using Sobel gradients and Laplacian variance contrast tests to find the **tightest unblurred bounding box** (`min_bw`, `min_bh`), exporting **pure native aspect ratios** (e.g., 9:16 vertical, 1:1 square, 4:3) with 0 blurred pixels.

### 2. SIFT + RANSAC Incident Continuity
In compilations, editors frequently cut to zoom-in replays or alternative angles of the same incident. Normal color histograms collapse on zoom shots. `clip-chop` pairs HSV color correlation with scale-invariant **SIFT + RANSAC homography verification** (with watermark masking) to seamlessly group replays and zoom cuts into **one unified incident**.

### 3. Frame-Accurate Buffer (Zero 2-3 Bleed Frames)
Eliminates whip-pan blur, cross-dissolve, and flash frame bleed by seeking post-decode (`-i` before `-ss`) and applying an automated `0.15s` (~4-5 frames @ 30fps) safety buffer on incident boundaries.

### 4. 2-Tier Mathematical Anti-Fingerprinting
* **Tier 1 (Geometry & Composition)**: 18% deep crop + 2° micro-tilt + horizontal flip.
* **Tier 2 (Temporal Synthesis)**: Dynamic speed shift (97–103%) coupled with `minterpolate` Optical Flow, synthesizing new intermediate frames so zero original frames remain indexed.

### 5. Self-Bootstrapping Dependencies
All scripts automatically verify and install missing runtime dependencies (`opencv-python`, `scenedetect`, `yt-dlp`, `numpy`) and leverage Apple Silicon hardware acceleration (`h264_videotoolbox`) when available.

---

## 🚀 Quick Start

### 1. All-in-One Pipeline
```bash
# Process a local video or YouTube URL (chops and remixes 10 incidents)
python3 skills/clip-repurpose/scripts/pipeline.py "https://youtu.be/..." 10
```

### 2. Standalone Chop (Unblur & Incident Aggregation)
```bash
python3 skills/clip-chop/scripts/split_unblur.py full_video.mp4 15
```

### 3. Standalone Remix (Anti-Fingerprint Transformation)
```bash
python3 skills/clip-remix/scripts/transform.py input_clip.mp4 output_remix.mp4
```

---

## 📄 License
MIT License. Open for community use, fork, and contribution.
