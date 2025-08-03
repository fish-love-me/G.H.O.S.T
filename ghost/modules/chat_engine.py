import json
from ghost.modules.memory import retrieve, replace_or_add_fact, extract_fact
import openai

# Load API key
with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

client = openai.OpenAI(api_key=CONFIG["openai_api_key"])

BASE_SYSTEM_PROMPT = "You are G.H.O.S.T, a helpful personal voice assistant."

def stream_chat(user_text: str, conversation: list):
    # Load relevant long-term memory
    memories = retrieve(user_text)

    # Compose full message history
    messages = [{"role": "system", "content": BASE_SYSTEM_PROMPT}] + memories + conversation
    messages.append({"role": "user", "content": user_text})

    # Request GPT-4o response (streaming)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        stream=True
    )

    full_reply = ""
    for chunk in response:
        delta = chunk.choices[0].delta.content or ""
        full_reply += delta
        yield delta

    # Update short-term memory
    conversation.append({"role": "user", "content": user_text})
    conversation.append({"role": "assistant", "content": full_reply})

    # ✅ Now safely extract and store fact
    fact = extract_fact(user_text, full_reply)
    if fact:
        replace_or_add_fact(fact)
