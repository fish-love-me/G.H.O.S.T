from ghost.modules.audio_capture import capture_audio
import simpleaudio as sa

path = capture_audio()
if path:
    print("▶️ Playing back...")
    sa.WaveObject.from_wave_file(path).play().wait_done()
else:
    print("❌ Nothing was recorded.")
