import os
import time
import pygame

from ghost.modules.openai_client import config  

client = config.client
model_tts = config.get("model_tts", "tts-1")
default_voice = config.get("default_voice", "nova")

def speak(text: str, voice: str = None):
    voice = voice or default_voice
    print(f"🔊 Speaking with voice: {voice}")

    try:
        response = client.audio.speech.create(
            model=model_tts,
            voice=voice,
            input=text,
            response_format="wav"
        )
    except Exception as e:
        print(f"❌ TTS generation failed: {e}")
        return

    os.makedirs("audio", exist_ok=True)
    timestamp = int(time.time() * 1000)
    wav_path = f"audio/response_{timestamp}.wav"

    try:
        with open(wav_path, "wb") as f:
            f.write(response.content)

        pygame.mixer.init()
        pygame.mixer.music.load(wav_path)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.unload()
        os.remove(wav_path)
        print("✅ Finished speaking.")

    except Exception as e:
        print(f"❌ Audio playback failed: {e}")
