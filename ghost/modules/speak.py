import openai
import json
import os
import simpleaudio as sa
from pydub import AudioSegment
from threading import Thread

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
    mp3_path = "audio/response.mp3"
    wav_path = "audio/response.wav"

    # Save mp3
    with open(mp3_path, "wb") as f:
        f.write(response.content)

    # Convert to wav
    sound = AudioSegment.from_file(mp3_path, format="mp3")
    sound.export(wav_path, format="wav")

    # Play with simpleaudio (safe)
    wave_obj = sa.WaveObject.from_wave_file(wav_path)
    play_obj = wave_obj.play()
    play_obj.wait_done()

def stream_and_speak(text: str):
    buffer = ""
    thread = None

    def fake_stream(text):
        for char in text:
            yield char

    for part in fake_stream(text):
        print(part, end="", flush=True)
        buffer += part

        if part in [".", "!", "?"]:
            if thread and thread.is_alive():
                thread.join()
            thread = Thread(target=speak, args=(buffer.strip(),))
            thread.start()
            buffer = ""

    if buffer.strip():
        if thread and thread.is_alive():
            thread.join()
        speak(buffer.strip())
