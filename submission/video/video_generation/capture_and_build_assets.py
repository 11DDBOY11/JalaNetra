"""
capture_and_build_assets.py
Generates the 8 visual assets for the current JalaNetra Pulse demo video:
- 01_scene1_pulse_home.png (Clean light Pulse page with Kodialbail selected)
- 02_scene2_report_water.png (Report water status interface with No water selected)
- 03_scene3_outage_detected.png (Active incident banner on Pulse home + honesty label)
- 04_scene4_response_board.png (Response board with active incident & checklist)
- 05_scene5_water_context.png (Groundwater context with 4,962 CGWB records & chart)
- 06_scene6_aws_architecture.png (Clean light AWS serverless architecture diagram)
- 06b_scene6_notification_test.png (Notification test tool with message preview)
- 07_scene7_impact_closing.png (Clean closing card with light civic-tech design)
"""

import os
import sys
import json
import urllib.request
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ASSETS_DIR = os.path.join(ROOT_DIR, "submission", "video", "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

# Clean Light Civic Palette
COLOR_BG_PAGE = (248, 250, 252)     # #F8FAFC
COLOR_SURFACE = (255, 255, 255)     # #FFFFFF
COLOR_BORDER = (228, 231, 236)      # #E4E7EC
COLOR_NAVY = (22, 50, 79)           # #16324F
COLOR_BLUE = (47, 128, 237)         # #2F80ED
COLOR_TEAL = (21, 158, 156)         # #159E9C
COLOR_TEXT_DARK = (23, 32, 51)      # #172033
COLOR_TEXT_MUTED = (102, 112, 133)  # #667085
COLOR_CRITICAL = (217, 45, 32)      # #D92D20
COLOR_SUCCESS = (18, 183, 106)      # #12B76A

def get_font(size, bold=False):
    font_candidates = [
        "C:\\Windows\\Fonts\\segoeuib.ttf" if bold else "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\calibrib.ttf" if bold else "C:\\Windows\\Fonts\\calibri.ttf"
    ]
    for path in font_candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

def draw_pill(draw, xy, text, font, bg_color, text_color, pad=(16, 8), border_color=None):
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x, y = xy
    rect = [x, y, x + tw + pad[0] * 2, y + th + pad[1] * 2]
    radius = (rect[3] - rect[1]) // 2
    draw.rounded_rectangle(rect, radius=radius, fill=bg_color, outline=border_color, width=1 if border_color else 0)
    draw.text((x + pad[0], y + pad[1] - bbox[1]), text, font=font, fill=text_color)
    return rect[2]

def add_honesty_label(img_path, label_text):
    """Adds a clean, prominent honesty badge to the captured screenshot."""
    img = Image.open(img_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font = get_font(20, bold=True)
    bbox = font.getbbox(label_text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    # Position at top right
    bx = 1920 - tw - 90
    by = 88
    rect = [bx - 18, by - 8, bx + tw + 18, by + th + 12]
    draw.rounded_rectangle(rect, radius=8, fill=(255, 255, 255, 245), outline=(217, 45, 32), width=2)
    draw.text((bx, by), label_text, font=font, fill=(217, 45, 32))

    final = Image.alpha_composite(img, overlay).convert("RGB")
    final.save(img_path, "PNG")

# ─────────────────────────────────────────────────────────────
# 6. Clean Light AWS Serverless Architecture Slide
def wrap_text_lines(text, font, max_width):
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

def draw_vector_arrow(draw, start_xy, end_xy, color=COLOR_BLUE):
    sx, sy = start_xy
    ex, ey = end_xy
    draw.line([(sx, sy), (ex - 6, ey)], fill=color, width=3)
    head = [(ex, ey), (ex - 10, ey - 7), (ex - 10, ey + 7)]
    draw.polygon(head, fill=color)

# ─────────────────────────────────────────────────────────────
# 6. Clean Light AWS Serverless Architecture Slide
# ─────────────────────────────────────────────────────────────
def create_06_aws_architecture():
    img = Image.new("RGB", (1920, 1080), COLOR_BG_PAGE)
    draw = ImageDraw.Draw(img)

    f_pill = get_font(18, bold=True)
    f_head = get_font(44, bold=True)
    f_sub = get_font(21, bold=False)
    f_box_t = get_font(20, bold=True)
    f_box_d = get_font(15, bold=False)

    draw_pill(draw, (135, 70), "AWS SERVERLESS ARCHITECTURE (CODIFIED WITH AWS CDK)", f_pill, (238, 244, 253), COLOR_BLUE, pad=(18, 8), border_color=COLOR_BORDER)
    draw.text((135, 130), "Real-Time Outage Detection & Advisory Pipeline", font=f_head, fill=COLOR_NAVY)
    draw.text((135, 192), "Serverless, event-driven infrastructure defined in infra/app.py for municipal scale.", font=f_sub, fill=COLOR_TEXT_MUTED)

    steps = [
        ("1. Ingestion Layer", "API Gateway & Lambda", "Ingests community reports with SHA-256 privacy & 30-min deduplication.", COLOR_BLUE),
        ("2. Real-Time Storage", "Amazon DynamoDB", "Tables: water_reports, community_alerts, and subscriptions with TTL.", COLOR_NAVY),
        ("3. Scheduled Auditor", "Amazon EventBridge", "Orchestrates 90-min rolling evaluations and alert recovery transitions.", (109, 40, 217)),
        ("4. Notification Hub", "Amazon SNS (Sandbox)", "Controlled transactional SMS preview & verified test send to authorized numbers.", (194, 65, 12)),
        ("5. Citizen Dashboard", "AWS Amplify & S3", "Public civic dashboard hosting with S3 historical CGWB data store.", COLOR_TEAL),
    ]

    card_y = 255
    card_h = 425
    w_step = 300
    gap = 35
    start_x = 135

    for idx, (title, aws_svc, detail, col) in enumerate(steps):
        x = start_x + idx * (w_step + gap)
        # Main card
        draw.rounded_rectangle([x, card_y, x + w_step, card_y + card_h], radius=14, fill=COLOR_SURFACE, outline=COLOR_BORDER, width=1)

        # Header tag
        draw.rounded_rectangle([x + 12, card_y + 16, x + w_step - 12, card_y + 54], radius=6, fill=(242, 244, 247))
        draw.text((x + 20, card_y + 24), title, font=get_font(15, bold=True), fill=COLOR_TEXT_MUTED)

        # AWS Service Title
        draw.text((x + 20, card_y + 72), aws_svc, font=f_box_t, fill=col)
        draw.line([(x + 20, card_y + 112), (x + w_step - 20, card_y + 112)], fill=COLOR_BORDER, width=1)

        # Body detail wrapped
        d_lines = wrap_text_lines(detail, f_box_d, w_step - 40)
        curr_dy = card_y + 130
        for dl in d_lines:
            draw.text((x + 20, curr_dy), dl, font=f_box_d, fill=COLOR_TEXT_DARK)
            curr_dy += 24

        draw_pill(draw, (x + 20, card_y + 355), "CDK Defined", get_font(14, bold=True), (242, 244, 247), col, pad=(12, 6))

        # Vector arrow between cards
        if idx < len(steps) - 1:
            arrow_start_x = x + w_step + 4
            arrow_end_x = x + w_step + gap - 4
            draw_vector_arrow(draw, (arrow_start_x, card_y + 200), (arrow_end_x, card_y + 200), color=COLOR_BLUE)

    # Callouts Row
    callout_y = 710
    draw.rounded_rectangle([135, callout_y, 1785, callout_y + 175], radius=12, fill=COLOR_SURFACE, outline=COLOR_BORDER, width=1)

    callouts = [
        ("90-Min Cluster Rule", "DynamoDB queries aggregate 3+ unique dry hashes within rolling 90m window."),
        ("Zero Privacy Leakage", "Raw phone numbers never logged or stored; SHA-256 masked in all API responses."),
        ("Strict Sandbox Safety", "SMS_LIVE_MODE=false by default; preview-only mode prevents unsolicited broadcasts."),
        ("Cost Optimized", "Under $12/month estimated serverless tier for 60 municipal wards.")
    ]
    f_ch = get_font(18, bold=True)
    f_cb = get_font(15, bold=False)
    for c_idx, (ch, cb) in enumerate(callouts):
        cx = 165 + c_idx * 405
        draw.text((cx, callout_y + 22), ch, font=f_ch, fill=COLOR_NAVY)
        c_lines = wrap_text_lines(cb, f_cb, 370)
        c_dy = callout_y + 58
        for cl in c_lines:
            draw.text((cx, c_dy), cl, font=f_cb, fill=COLOR_TEXT_MUTED)
            c_dy += 22

    # Mandatory Footer
    foot_rect = [135, 915, 1785, 980]
    draw.rounded_rectangle(foot_rect, radius=8, fill=(254, 243, 242), outline=COLOR_CRITICAL, width=2)
    foot_msg = "Local demo shown. AWS deployment architecture defined with CDK."
    draw.text((170, 935), foot_msg, font=get_font(20, bold=True), fill=COLOR_CRITICAL)

    out_p = os.path.join(ASSETS_DIR, "06_scene6_aws_architecture.png")
    img.save(out_p, "PNG")
    print(f"Created {out_p}")

# ─────────────────────────────────────────────────────────────
# 7. Clean Light Impact & Closing Slide (with UI in background)
# ─────────────────────────────────────────────────────────────
def create_07_impact_closing():
    # Use current UI screenshot as subtle background if available
    bg_ui_path = os.path.join(ASSETS_DIR, "01_scene1_pulse_home.png")
    if os.path.exists(bg_ui_path):
        base = Image.open(bg_ui_path).convert("RGBA")
        # Soften/wash out with clean white overlay so text pops with high contrast
        tint = Image.new("RGBA", (1920, 1080), (248, 250, 252, 230))
        img = Image.alpha_composite(base, tint).convert("RGB")
    else:
        img = Image.new("RGB", (1920, 1080), COLOR_BG_PAGE)

    draw = ImageDraw.Draw(img)

    f_pill = get_font(18, bold=True)
    f_huge = get_font(68, bold=True)
    f_sub = get_font(30, bold=True)

    draw_pill(draw, (960 - 200, 105), "COMMUNITY WATER RESPONSE", f_pill, (238, 244, 253), COLOR_BLUE, pad=(18, 8), border_color=COLOR_BORDER)

    title = "JalaNetra Pulse"
    bbox = f_huge.getbbox(title)
    tw = bbox[2] - bbox[0]
    draw.text(((1920 - tw) // 2, 190), title, font=f_huge, fill=COLOR_NAVY)

    sub = "Community water response for Mangaluru"
    bbox_s = f_sub.getbbox(sub)
    tws = bbox_s[2] - bbox_s[0]
    draw.text(((1920 - tws) // 2, 285), sub, font=f_sub, fill=COLOR_BLUE)

    # 3 Takeaway Cards
    card_y = 385
    card_h = 370
    card_w = 480
    cards = [
        ("Report early", "• 1-click household tap status\n• Water available • Low supply • No water\n• Salted SHA-256 privacy protection\n• Zero registration required.", COLOR_BLUE),
        ("Respond together", "• 90-minute cluster detection\n• 3 reports trigger community alert\n• Response board for ward volunteers\n• Structured relief checklist.", COLOR_NAVY),
        ("Build water resilience", "• 4,962 CGWB records context\n• 180-day freshness safeguard\n• AWS serverless CDK architecture\n• Verified community recovery.", COLOR_TEAL),
    ]

    for idx, (title_c, desc_c, col) in enumerate(cards):
        cx = 180 + idx * 540
        draw.rounded_rectangle([cx, card_y, cx + card_w, card_y + card_h], radius=14, fill=COLOR_SURFACE, outline=COLOR_BORDER, width=2)
        draw.text((cx + 32, card_y + 36), title_c, font=get_font(26, bold=True), fill=col)
        draw.line([(cx + 32, card_y + 82), (cx + card_w - 32, card_y + 82)], fill=COLOR_BORDER, width=1)
        draw.multiline_text((cx + 32, card_y + 105), desc_c, font=get_font(20, bold=False), fill=COLOR_TEXT_DARK, spacing=14)

    close_text = "Report early  •  Respond together  •  Build water-resilient communities"
    f_q = get_font(24, bold=True)
    bbox_q = f_q.getbbox(close_text)
    twq = bbox_q[2] - bbox_q[0]
    draw.text(((1920 - twq) // 2, 825), close_text, font=f_q, fill=COLOR_NAVY)

    foot = "JalaNetra Pulse  •  FastAPI  •  React  •  TypeScript  •  AWS CDK"
    f_ft = get_font(18, bold=False)
    bbox_ft = f_ft.getbbox(foot)
    twft = bbox_ft[2] - bbox_ft[0]
    draw.text(((1920 - twft) // 2, 915), foot, font=f_ft, fill=COLOR_TEXT_MUTED)

    out_p = os.path.join(ASSETS_DIR, "07_scene7_impact_closing.png")
    img.save(out_p, "PNG")
    print(f"Created {out_p}")

# ─────────────────────────────────────────────────────────────
# Playwright Capture of Current Light Civic-Tech UI
# ─────────────────────────────────────────────────────────────
def reset_scenario_via_api():
    req = urllib.request.Request("http://localhost:8000/api/pulse/scenario/reset", data=b"{}", headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)

def seed_outage_via_api():
    req = urllib.request.Request("http://localhost:8000/api/pulse/scenario/seed-outage", data=json.dumps({"ward_id": "dk-kodialbail"}).encode(), headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)

def capture_live_screenshots():
    print("Resetting scenario data to normal clean baseline...")
    reset_scenario_via_api()

    print("Launching Chrome for live app capture...")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})

        # 1. Capture 01_scene1_pulse_home.png (Clean light Pulse page with Kodialbail selected)
        print("Capturing 01_scene1_pulse_home.png...")
        page.goto("http://localhost:5173/")
        page.wait_for_timeout(1500)
        p1 = os.path.join(ASSETS_DIR, "01_scene1_pulse_home.png")
        page.screenshot(path=p1)
        print(f"Captured {p1}")

        # 2. Capture 02_scene2_report_water.png (Report water status interface with No water selected)
        print("Capturing 02_scene2_report_water.png...")
        page.goto("http://localhost:5173/?tab=report")
        page.wait_for_timeout(1200)
        page.click("button:has-text('No water')")
        page.wait_for_timeout(800)
        p2 = os.path.join(ASSETS_DIR, "02_scene2_report_water.png")
        page.screenshot(path=p2)
        print(f"Captured {p2}")

        # 3. Capture 03_scene3_outage_detected.png (Seed 3 reports and show active alert on Pulse home)
        print("Seeding 3 No water reports for Kodialbail...")
        seed_outage_via_api()
        page.wait_for_timeout(1000)
        page.goto("http://localhost:5173/")
        page.wait_for_timeout(1500)
        p3 = os.path.join(ASSETS_DIR, "03_scene3_outage_detected.png")
        page.screenshot(path=p3)
        add_honesty_label(p3, "Simulated reports used for this recorded scenario.")
        print(f"Captured {p3}")

        # 4. Capture 04_scene4_response_board.png (Response board with active incident in Kodialbail)
        print("Capturing 04_scene4_response_board.png...")
        page.goto("http://localhost:5173/?tab=admin")
        page.wait_for_timeout(1500)
        p4 = os.path.join(ASSETS_DIR, "04_scene4_response_board.png")
        page.screenshot(path=p4)
        print(f"Captured {p4}")

        # 5. Capture 05_scene5_water_context.png (Groundwater context with CGWB observations & chart)
        print("Capturing 05_scene5_water_context.png...")
        page.goto("http://localhost:5173/?tab=historical")
        page.wait_for_timeout(1500)
        p5 = os.path.join(ASSETS_DIR, "05_scene5_water_context.png")
        page.screenshot(path=p5)
        print(f"Captured {p5}")

        # 6. Capture 06b_scene6_notification_test.png (Notification test tool with message preview)
        print("Capturing 06b_scene6_notification_test.png...")
        page.goto("http://localhost:5173/?tab=tools")
        page.wait_for_timeout(1200)
        page.click("button:has-text('Generate message preview')")
        page.wait_for_timeout(1200)
        p6b = os.path.join(ASSETS_DIR, "06b_scene6_notification_test.png")
        page.screenshot(path=p6b)
        print(f"Captured {p6b}")

        browser.close()

if __name__ == "__main__":
    print("Building graphical architecture slide...")
    create_06_aws_architecture()

    print("Capturing live screenshots from localhost...")
    capture_live_screenshots()

    print("Building closing slide with current UI background...")
    create_07_impact_closing()

    print("All visual assets captured and created successfully!")
