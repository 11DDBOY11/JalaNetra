"""
generate_narration.py
Synthesizes truthful English narration for JalaNetra hackathon demo video using local TTS.
Zero external API calls, zero paid cloud dependencies, 100% offline.
"""
import os
import wave
import pyttsx3

SCENES = [
    {
        "id": 1,
        "text": "JalaNetra is a responsible water-security decision-support system for Mangaluru. Coastal Karnataka receives heavy rainfall, but communities can still experience groundwater stress after the monsoon."
    },
    {
        "id": 2,
        "text": "JalaNetra integrates 4,962 real historical Central Ground Water Board observations from 115 monitoring stations in Dakshin Kannada, covering 1996 to 2020. These are quarterly government observations, not live groundwater sensor readings."
    },
    {
        "id": 3,
        "text": "Most dashboards would turn old data into a confident-looking alert. JalaNetra does the opposite. When the latest verified station observation is too old, it shows historical groundwater context only and refuses to generate a misleading current tanker-booking recommendation."
    },
    {
        "id": 4,
        "text": "Residents can report whether water supply came, was low, or was unavailable. This creates a pathway for current community signals while protecting users from overconfident forecasts based on stale measurements."
    },
    {
        "id": 5,
        "text": "For preparedness, JalaNetra includes a clearly labelled what-if simulator. A dry-water scenario can demonstrate a precautionary advisory, but it is always marked as a scenario simulation, not a live measurement and not a real alert."
    },
    {
        "id": 6,
        "text": "The production-ready AWS architecture is defined with CDK using API Gateway, Lambda, DynamoDB, S3, EventBridge, SNS, Polly, and Amplify. This hackathon demonstration runs locally, sends no messages, and deploys no cloud resources."
    },
    {
        "id": 7,
        "text": "JalaNetra turns historical groundwater records into transparent local context, knows when data is too old to act on, and prepares a safer path from community reports to water-stress preparedness."
    }
]

def synthesize_scenes():
    out_dir = os.path.abspath("submission/video/narration")
    os.makedirs(out_dir, exist_ok=True)
    temp_dir = os.path.join(out_dir, "temp_scenes")
    os.makedirs(temp_dir, exist_ok=True)

    engine = pyttsx3.init()
    engine.setProperty("rate", 145) # Calm, deliberate pacing
    voices = engine.getProperty("voices")
    # Prefer English voice if present
    for v in voices:
        if "david" in v.name.lower() or "zira" in v.name.lower() or "english" in v.name.lower():
            engine.setProperty("voice", v.id)
            break

    scene_files = []
    durations = []

    for item in SCENES:
        s_id = item["id"]
        s_path = os.path.join(temp_dir, f"scene_{s_id}.wav")
        engine.save_to_file(item["text"], s_path)
        engine.runAndWait()

        # Measure duration
        with wave.open(s_path, 'rb') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            dur = frames / float(rate)
            durations.append(dur)
            scene_files.append(s_path)
            print(f"Scene {s_id}: {dur:.2f} seconds")

    total_speech = sum(durations)
    print(f"Total raw speech duration: {total_speech:.2f} seconds")

    # Now create concatenated narration_en.wav with 1.2s silence gap between scenes
    combined_wav = os.path.join(out_dir, "narration_en.wav")

    # Read first file to get parameters
    with wave.open(scene_files[0], 'rb') as first_wf:
        params = first_wf.getparams()
        sample_rate = first_wf.getframerate()
        n_channels = first_wf.getnchannels()
        sampwidth = first_wf.getsampwidth()

    silence_frames = int(sample_rate * 1.0) # 1.0 second silence between scenes
    silence_bytes = b'\x00' * (silence_frames * n_channels * sampwidth)

    with wave.open(combined_wav, 'wb') as out_wf:
        out_wf.setparams(params)
        for idx, f_path in enumerate(scene_files):
            with wave.open(f_path, 'rb') as in_wf:
                out_wf.writeframes(in_wf.readframes(in_wf.getnframes()))
            if idx < len(scene_files) - 1:
                out_wf.writeframes(silence_bytes)

    with wave.open(combined_wav, 'rb') as final_wf:
        final_dur = final_wf.getnframes() / float(final_wf.getframerate())

    print(f"Final combined narration_en.wav duration: {final_dur:.2f} seconds")
    return final_dur, durations

if __name__ == "__main__":
    synthesize_scenes()
