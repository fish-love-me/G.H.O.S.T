import json
from miio import Yeelight
from modules.speak import speak
from modules.intent_parser import parse_intent

# Load config
CONFIG = json.load(open("config.json"))

# Get lamp object
def get_lamp():
    return Yeelight(CONFIG["mi_lamp_ip"], CONFIG["mi_lamp_token"])

# Main handler
def handle(text: str) -> str:
    intent = parse_intent(text)
    action = intent.get("action")
    target = intent.get("target")
    args = intent.get("args", {})

    if target != "lamp":
        speak("This handler only works with the lamp.")
        return "❌ Unsupported target."

    if action == "turn_on":
        return turn_on_lamp()
    elif action == "turn_off":
        return turn_off_lamp()
    elif action == "set_brightness":
        return set_brightness(args.get("level"))
    elif action == "increase_brightness":
        return adjust_brightness(+30)
    elif action == "decrease_brightness":
        return adjust_brightness(-30)
    else:
        speak("Unknown command for the lamp.")
        return "❓ Unknown lamp command."

# Lamp control functions

def turn_on_lamp():
    try:
        get_lamp().on()
        return speak_and_return("Lamp turned on.")
    except Exception as e:
        return speak_and_return(f"Failed to turn on lamp: {e}")

def turn_off_lamp():
    try:
        get_lamp().off()
        return speak_and_return("Lamp turned off.")
    except Exception as e:
        return speak_and_return(f"Failed to turn off lamp: {e}")

def set_brightness(level):
    try:
        level = int(level)
        level = max(1, min(100, level))
        get_lamp().set_brightness(level)
        return speak_and_return(f"Brightness set to {level} percent.")
    except Exception:
        return speak_and_return("Could not set brightness.")

def adjust_brightness(change):
    try:
        lamp = get_lamp()
        current = lamp.status().brightness
        new_level = max(1, min(100, current + change))
        lamp.set_brightness(new_level)
        return speak_and_return(f"Brightness adjusted to {new_level} percent.")
    except Exception:
        return speak_and_return("Could not adjust brightness.")

def speak_and_return(msg):
    speak(msg)
    return msg
