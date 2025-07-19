import openai
import json

def transcribe_audio(file_path="audio/input.wav"):
    with open("config.json", "r") as f:
        config = json.load(f)

    client = openai.OpenAI(api_key=config["openai_api_key"])

    print("🧠 Transcribing (forced Hebrew)...")

    # Try Hebrew first
    with open(file_path, "rb") as audio_file:
        result = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=audio_file,
            language="he"
        )

    # Optional: add fallback if transcript is garbage/empty
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
