import openai
import json
import os
from pydub import AudioSegment
from pydub.playback import play

def speak(text: str, voice="nova"):
    with open("config.json", "r") as f:
        config = json.load(f)

    client = openai.OpenAI(api_key=config["openai_api_key"])

    print("🔊 Speaking...")

    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=text
    )

    os.makedirs("audio", exist_ok=True)
    output_path = "audio/response.mp3"

    with open(output_path, "wb") as f:
        f.write(response.content)

    sound = AudioSegment.from_file(output_path, format="mp3")
    play(sound)
