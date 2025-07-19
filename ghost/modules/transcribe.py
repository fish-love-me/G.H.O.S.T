import openai
import json
import os

def transcribe_audio(file_path="audio/input.wav"):
    with open("config.json", "r") as f:
        config = json.load(f)

    client = openai.OpenAI(api_key=config["openai_api_key"])

    print("🧠 Transcribing...")
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )

    print("📝 Transcription complete.")
    return transcript.text
