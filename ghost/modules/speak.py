import os
import pygame
import time

from ghost.modules.openai_client import client

def speak(text: str, voice="onyx"):
    print("🔊 Speaking...")

    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=text,
        response_format="wav"
    )

    os.makedirs("audio", exist_ok=True)

    timestamp = int(time.time() * 1000)
    wav_path = f"audio/response_{timestamp}.wav"

    with open(wav_path, "wb") as f:
        f.write(response.content)

    pygame.mixer.init()
    pygame.mixer.music.load(wav_path)
    pygame.mixer.music.play()

    # ✅ נמתין עד שהנגינה תסתיים
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    # ✅ נוודא שסיים לנגן לפני שנמחק
    pygame.mixer.music.unload()  # חובה לפני מחיקה ב-Windows
    os.remove(wav_path)
