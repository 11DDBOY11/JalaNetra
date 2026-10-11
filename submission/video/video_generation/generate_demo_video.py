"""
generate_demo_video.py
Assembles the complete, broadcast-quality 1080p MP4 hackathon demo video for JalaNetra Pulse:
- Title: "JalaNetra Pulse — Community Water Outage Detection for Mangaluru"
- Target Duration: 2 minutes 36 seconds (156.0s) — fits 2m20s to 2m40s target perfectly (< 3 mins).
- Video Resolution: 1920x1080 Full HD @ 30 FPS.
- Visual Assets: Current clean light civic-tech UI screenshots captured from localhost & CDK architecture.
- Narration: Natural Microsoft Edge Neural Voice (en-IN-NeerjaNeural).
- Subtitles: Clean, high-contrast, mobile-legible lower-third synchronized captions with badges.
- Cross-fade: 0.4s smooth cinematic transitions between scenes.
- Encodes with libx264 (H.264) and AAC into submission/video/jalanetra_demo.mp4.
"""

import os
import sys
import subprocess
import datetime
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
VIDEO_DIR = os.path.join(ROOT_DIR, "submission", "video")
ASSETS_DIR = os.path.join(VIDEO_DIR, "assets")
NARRATION_DIR = os.path.join(VIDEO_DIR, "narration")
OUTPUT_MP4 = os.path.join(VIDEO_DIR, "jalanetra_demo.mp4")
LOG_FILE = os.path.join(VIDEO_DIR, "video_generation", "generation_log.txt")
NEURAL_AUDIO_WAV = os.path.join(NARRATION_DIR, "neural_narration.wav")

FPS = 30
WIDTH = 1920
HEIGHT = 1080
TOTAL_DURATION = 156.0 # Exactly 2 minutes 36 seconds (< 3 minutes, within 2m20s-2m40s)
TOTAL_FRAMES = int(TOTAL_DURATION * FPS)

# Subtitle Schedule: (start_sec, end_sec, text, badge)
SUBTITLES = [
    # Scene 1: Problem & Project (0.0s - 18.0s)
    (1.0, 17.5,
     "JalaNetra Pulse helps Mangaluru communities respond faster when a neighbourhood experiences a water-supply interruption. A resident often cannot tell whether a dry tap is only a home-level issue or a wider local outage.",
     "JALANETRA PULSE • COMMUNITY WATER OUTAGE DETECTION FOR MANGALURU"),

    # Scene 2: Current Community Reporting (18.0s - 38.0s)
    (19.0, 31.0,
     "Residents can report water availability, low supply, or no water. Reports are grouped by ward and time, while personal details are protected.",
     "CURRENT COMMUNITY REPORTS • WATER AVAILABLE • LOW SUPPLY • NO WATER"),

    # Scene 3: Outage Detection (38.0s - 65.0s)
    (39.0, 51.5,
     "When three independent residents in the same ward report no water within ninety minutes, JalaNetra Pulse detects a local pattern and creates a community water-issue incident.",
     "3 INDEPENDENT REPORTS • 90-MINUTE WINDOW • COMMUNITY WATER ISSUE REPORTED"),

    # Scene 4: Response Board (65.0s - 87.0s)
    (66.0, 83.0,
     "The response board turns reports into a structured local workflow. Apartment associations, ward volunteers, and community responders can verify the interruption, coordinate water support, and record recovery updates.",
     "RESPONSE BOARD • VERIFY INTERRUPTION • COORDINATE SUPPORT • RECORD RECOVERY"),

    # Scene 5: Historical Water Context (87.0s - 106.0s)
    (87.8, 105.5,
     "Historical Central Ground Water Board observations provide long-term groundwater context for Dakshin Kannada. JalaNetra keeps this separate from current outage detection, so historical data is never presented as live water availability.",
     "4,962 CGWB OBSERVATIONS • 115 STATIONS • HISTORICAL CONTEXT (NOT LIVE MONITORING)"),

    # Scene 6a: AWS Architecture (106.0s - 124.0s)
    (106.7, 124.0,
     "JalaNetra Pulse is designed as an AWS serverless system. Amazon API Gateway routes water reports to AWS Lambda. Amazon DynamoDB stores reports, incidents, and subscriptions.",
     "AWS SERVERLESS ARCHITECTURE • API GATEWAY • LAMBDA • DYNAMODB • CDK DEFINED"),

    # Scene 6b: SNS Preview & S3/Amplify (124.0s - 139.0s)
    (124.0, 138.5,
     "Amazon EventBridge evaluates alert patterns, Amazon SNS supports controlled transactional notifications, Amazon S3 stores historical data, and AWS Amplify hosts the public dashboard.",
     "EVENTBRIDGE • SNS NOTIFICATION PREVIEW (SANDBOX SAFETY) • S3 • AMPLIFY"),

    # Scene 7: Impact and Close (139.0s - 156.0s)
    (139.5, 155.5,
     "JalaNetra Pulse turns scattered household complaints into a shared community signal. It helps neighbourhoods recognize a water issue earlier, coordinate a response, and build a more reliable picture of local water stress.",
     "REPORT EARLY • RESPOND TOGETHER • BUILD WATER-RESILIENT COMMUNITIES"),
]

# Visual Scene Cut Schedule: (start_sec, end_sec, asset_filename)
VISUAL_SCENES = [
    (0.0, 18.0, "01_scene1_pulse_home.png"),
    (18.0, 38.0, "02_scene2_report_water.png"),
    (38.0, 65.0, "03_scene3_outage_detected.png"),
    (65.0, 87.0, "04_scene4_response_board.png"),
    (87.0, 106.0, "05_scene5_water_context.png"),
    (106.0, 124.0, "06_scene6_aws_architecture.png"),
    (124.0, 139.0, "06b_scene6_notification_test.png"),
    (139.0, 156.0, "07_scene7_impact_closing.png"),
]

def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{ts}] {msg}"
    print(formatted)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")

def get_font(size, bold=False):
    candidates = [
        "C:\\Windows\\Fonts\\segoeuib.ttf" if bold else "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\calibrib.ttf" if bold else "C:\\Windows\\Fonts\\calibri.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    cur = []
    for w in words:
        test = " ".join(cur + [w])
        bbox = font.getbbox(test)
        if (bbox[2] - bbox[0]) <= max_width:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines

def get_current_subtitle(sec):
    for start, end, text, badge in SUBTITLES:
        if start <= sec < end:
            return text, badge
    return None, None

def get_current_scene_image(sec, asset_images):
    crossfade_dur = 0.4
    for idx, (start, end, fname) in enumerate(VISUAL_SCENES):
        if start <= sec < end:
            base_img = asset_images[fname]
            if idx < len(VISUAL_SCENES) - 1 and (end - sec) <= crossfade_dur:
                next_fname = VISUAL_SCENES[idx + 1][2]
                next_img = asset_images[next_fname]
                alpha = 1.0 - ((end - sec) / crossfade_dur)
                return Image.blend(base_img, next_img, alpha)
            return base_img
    return asset_images[VISUAL_SCENES[-1][2]]

def draw_subtitle_overlay(frame_img, text, badge, f_text, f_badge):
    draw = ImageDraw.Draw(frame_img)
    lines = wrap_text(text, f_text, max_width=1620)
    line_h = 36
    total_h = len(lines) * line_h + 46

    box_y = 1080 - total_h - 36
    box_rect = [110, box_y, 1810, box_y + total_h]

    # Draw dark translucent backdrop
    draw.rounded_rectangle(box_rect, radius=14, fill=(15, 28, 48, 238), outline=(56, 189, 248), width=2)

    # Draw small badge
    bbox_b = f_badge.getbbox(badge)
    bw = bbox_b[2] - bbox_b[0]
    badge_rect = [135, box_y - 14, 135 + bw + 22, box_y + 14]
    draw.rounded_rectangle(badge_rect, radius=6, fill=(22, 50, 79), outline=(56, 189, 248), width=1)
    draw.text((146, box_y - 10), badge, font=f_badge, fill=(56, 189, 248))

    # Draw text lines centered
    text_start_y = box_y + 24
    for l_idx, l in enumerate(lines):
        bbox_l = f_text.getbbox(l)
        lw = bbox_l[2] - bbox_l[0]
        lx = (1920 - lw) // 2
        ly = text_start_y + l_idx * line_h
        draw.text((lx, ly), l, font=f_text, fill=(248, 250, 252))

def assemble_video():
    log("=" * 60)
    log("Starting JalaNetra Pulse Final Demo Video Assembly")
    log("=" * 60)

    if not os.path.exists(NEURAL_AUDIO_WAV):
        raise FileNotFoundError(f"Missing master neural audio: {NEURAL_AUDIO_WAV}")

    log("Preloading visual scene images...")
    asset_images = {}
    for _, _, fname in VISUAL_SCENES:
        if fname not in asset_images:
            p = os.path.join(ASSETS_DIR, fname)
            if not os.path.exists(p):
                raise FileNotFoundError(f"Missing visual asset: {p}")
            img = Image.open(p).convert("RGB")
            if img.size != (WIDTH, HEIGHT):
                img = img.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
            asset_images[fname] = img
    log(f"Successfully loaded {len(asset_images)} scene assets.")

    log(f"Launching FFmpeg sub-process for H.264/AAC MP4 output ({OUTPUT_MP4})...")
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",               # pipe raw frames from stdin
        "-i", NEURAL_AUDIO_WAV,  # neural audio track
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "19",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        OUTPUT_MP4
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    f_text = get_font(25, bold=True)
    f_badge = get_font(15, bold=True)

    log(f"Rendering {TOTAL_FRAMES} frames ({TOTAL_DURATION:.1f}s at {FPS}fps)...")
    progress_step = TOTAL_FRAMES // 10

    for frame_idx in range(TOTAL_FRAMES):
        sec = frame_idx / float(FPS)

        cur_img = get_current_scene_image(sec, asset_images).copy()

        sub_text, sub_badge = get_current_subtitle(sec)
        if sub_text:
            draw_subtitle_overlay(cur_img, sub_text, sub_badge, f_text, f_badge)

        raw_bytes = cur_img.tobytes()
        proc.stdin.write(raw_bytes)

        if frame_idx % progress_step == 0 or frame_idx == TOTAL_FRAMES - 1:
            pct = int((frame_idx + 1) / TOTAL_FRAMES * 100)
            log(f"Progress: {pct}% ({frame_idx + 1}/{TOTAL_FRAMES} frames rendered)")

    proc.stdin.close()
    proc.wait()

    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg failed with return code {proc.returncode}")

    if not os.path.exists(OUTPUT_MP4):
        raise FileNotFoundError(f"Output MP4 was not created at {OUTPUT_MP4}")

    file_size_mb = os.path.getsize(OUTPUT_MP4) / (1024 * 1024)
    log("Video assembly for JalaNetra Pulse finished successfully!")
    log(f"Output Path: {OUTPUT_MP4}")
    log(f"File Size: {file_size_mb:.2f} MB")
    log(f"Target Duration: {TOTAL_DURATION:.1f} seconds")

    probe_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size,bit_rate",
        "-of", "default=noprint_wrappers=1",
        OUTPUT_MP4
    ]
    probe_res = subprocess.run(probe_cmd, capture_output=True, text=True)
    log(f"FFprobe metadata:\n{probe_res.stdout.strip()}")
    return OUTPUT_MP4

if __name__ == "__main__":
    assemble_video()
