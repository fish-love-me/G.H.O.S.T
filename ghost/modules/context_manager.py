# ghost/modules/context_manager.py

from __future__ import annotations
from typing import List
from ghost.modules.memory import retrieve
from ghost.modules.openai_client import config as _cfg

# סף אורך לשיחה הקצרה לפני שמסכמים
MAX_SHORT_CONVO_CHARS = 2000

client = _cfg.client


def summarize_short_term(conversation: List[dict]) -> str:
    """סיכום של השיחה הקצרה כשהיא מתארכת מדי."""
    text = ""
    for msg in conversation:
        prefix = "User" if msg["role"] == "user" else "Assistant"
        text += f"{prefix}: {msg['content']}\n"

    prompt = [
        {"role": "system", "content": (
            "סכם את השיחה בין המשתמש לעוזר בניסוח קצר ומובן שמכסה את כל הנקודות החשובות, "
            "כדי שאוכל להשתמש בזה כהקשר לשיחה עתידית. אל תמציא מידע."
        )},
        {"role": "user", "content": text.strip()}
    ]

    try:
        resp = client.chat.completions.create(
            model=_cfg.get("model_chat", "gpt-4o"),
            messages=prompt,
            max_tokens=256,
            temperature=0.3
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Short-term summarization failed: {e}")
        return "שיחה קודמת עם המשתמש התקבלה אך לא סוכמה בהצלחה."


def build_context(user_text: str, short_term: List[dict]) -> List:
    """יוצר את רשימת ההודעות (context) שישלחו ל־LLM, כולל זיכרון ארוך + שיחה קצרה / סיכום."""
    # Lazy import to avoid circular dependency
    from ghost.modules.chat_engine import Message

    messages: List[Message] = []
    base_prompt = _cfg.get("base_system_prompt", "אתה עוזר אישי חכם.")

    # 1. Prompt ראשי
    messages.append(Message("system", base_prompt))

    # 2. סיכום של הזיכרון הארוך
    memories = retrieve(user_text)
    if memories:
        messages.extend(Message(**m) for m in memories)

    # 3. אם השיחה קצרה → מוסיפים את כולה
    total_chars = sum(len(m["content"]) for m in short_term)
    if total_chars <= MAX_SHORT_CONVO_CHARS:
        messages.extend(Message(**m) for m in short_term)
    else:
        # אם ארוכה מדי → סיכום במקום
        summary = summarize_short_term(short_term)
        messages.append(Message("system", f"[short-term summary] {summary}"))

    # 4. הודעת המשתמש הנוכחית
    messages.append(Message("user", user_text))

    return messages
