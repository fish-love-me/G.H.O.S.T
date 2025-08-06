import os
from ghost.modules.openai_client import config
client = config.client

model_transcribe = config.get("model_transcribe", "gpt-4o-transcribe")

def transcribe_audio(file_path="audio/input.wav"):
    if not os.path.exists(file_path) or os.path.getsize(file_path) < 100:
        print("⚠️ Empty or missing audio file. Please record something first.")
        return ""

    languages = ["he", "en", "ru"]  # fallback sequence
    result_text = ""

    for lang in languages:
        print(f"🧠 Transcribing (language: {lang})...")
        try:
            with open(file_path, "rb") as audio_file:
                result = client.audio.transcriptions.create(
                    model=model_transcribe,
                    file=audio_file,
                    language=lang
                )
            result_text = result.text.strip()
            if result_text:
                break
        except Exception as e:
            print(f"❌ Transcription error ({lang}): {e}")

    if not result_text:
        print("❌ All transcription attempts failed.")
    else:
        print(f"📝 Transcription: {result_text}")

    return result_text
