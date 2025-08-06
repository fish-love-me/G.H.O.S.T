# main.py
import json
import struct
import time
import os
from datetime import datetime, timedelta

import pyaudio
import pvporcupine

from ghost.modules.chat_engine import stream_chat
from ghost.modules.transcribe import transcribe_audio
from ghost.modules.audio_capture import capture_audio as wait_for_voice
from ghost.modules.speak import speak
from ghost.modules.memory import retrieve, extract_fact, replace_or_add_fact

# ── CONFIGURATION ────────────────────────────────────────────────
MODE = "text"  # "voice" or "text"

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

ACCESS_KEY = CONFIG.get("porcupine_access_key")
KEYWORD_PATH = "C:/Users/ronie/G.H.O.S.T/wake_words/hey-ghost_en_windows_v3_0_0.ppn"

SILENCE_TIMEOUT_SEC = 10
STOP_PHRASES = {"תודה", "סיימתי", "זהו", "אין לי עוד שאלות"}

# ── FUNCTIONS ────────────────────────────────────────────────────
def wait_for_wakeword(keyword_path: str, access_key: str):
    porcupine = pvporcupine.create(
        access_key=access_key,
        keyword_paths=[keyword_path]
    )
    pa = pyaudio.PyAudio()
    stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )
    print("…listening for wake word…", end="", flush=True)
    try:
        while True:
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm_unpacked = struct.unpack_from("h" * porcupine.frame_length, pcm)
            if porcupine.process(pcm_unpacked) >= 0:
                print("\n🔔 Wake word detected!\n")
                break
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        porcupine.delete()


def handle_interaction(user_text: str, conversation: list[dict]):
    if user_text.strip() in STOP_PHRASES:
        if MODE == "voice":
            speak("בשמחה. עד הפעם הבאה.")
        else:
            print("🧠 סיום שיחה.")
        return False

    response_text = ""
    print("🤖 ", end="", flush=True)
    for chunk in stream_chat(user_text, conversation):
        print(chunk, end="", flush=True)
        response_text += chunk

    if MODE == "voice":
        speak(response_text)

    conversation.append({"role": "user", "content": user_text})
    conversation.append({"role": "assistant", "content": response_text})

    # <<< שינינו כאן כדי לבדוק האם באמת נוספה זיכרון חדש >>>
    fact = extract_fact(user_text, response_text)
    if fact:
        added = replace_or_add_fact(fact)   # מחזיר True אם המערכת הוסיפה/החליפה
        if added:
            print(f"\n📌 New fact: {fact}")

    return True

    if user_text.strip() in STOP_PHRASES:
        if MODE == "voice":
            speak("בשמחה. עד הפעם הבאה.")
        else:
            print("🧠 סיום שיחה.")
        return False

    response_text = ""
    print("🤖 ", end="", flush=True)
    for chunk in stream_chat(user_text, conversation):
        print(chunk, end="", flush=True)
        response_text += chunk

    if MODE == "voice":
        speak(response_text)

    conversation.append({"role": "user", "content": user_text})
    conversation.append({"role": "assistant", "content": response_text})

    fact = extract_fact(user_text, response_text)
    if fact:
        print(f"\n📌 New fact: {fact}")
        replace_or_add_fact(fact)

    return True

    if user_text.strip() in STOP_PHRASES:
        if MODE == "voice":
            speak("בשמחה. עד הפעם הבאה.")
        else:
            print("🧠 סיום שיחה.")
        return False

    response_text = ""
    print("🤖 ", end="", flush=True)
    for chunk in stream_chat(user_text, conversation):
        print(chunk, end="", flush=True)
        response_text += chunk

    if MODE == "voice":
        speak(response_text)

    conversation.append({"role": "user", "content": user_text})
    conversation.append({"role": "assistant", "content": response_text})

    fact = extract_fact(user_text, response_text)
    if fact:
        print(f"\n📌 New fact: {fact}")
        replace_or_add_fact(fact)

    return True
    # Process chat
    response_text = ""
    for chunk in stream_chat(user_text, conversation):
        print(chunk, end="", flush=True)
        response_text += chunk

    if MODE == "voice":
        speak(response_text)
        
    

    # Update memory
    conversation.append({"role": "user", "content": user_text})
    conversation.append({"role": "assistant", "content": response_text})

    fact = extract_fact(user_text, response_text)
    if fact:
        print(f"\n📌 New fact: {fact}")
        replace_or_add_fact(fact)

    return True

# ── MAIN LOOP ───────────────────────────────────────────────────
def run():
    while True:
        if MODE == "voice":
            if not ACCESS_KEY or not os.path.isfile(KEYWORD_PATH):
                raise RuntimeError("Porcupine config missing.")
            wait_for_wakeword(KEYWORD_PATH, ACCESS_KEY)
            print("…entering conversation mode…")

        conversation = retrieve("user memory")
        last_input = datetime.now()
        in_conversation = True

        while in_conversation:
            if MODE == "voice":
                audio_path = wait_for_voice()
                now = datetime.now()
                if audio_path:
                    last_input = now
                    user_text = transcribe_audio(audio_path)
                    if not user_text:
                        continue
                    in_conversation = handle_interaction(user_text, conversation)
                elif (now - last_input) > timedelta(seconds=SILENCE_TIMEOUT_SEC):
                    speak("נראה שהשיחה נסתיימה. הפעם הבאה!")
                    break
                else:
                    time.sleep(0.1)

            elif MODE == "text":
                try:
                    user_text = input("\n👤 ")
                    if user_text.strip() == "":
                        continue
                    in_conversation = handle_interaction(user_text, conversation)
                except KeyboardInterrupt:
                    print("\n🛑 Exiting.")
                    return

        print("…waiting for next interaction…")


if __name__ == "__main__":
    run()
