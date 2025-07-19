import subprocess
import webbrowser
import json
from miio import Yeelight
from modules.speak import speak


def execute_intent(intent: dict):
    action = intent.get("action")
    target = intent.get("target")

    if action == "open_app":
        return open_app(target)

    elif action == "turn_on":
        return turn_on_device(target)

    elif action == "turn_off":
        return turn_off_device(target)

    else:
        print("⚠️ Unknown action. No execution.")
        speak("Sorry, I don't know how to handle that.")
        return


def open_app(target: str):
    target = target.lower()

    if target == "google":
        print("🌐 Opening Google in browser...")
        speak("Opening Google")
        webbrowser.open("https://www.google.com")

    elif target == "notepad":
        print("📝 Opening Notepad...")
        speak("Opening Notepad")
        subprocess.Popen(["notepad.exe"])

    else:
        print(f"❌ App '{target}' not recognized.")
        speak(f"I don't know how to open {target}")


def get_lamp():
    with open("config.json", "r") as f:
        config = json.load(f)
    return Yeelight(config["mi_lamp_ip"], config["mi_lamp_token"])


def turn_on_device(target: str):
    if target.lower() == "lamp":
        try:
            lamp = get_lamp()
            lamp.on()
            speak("Turning on the lamp")
            print("✅ Lamp turned on.")
        except Exception as e:
            print(f"❌ Error turning on lamp: {e}")
            speak("Failed to turn on the lamp")
    else:
        print(f"💡 (Mock) Turning ON '{target}'")
        speak(f"Turning on {target}")


def turn_off_device(target: str):
    if target.lower() == "lamp":
        try:
            lamp = get_lamp()
            lamp.off()
            speak("Turning off the lamp")
            print("✅ Lamp turned off.")
        except Exception as e:
            print(f"❌ Error turning off lamp: {e}")
            speak("Failed to turn off the lamp")
    else:
        print(f"💡 (Mock) Turning OFF '{target}'")
        speak(f"Turning off {target}")
