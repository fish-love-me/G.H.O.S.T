# ghost/modules/audio_capture.py
import os, time, wave, queue
import pyaudio, webrtcvad, numpy as np, noisereduce as nr
import soundfile as sf

from ghost.modules.openai_client import config


def capture_audio(
    filename: str | None = None,
    max_record: float = 15.0,
    pre_speech_ms: int = 300,
    silence_timeout_ms: int = 1200
) -> str | None:
    """Capture clean speech only using WebRTC-VAD and denoise with noisereduce."""

    # ── Audio settings ─────────────────────────────────────────────────
    RATE = 16000
    FRAME_MS = 30
    FRAME_SAMPLES = RATE * FRAME_MS // 1000
    CHANNELS = 1

    # RMS threshold to avoid false triggers (e.g., keyboard clicks)
    MIN_RMS_THRESHOLD = 300  # adjust between 300-600 as needed

    # ── File setup ─────────────────────────────────────────────────────
    default_path = config.get("file_paths", {}).get(
        "input_audio", "audio/input.wav"
    )
    filename = filename or default_path
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # ── Initialize modules ─────────────────────────────────────────────
    vad = webrtcvad.Vad(3)  # aggressiveness: 0-3
    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=FRAME_SAMPLES
    )

    ring = queue.deque(maxlen=pre_speech_ms // FRAME_MS)
    recorded: list[bytes] = []

    print("…waiting for speech…", end="", flush=True)
    recording = False
    silence_ms = 0
    start_time = time.time()

    try:
        while True:
            raw = stream.read(FRAME_SAMPLES, exception_on_overflow=False)
            # Voice activity detection
            is_speech = vad.is_speech(raw, RATE)

            # Compute RMS safely
            samples = np.frombuffer(raw, dtype=np.int16)
            if samples.size == 0:
                continue
            with np.errstate(invalid='ignore'):
                rms = np.sqrt(np.mean(samples.astype(np.float32) ** 2))
            if np.isnan(rms):
                continue

            # Trigger recording only if VAD and RMS threshold met
            if not recording:
                ring.append(raw)
                if is_speech and rms > MIN_RMS_THRESHOLD:
                    print("\n🎙 Voice detected, recording…")
                    recording = True
                    recorded.extend(ring)
                    ring.clear()
                    silence_ms = 0
            else:
                recorded.append(raw)
                silence_ms = 0 if is_speech else silence_ms + FRAME_MS
                if silence_ms > silence_timeout_ms:
                    print("⏹ Speech ended.")
                    break

            if time.time() - start_time > max_record:
                print("⏹ Max duration reached.")
                break

    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()

    if len(recorded) < 5:
        print("⚠️ Not enough speech recorded.")
        return None

    # ── Convert and denoise ────────────────────────────────────────────
    audio_data = b"".join(recorded)
    audio_np = np.frombuffer(audio_data, dtype=np.int16)

    print("🔧 Suppressing noise…")
    denoised = nr.reduce_noise(y=audio_np, sr=RATE)

    # ── Save to WAV ────────────────────────────────────────────────────
    try:
        sf.write(filename, denoised, RATE, subtype="PCM_16")
        print(f"💾 Saved → {filename}")
        return filename
    except Exception as e:
        print(f"❌ Save failed: {e}")
        return None
