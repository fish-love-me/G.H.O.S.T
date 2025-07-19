import openai
import json

def get_intent(transcribed_text: str) -> dict:
    with open("config.json", "r") as f:
        config = json.load(f)

    client = openai.OpenAI(api_key=config["openai_api_key"])

    system_prompt = """
You are GHOST, a smart voice assistant. Your job is to extract the user's intent as structured JSON.

Always respond in this format:
{
  "action": "<action_name>",
  "target": "<device_or_app>",
  "args": { ... }
}

Examples:
User says: "Turn on the lamp"
→ {"action": "turn_on", "target": "lamp", "args": {}}

User says: "Open YouTube"
→ {"action": "open_app", "target": "youtube", "args": {}}

If it's unclear or not actionable:
→ {"action": "unknown", "target": "", "args": {}}
"""

    print("🧠 Asking GPT for intent...")

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcribed_text}
        ],
        temperature=0.3
    )

    content = response.choices[0].message.content.strip()

    try:
        intent = json.loads(content)
        print("✅ Intent parsed.")
        return intent
    except json.JSONDecodeError:
        print("❌ GPT returned invalid JSON.")
        return {
            "action": "unknown",
            "target": "",
            "args": {}
        }
