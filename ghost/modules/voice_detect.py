import pyaudio
import os
import wave
import audioop
import time

THRESHOLD = 800  # עוצמת קול שנספר כדיבור – תכוון לפי הצורך
SILENCE_TIMEOUT = 2.0  # כמה שניות של שקט לפני שמפסיקים הקלטה

def wait_for_voice(filename="audio/input.wav", timeout=10):
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16,
                     channels=1,
                     rate=16000,
                     input=True,
                     frames_per_buffer=1024)

    print("🎙 מחכה שתתחיל לדבר...")

    frames = []
    start_time = time.time()
    silence_start = None
    recording = False

    while True:
        data = stream.read(1024, exception_on_overflow=False)
        rms = audioop.rms(data, 2)

        if rms > THRESHOLD:
            if not recording:
                print("🎙 זוהה דיבור. מקליט...")
                recording = True
            frames.append(data)
            silence_start = None

        elif recording:
            frames.append(data)
            if silence_start is None:
                silence_start = time.time()
            elif time.time() - silence_start > SILENCE_TIMEOUT:
                print("🛑 דיבור נפסק. מסיים הקלטה.")
                break

        elif time.time() - start_time > timeout:
            break

    stream.stop_stream()
    stream.close()
    pa.terminate()

    # 🛡 הגנה על מקרי קצה — לא לשלוח קובץ ריק
    if not frames or len(frames) < 5:
        print("❌ לא זוהה דיבור משמעותי. מתעלם.")
        return None

    wave_dir = os.path.dirname(filename)
    if wave_dir:
        os.makedirs(wave_dir, exist_ok=True)

    wf = wave.open(filename, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
    wf.setframerate(16000)
    wf.writeframes(b''.join(frames))
    wf.close()

    return filename
