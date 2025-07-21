import openai
import json
import re

def parse_intent(text: str) -> dict:
    print("🧠 Parsing intent...")
    lowered = text.lower()

    # Aliases
    is_lamp = any(word in lowered for word in ["מנורה", "lamp", "אור", "האור"])
    is_turn_on = any(word in lowered for word in ["תדליק", "הפעל"])
    is_turn_off = any(word in lowered for word in ["כבה", "תכבה"])
    is_brightness_up = any(word in lowered for word in ["הגבר", "תגביר", "יותר אור"])
    is_brightness_down = any(word in lowered for word in ["הנמך", "תוריד", "פחות אור"])

    if is_turn_on and is_lamp:
        return {"action": "turn_on", "target": "lamp", "args": {}}

    if is_turn_off and is_lamp:
        return {"action": "turn_off", "target": "lamp", "args": {}}

    if "בהירות" in lowered and is_lamp:
        if is_brightness_up:
            return {"action": "increase_brightness", "target": "lamp", "args": {}}
        if is_brightness_down:
            return {"action": "decrease_brightness", "target": "lamp", "args": {}}
        match = re.search(r"(\d{1,3})", lowered)
        if match:
            return {"action": "set_brightness", "target": "lamp", "args": {"level": int(match.group(1))}}

    # fallback to GPT
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        client = openai.OpenAI(api_key=config["openai_api_key"])

        system_prompt = """
You are GHOST, a smart voice assistant. Extract user intent from the input in this format:

{
  "action": "<action>",
  "target": "<target>",
  "args": { ... }
}

Only return JSON. If the intent is unclear, return:
{"action": "unknown", "target": "", "args": {}}
"""
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        return json.loads(response.choices[0].message.content.strip())

    except Exception as e:
        print("❌ Fallback failed:", e)
        return {"action": "unknown", "target": "", "args": {}}
