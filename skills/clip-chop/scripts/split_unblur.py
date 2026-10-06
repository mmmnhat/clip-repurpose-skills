#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess

def ensure_deps():
    if not shutil.which("ffmpeg"):
        sys.exit("Error: 'ffmpeg' not found on system PATH. Please install ffmpeg.")
    required = {"cv2": "opencv-python", "numpy": "numpy", "scenedetect": "scenedetect", "yt_dlp": "yt-dlp"}
    missing = [pkg for mod, pkg in required.items() if not _has_mod(mod)]
    if missing:
        print(f"Auto-installing missing packages: {missing}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing], stdout=subprocess.DEVNULL)

def _has_mod(mod_name):
    try:
        __import__(mod_name)
        return True
    except ImportError:
        return False

ensure_deps()
import cv2
import numpy as np
import yt_dlp
from scenedetect import open_video, SceneManager, ContentDetector

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

def detect_pillar_or_letter(frame):
    h, w, _ = frame.shape
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mid_y1, mid_y2 = int(h * 0.20), int(h * 0.80)

    # 1. Check Pillarbox (blur on left & right sides)
    margin_l = gray[mid_y1:mid_y2, 30:120]
    margin_r = gray[mid_y1:mid_y2, w - 120:w - 30]
    center_roi = gray[mid_y1:mid_y2, int(w * 0.40):int(w * 0.60)]

    var_l = cv2.Laplacian(margin_l, cv2.CV_64F).var()
    var_r = cv2.Laplacian(margin_r, cv2.CV_64F).var()
    var_c = cv2.Laplacian(center_roi, cv2.CV_64F).var()
    blur_ratio = var_c / (max(var_l, var_r) + 1e-5)

    if blur_ratio >= 8.0 and max(var_l, var_r) <= 20.0:
        sobel_x = np.abs(cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3))
        col_energy = np.mean(sobel_x[mid_y1:mid_y2, :], axis=0)

        left_band = col_energy[100:w // 2 - 40]
        left_peak = 100 + int(np.argmax(left_band))
        right_band = col_energy[w // 2 + 40:w - 100]
        right_peak = (w // 2 + 40) + int(np.argmax(right_band))

        symmetry = abs((w - right_peak) - left_peak)
        if symmetry <= 8 and col_energy[left_peak] > 30 and col_energy[right_peak] > 30:
            x1 = ((left_peak + 2) // 2) * 2
            x2 = ((right_peak - 2) // 2) * 2
            bw = ((x2 - x1) // 2) * 2
            return True, (x1, 0, bw, h)

    # 2. Check Letterbox (blur on top & bottom)
    mid_x1, mid_x2 = int(w * 0.20), int(w * 0.80)
    margin_t = gray[20:80, mid_x1:mid_x2]
    margin_b = gray[h - 80:h - 20, mid_x1:mid_x2]
    var_t = cv2.Laplacian(margin_t, cv2.CV_64F).var()
    var_b = cv2.Laplacian(margin_b, cv2.CV_64F).var()
    blur_ratio_y = var_c / (max(var_t, var_b) + 1e-5)

    if blur_ratio_y >= 8.0 and max(var_t, var_b) <= 20.0:
        sobel_y = np.abs(cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3))
        row_energy = np.mean(sobel_y[:, mid_x1:mid_x2], axis=1)

        top_peak = 40 + int(np.argmax(row_energy[40:h // 2 - 30]))
        bot_peak = (h // 2 + 30) + int(np.argmax(row_energy[h // 2 + 30:h - 40]))

        symmetry_y = abs((h - bot_peak) - top_peak)
        if symmetry_y <= 8 and row_energy[top_peak] > 30 and row_energy[bot_peak] > 30:
            y1 = ((top_peak + 2) // 2) * 2
            y2 = ((bot_peak - 2) // 2) * 2
            bh = ((y2 - y1) // 2) * 2
            return True, (0, y1, w, bh)

    return False, (0, 0, w, h)

def get_hsv_hist(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [16, 16], [0, 180, 0, 256])
    return cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)

def resolve_video_source(src):
    if src.startswith("http://") or src.startswith("https://"):
        print(f"Downloading stream from {src}...")
        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": "source_download.%(ext)s",
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([src])
        return "source_download.mp4"
    return src

def analyze_incident_profile(cap, start_sec, end_sec, num_samples=5):
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    dur = end_sec - start_sec

    blurred_boxes = []
    has_any_blur = False

    for i in range(num_samples):
        t = start_sec + dur * ((i + 0.5) / num_samples)
        cap.set(cv2.CAP_PROP_POS_MSEC, int(t * 1000))
        ret, frame = cap.read()
        if ret:
            is_blur, box = detect_pillar_or_letter(frame)
            if is_blur:
                has_any_blur = True
                blurred_boxes.append(box)

    if not has_any_blur:
        return False, (0, 0, w, h)

    # Use the tightest bounding box across all samples to guarantee zero blur leak
    min_bw = min(b[2] for b in blurred_boxes)
    min_bh = min(b[3] for b in blurred_boxes)
    x = max(0, (w - min_bw) // 2 // 2 * 2)
    y = max(0, (h - min_bh) // 2 // 2 * 2)
    return True, (x, y, min_bw, min_bh)

_sift = None
_bf = None

def get_geometric_inliers(f1, f2):
    global _sift, _bf
    if _sift is None:
        _sift = cv2.SIFT_create(nfeatures=600)
        _bf = cv2.BFMatcher()
    s1 = cv2.resize(f1, (640, 360))
    s2 = cv2.resize(f2, (640, 360))
    mask = np.zeros((360, 640), dtype=np.uint8)
    mask[int(360 * 0.15):int(360 * 0.85), :] = 255
    kp1, des1 = _sift.detectAndCompute(s1, mask)
    kp2, des2 = _sift.detectAndCompute(s2, mask)
    if des1 is None or des2 is None or len(des1) < 8 or len(des2) < 8:
        return 0
    matches = _bf.knnMatch(des1, des2, k=2)
    good = [m for m, n in matches if m.distance < 0.75 * n.distance]
    if len(good) < 8:
        return 0
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    _, h_mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    return int(np.sum(h_mask)) if h_mask is not None else 0

def split_and_unblur(video_path, out_dir="output_chop", limit=None):
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    actual_path = resolve_video_source(video_path)

    print(f"Scanning scenes in '{actual_path}'...")
    video = open_video(actual_path)
    sm = SceneManager()
    sm.auto_downscale = True
    sm.add_detector(ContentDetector(threshold=28.0, min_scene_len=15))

    scan_end = (limit * 18.0) if (limit and limit <= 15) else None
    sm.detect_scenes(video, frame_skip=0, end_time=scan_end)
    raw_scenes = sm.get_scene_list()

    cap = cv2.VideoCapture(actual_path)
    shots = []
    for s, e in raw_scenes:
        mid_idx = (s.frame_num + e.frame_num) // 2
        cap.set(cv2.CAP_PROP_POS_FRAMES, mid_idx)
        ret, frame = cap.read()
        if not ret:
            continue
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, s.frame_num + 2))
        _, f_start = cap.read()
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, e.frame_num - 2))
        _, f_end = cap.read()

        shots.append({
            "start": s.seconds,
            "end": e.seconds,
            "dur": round(e.seconds - s.seconds, 2),
            "mid_frame": cv2.resize(frame, (640, 360)),
            "mid_hist": get_hsv_hist(frame),
            "start_hist": get_hsv_hist(f_start) if f_start is not None else get_hsv_hist(frame),
            "end_hist": get_hsv_hist(f_end) if f_end is not None else get_hsv_hist(frame),
        })

    # Merge sub-shots of the same incident (replays, multi-angles, zoom-ins)
    incidents = []
    for s in shots:
        if incidents:
            prev = incidents[-1]
            b_corr = float(cv2.compareHist(prev["end_hist"], s["start_hist"], cv2.HISTCMP_CORREL))
            m_corr = float(cv2.compareHist(prev["mid_hist"], s["mid_hist"], cv2.HISTCMP_CORREL))
            max_corr = max(b_corr, m_corr)

            color_match = (max_corr >= 0.70 or b_corr >= 0.75)
            geo_match = False
            if not color_match and (max_corr >= 0.35 or b_corr >= 0.30):
                inl = get_geometric_inliers(prev["mid_frame"], s["mid_frame"])
                if inl >= 14:
                    geo_match = True

            if color_match or geo_match:
                prev["end"] = s["end"]
                prev["dur"] = round(prev["end"] - prev["start"], 2)
                prev["end_hist"] = s["end_hist"]
                prev["mid_frame"] = s["mid_frame"]
                continue
        incidents.append(s)

    # Release intermediate frame references
    for s in shots:
        s.pop("mid_frame", None)
    for inc in incidents:
        inc.pop("mid_frame", None)

    # Multi-checkpoint profile per incident
    for inc in incidents:
        has_blur, box = analyze_incident_profile(cap, inc["start"], inc["end"])
        inc["has_blur"] = has_blur
        inc["box"] = box

    cap.release()

    total = min(limit, len(incidents)) if limit else len(incidents)
    print(f"Exporting {total}/{len(incidents)} distinct scenes into '{out_dir}'...")

    vcodec = get_vcodec()
    results = []
    for i in range(total):
        inc = incidents[i]
        dur = inc["dur"]

        # Accurate frame seeking buffer: trim 0.15s (4-5 frames) from start & end to prevent transition/bleed
        safe_start = inc["start"] + 0.15 if dur > 0.8 else inc["start"]
        safe_end = inc["end"] - 0.15 if dur > 0.8 else inc["end"]
        safe_dur = round(safe_end - safe_start, 2)

        # Native resolution tagging
        bw, bh = inc["box"][2], inc["box"][3]
        out_file = os.path.join(out_dir, f"clip_{i+1:03d}_{bw}x{bh}_{safe_dur}s.mp4")

        # Put -i before -ss for accurate decoded seeking
        cmd = ["ffmpeg", "-y", "-i", actual_path, "-ss", f"{safe_start:.3f}", "-to", f"{safe_end:.3f}"]

        if inc["has_blur"]:
            b = inc["box"]
            # Pure Native Crop: crop exactly to the unblurred content dimensions (no forced scaling)
            cmd += ["-vf", f"crop={b[2]}:{b[3]}:{b[0]}:{b[1]}"]

        cmd += ["-c:v", vcodec, "-b:v", "3500k", "-c:a", "aac", out_file]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        results.append(out_file)
        mode = f"native {bw}x{bh} (unblurred)" if inc["has_blur"] else f"native {bw}x{bh} (full)"
        print(f"  ✓ [{i+1:02d}/{total:02d}] {os.path.basename(out_file)} ({mode})")

    return results

if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else 'full_video.mp4'
    lim = None
    if len(sys.argv) > 2:
        val = sys.argv[2].lower()
        if val not in ('all', '0', 'none'):
            lim = int(val)
    split_and_unblur(src, limit=lim)
