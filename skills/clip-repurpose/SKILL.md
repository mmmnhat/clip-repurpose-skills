---
name: clip-repurpose
description: All-in-one video re-purposing pipeline. Automatically downloads videos from URL or local file, splits incidents without over-cutting, strips blurred backgrounds, and applies 2-tier geometric + optical flow transformations. Use when the user wants an automated end-to-end clip extraction and remixing workflow.
---

# Clip Repurpose (All-In-One Pipeline)

Fully automated pipeline connecting download, incident splitting, unblur cropping, and 2-tier anti-fingerprint transformations.

## Pipeline Architecture

`URL / Local File -> Auto-Install Dependencies -> Incident Splitting (Correlation Guard) -> Exact Seam Unblur -> 2-Tier Transform (Tier 1 Geometry + Tier 2 Optical Flow) -> Export`

## Usage

```bash
python3 skills/clip-repurpose/scripts/pipeline.py <video_url_or_file> [limit]
```

### Examples

```bash
# Process 5 clips from a local file
python3 skills/clip-repurpose/scripts/pipeline.py full_video.mp4 5

# Process 10 clips directly from YouTube
python3 skills/clip-repurpose/scripts/pipeline.py "https://youtu.be/..." 10
```

- Raw cropped clips are saved in: `output_repurposed/raw_chops/`
- Final transformed clips are saved in: `output_repurposed/`
