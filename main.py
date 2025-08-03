from ghost.modules.chat_engine import stream_chat
from ghost.modules.transcribe import transcribe_audio
from ghost.modules.voice_detect import wait_for_voice
from ghost.modules.speak import speak

import json

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

conversation = []

def run():
    while True:
        audio_path = wait_for_voice()
        if not audio_path:
            continue        # skip empty or noise
          
        user_text = transcribe_audio(audio_path)
        if not user_text:   
            continue        # skip empty transcript

        print(f"👤 {user_text}")

        response_text = ""
        for chunk in stream_chat(user_text, conversation):
            print(chunk, end="", flush=True)
            response_text += chunk

        speak(response_text)


if __name__ == "__main__":
    run()
