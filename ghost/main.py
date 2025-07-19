import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import struct
import pvporcupine
import pyaudio

from modules.input_audio import record_audio
from modules.transcribe import transcribe_audio
from modules.task_classifier import classify_task
from modules.task_router import route_task

def wait_for_wake_word():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    cfg_path = os.path.join(root, "config.json")
    ppn_path = os.path.join(root, "wake_words", "hey-ghost_en_windows_v3_0_0.ppn")

    with open(cfg_path) as f:
        key = json.load(f)["porcupine_access_key"]

    porcupine = pvporcupine.create(access_key=key, keyword_paths=[ppn_path])
    pa = pyaudio.PyAudio()
    stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )

    print("🎧 מחכה ל־‘Hey Ghost’...")
    try:
        while True:
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            if porcupine.process(pcm) >= 0:
                print("👻 זוהתה מילת ההפעלה!")
                break
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        porcupine.delete()

def main():
    wait_for_wake_word()
    record_audio()
    text = transcribe_audio()
    print("🗣 You said:", text)

    task_type = classify_task(text)
    print(f"🔎 Detected task type: {task_type}")

    response = route_task(task_type, text)
    print("🤖 G.H.O.S.T:", response)

if __name__ == "__main__":
    main()
