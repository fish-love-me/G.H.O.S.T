import openai
import json
import os

def transcribe_audio(file_path="audio/input.wav"):
    if not os.path.exists(file_path) or os.path.getsize(file_path) < 100:
        print("❌ קובץ השמע ריק או לא קיים. מדלג על תמלול.")
        return ""

    with open("config.json", "r") as f:
        config = json.load(f)

    client = openai.OpenAI(api_key=config["openai_api_key"])

    print("🧠 Transcribing (forced Hebrew)...")

    with open(file_path, "rb") as audio_file:
        result = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=audio_file,
            language="he"
        )

    if len(result.text.strip()) < 2:
        print("⚠️ Empty or failed Hebrew transcription. Trying English...")
        with open(file_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file,
                language="en"
            )

    if len(result.text.strip()) < 2:
        print("⚠️ Still unclear. Trying Russian...")
        with open(file_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file,
                language="ru"
            )

    print("📝 Transcription complete.")
    return result.text
