import os
import subprocess
from ghost.modules.openai_client import client

voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
test_sentence = "שלום זה הקול שלי, מה אומר?"

os.makedirs("audio/test_voices", exist_ok=True)

for voice in voices:
    print(f"🔊 Generating voice: {voice}")

    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=test_sentence,
        response_format="wav"
    )

    wav_path = f"audio/test_voices/{voice}.wav"
    with open(wav_path, "wb") as f:
        f.write(response.content)

    print(f"▶ Playing: {voice}")
    subprocess.run(["start", wav_path], shell=True)  # Opens with default system player

    input("⏸ Press Enter to continue to next voice...")  # Wait for you to finish listening

print("✅ All voices tested.")
