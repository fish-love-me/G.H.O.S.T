import json
from ghost.modules.memory import retrieve, replace_or_add_fact, extract_fact
from ghost.modules.openai_client import client


# Load API key
with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)


BASE_SYSTEM_PROMPT = (
    "You are G.H.O.S.T., a voice assistant inspired by J.A.R.V.I.S. from Iron Man. "
    "You speak fluent Hebrew. Your tone is calm, intelligent, and slightly sarcastic. "
    "You keep answers short, never overreact, and never use emotional or robotic language. "
    "Avoid greetings and motivational speech. You're focused, composed, and independent."
)


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
