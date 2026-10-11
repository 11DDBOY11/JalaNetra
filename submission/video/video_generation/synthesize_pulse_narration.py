"""
synthesize_pulse_narration.py
Synthesizes natural, calm Indian English narration for JalaNetra Pulse using edge-tts (en-IN-NeerjaNeural).
Measures exact audio lengths and produces master WAV, MP3, and synchronized SRT subtitle track.
"""

import asyncio
import os
import wave
import subprocess
import edge_tts

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
NARRATION_DIR = os.path.join(ROOT_DIR, "submission", "video", "narration")
TEMP_DIR = os.path.join(NARRATION_DIR, "pulse_scenes")
os.makedirs(TEMP_DIR, exist_ok=True)

VOICE = "en-IN-NeerjaNeural"
RATE = "-2%"
PITCH = "+0Hz"

# The 7 Mandatory Scenes specified in user requirements
SCENES = [
    {
        "id": 1,
        "title": "Scene 1: Problem and Project",
        "text": "JalaNetra Pulse helps Mangaluru communities respond faster when a neighbourhood experiences a water-supply interruption. A resident often cannot tell whether a dry tap is only a home-level issue or a wider local outage.",
        "badge": "JALANETRA PULSE",
        "caption": "Community water outage detection for Mangaluru",
        "target_start": 0.0,
        "target_end": 18.0,
        "asset": "01_scene1_pulse_home.png"
    },
    {
        "id": 2,
        "title": "Scene 2: Current Community Reporting",
        "text": "Residents can report water availability, low supply, or no water. Reports are grouped by ward and time, while personal details are protected.",
        "badge": "CURRENT COMMUNITY REPORTS",
        "caption": "Water available • Low supply • No water",
        "target_start": 18.0,
        "target_end": 38.0,
        "asset": "02_scene2_report_water.png"
    },
    {
        "id": 3,
        "title": "Scene 3: Outage Detection",
        "text": "When three independent residents in the same ward report no water within ninety minutes, JalaNetra Pulse detects a local pattern and creates a community water-issue incident.",
        "badge": "3 INDEPENDENT REPORTS • 90-MINUTE WINDOW",
        "caption": "Community water issue reported",
        "target_start": 38.0,
        "target_end": 65.0,
        "asset": "03_scene3_outage_detected.png"
    },
    {
        "id": 4,
        "title": "Scene 4: Response Board",
        "text": "The response board turns reports into a structured local workflow. Apartment associations, ward volunteers, and community responders can verify the interruption, coordinate water support, and record recovery updates.",
        "badge": "VERIFY SUPPLY INTERRUPTION • COORDINATE SUPPORT",
        "caption": "Record recovery",
        "target_start": 65.0,
        "target_end": 87.0,
        "asset": "04_scene4_response_board.png"
    },
    {
        "id": 5,
        "title": "Scene 5: Historical Water Context",
        "text": "Historical Central Ground Water Board observations provide long-term groundwater context for Dakshin Kannada. JalaNetra keeps this separate from current outage detection, so historical data is never presented as live water availability.",
        "badge": "4,962 HISTORICAL CGWB OBSERVATIONS • 115 STATIONS",
        "caption": "Historical context — not live monitoring",
        "target_start": 87.0,
        "target_end": 106.0,
        "asset": "05_scene5_water_context.png"
    },
    {
        "id": 6,
        "title": "Scene 6: AWS Use and Architecture",
        "text": "JalaNetra Pulse is designed as an AWS serverless system. Amazon API Gateway routes water reports to AWS Lambda. Amazon DynamoDB stores reports, incidents, and subscriptions. Amazon EventBridge evaluates alert patterns, Amazon SNS supports controlled transactional notifications, Amazon S3 stores historical data, and AWS Amplify hosts the public dashboard.",
        "badge": "API GATEWAY • LAMBDA • DYNAMODB • EVENTBRIDGE • SNS",
        "caption": "AWS infrastructure defined with CDK",
        "target_start": 106.0,
        "target_end": 139.0,
        "asset": "06_scene6_aws_architecture.png",
        "sub_asset": "06b_scene6_notification_test.png",
        "sub_asset_switch": 124.0
    },
    {
        "id": 7,
        "title": "Scene 7: Impact and Close",
        "text": "JalaNetra Pulse turns scattered household complaints into a shared community signal. It helps neighbourhoods recognize a water issue earlier, coordinate a response, and build a more reliable picture of local water stress.",
        "badge": "REPORT EARLY • RESPOND TOGETHER",
        "caption": "Build water-resilient communities",
        "target_start": 139.0,
        "target_end": 156.0,
        "asset": "07_scene7_impact_closing.png"
    }
]

async def synthesize_all():
    print(f"Synthesizing natural narration via edge-tts ({VOICE}, rate={RATE})...")
    scene_audio_files = []
    durations = []

    for item in SCENES:
        s_id = item["id"]
        mp3_path = os.path.join(TEMP_DIR, f"scene_{s_id}.mp3")
        wav_path = os.path.join(TEMP_DIR, f"scene_{s_id}.wav")

        communicate = edge_tts.Communicate(item["text"], VOICE, rate=RATE, pitch=PITCH)
        await communicate.save(mp3_path)

        cmd = f'ffmpeg -y -i "{mp3_path}" -ar 44100 -ac 1 "{wav_path}"'
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        with wave.open(wav_path, "rb") as wf:
            dur = wf.getnframes() / float(wf.getframerate())
            durations.append(dur)
            scene_audio_files.append(wav_path)
            print(f"Scene {s_id} ({item['title']}): speech duration = {dur:.2f}s")

    # Target total duration: 156.0 seconds (2m 36s), strictly within 140s-160s (2m20s - 2m40s)
    total_target = 156.0

    # Build master audio placed precisely at each scene's target schedule
    master_wav = os.path.join(NARRATION_DIR, "neural_narration.wav")
    master_mp3 = os.path.join(NARRATION_DIR, "neural_narration.mp3")

    with wave.open(scene_audio_files[0], "rb") as first_wf:
        params = first_wf.getparams()
        sample_rate = first_wf.getframerate()
        n_channels = first_wf.getnchannels()
        sampwidth = first_wf.getsampwidth()

    # Pre-allocate silence buffer for the full 155.0s
    total_frames = int(total_target * sample_rate)
    master_frames = bytearray(total_frames * n_channels * sampwidth)

    timeline = []
    for idx, (f_path, item, dur) in enumerate(zip(scene_audio_files, SCENES, durations)):
        # Center or slight lead-in for speech within the scene window
        scene_start = item["target_start"]
        scene_end = item["target_end"]
        scene_window = scene_end - scene_start

        # Lead-in pause: 1.0s to 1.5s
        lead_in = 1.0 if scene_window > dur + 2.0 else max(0.5, (scene_window - dur) / 2.0)
        speech_start = scene_start + lead_in
        speech_end = speech_start + dur

        timeline.append({
            "id": item["id"],
            "title": item["title"],
            "speech_start": speech_start,
            "speech_end": speech_end,
            "scene_start": scene_start,
            "scene_end": scene_end,
            "text": item["text"],
            "badge": item["badge"],
            "caption": item["caption"],
            "asset": item["asset"],
            "sub_asset": item.get("sub_asset"),
            "sub_asset_switch": item.get("sub_asset_switch")
        })

        with wave.open(f_path, "rb") as in_wf:
            in_bytes = in_wf.readframes(in_wf.getnframes())

        start_byte = int(speech_start * sample_rate) * n_channels * sampwidth
        end_byte = start_byte + len(in_bytes)
        if end_byte <= len(master_frames):
            master_frames[start_byte:end_byte] = in_bytes
        else:
            avail = len(master_frames) - start_byte
            master_frames[start_byte:] = in_bytes[:avail]

        print(f"Scheduled Scene {item['id']}: {speech_start:.1f}s -> {speech_end:.1f}s (window {scene_start:.1f}s -> {scene_end:.1f}s)")

    with wave.open(master_wav, "wb") as out_wf:
        out_wf.setparams(params)
        out_wf.writeframes(master_frames)

    print(f"\nMaster WAV written: {master_wav} ({total_target:.1f}s)")

    # Convert to MP3
    subprocess.run(f'ffmpeg -y -i "{master_wav}" -b:a 192k "{master_mp3}"', shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Master MP3 written: {master_mp3}")

    # Generate synchronized SRT subtitles
    srt_path = os.path.join(NARRATION_DIR, "neural_narration.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        for idx, t in enumerate(timeline):
            st_ms = int(t["speech_start"] * 1000)
            et_ms = int(t["speech_end"] * 1000)
            st_str = f"{st_ms // 3600000:02d}:{(st_ms % 3600000) // 60000:02d}:{(st_ms % 60000) // 1000:02d},{st_ms % 1000:03d}"
            et_str = f"{et_ms // 3600000:02d}:{(et_ms % 3600000) // 60000:02d}:{(et_ms % 60000) // 1000:02d},{et_ms % 1000:03d}"
            f.write(f"{idx + 1}\n{st_str} --> {et_str}\n{t['text']}\n\n")

    print(f"Synchronized SRT written: {srt_path}")
    return timeline, total_target

if __name__ == "__main__":
    asyncio.run(synthesize_all())
