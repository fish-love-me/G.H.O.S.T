# ghost/modules/chat_engine.py
"""High‑level chat orchestration for G.H.O.S.T.

Major improvements vs. original version
--------------------------------------
1. **Better noise detection** – delegates entirely to `looks_intelligible`, no
   hard cutoff on length ("hi" is now accepted) and ignores leading emojis.
2. **Conversation window management** – trims history to fit within a token
   budget so we never exceed the model context, even on long sessions.
3. **Robust OpenAI call** – retries with exponential back‑off on transient
   errors and yields a fallback message if all attempts fail.
4. **Streaming helper** – isolates streaming logic in `_stream_completion` for
   clarity and centralised error handling.
5. **Clear type hints & dataclasses** – improves IDE support and readability.
6. **Config hot‑reload** – allows live editing of config.json without restart.
7. **Richer memory query** – uses regex so "מה אתה זוכר על" / "what do you know
   about me" variants are also detected.

Usage remains identical: `for token in stream_chat(user_text, convo): ...`
"""

from __future__ import annotations

import itertools
import re
import time
from dataclasses import dataclass, field
from typing import Iterable, List

from ghost.modules.memory import (
    extract_fact,
    load_all_facts,
    replace_or_add_fact,
    retrieve,
)
from ghost.modules.openai_client import config as _config
from ghost.modules.utils import looks_intelligible
from ghost.modules.context_manager import build_context

# ---------------------------------------------------------------------------
#                               CONFIG ACCESS
# ---------------------------------------------------------------------------

def _cfg(key: str, default):
    """Live‑fetch a config key so changes in *config.json* are picked up."""
    return _config.get(key, default)


# ---------------------------------------------------------------------------
#                                CONSTANTS
# ---------------------------------------------------------------------------

_BASE_SYSTEM_PROMPT = _cfg(
    "base_system_prompt",
    "אתה jarvis — עוזר אישי חכם שרץ על המחשב המקומי של המשתמש. "
    "דבר עברית, אנגלית ורוסית. טון חכם, רגוע וקצת ציני. השתמש בזיכרון ארוך‑טווח כשזה מוסיף ערך. "
    "בקש אישור לפני שאתה מוסיף עובדות חדשות לזיכרון. תשובות תמציתיות."
)
_MODEL_CHAT = _cfg("model_chat", "gpt-4o")
_MODEL_CHAT_LATEST = _cfg("model_chat_latest", None)
_UNCLEAR_PROMPT = _cfg(
    "unclear_prompt", "מצטער, לא הבנתי. אפשר לנסח מחדש בבקשה?"
)

# Token budget for history (rough heuristic – 4 chars ≈ 1 token)
_MAX_PROMPT_CHARS = 12_000

# Noise regex pulled‑out emojis / punct only
_SIMPLE_NOISE = re.compile(r"^[\W_]+$")

# Memory query patterns (Hebrew / English, flexible wording)
_MEMORY_PATTERNS = re.compile(
    r"(?i)(?:מה\s+את[ה]?\s+זוכר|what\s+do\s+you\s+remember|what\s+do\s+you\s+know\s+about\s+me)"
)


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str

    def to_dict(self):
        return {"role": self.role, "content": self.content}


# ---------------------------------------------------------------------------
#                              NOISE FILTER
# ---------------------------------------------------------------------------

def _is_noise(text: str) -> bool:
    txt = text.strip()
    if not txt:
        return True
    if _SIMPLE_NOISE.match(txt):
        return True
    return not looks_intelligible(txt)


# ---------------------------------------------------------------------------
#                          STREAMING COMPLETIONS
# ---------------------------------------------------------------------------

_MAX_RETRIES = 3
_BACKOFF_BASE = 1.2


def _stream_completion(messages: List[Message]) -> Iterable[str]:
    from openai import OpenAIError  # local import to avoid hard dependency if mocked

    client = _config.client
    last_err: str | None = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=_cfg("model_chat", "gpt-4o"),
                messages=[m.to_dict() for m in messages],
                stream=True,
            )
            for chunk in response:
                yield chunk.choices[0].delta.content or ""
            return  # success, exit function
        except OpenAIError as exc:  # pragma: no cover
            last_err = str(exc)
            sleep = _BACKOFF_BASE ** attempt
            time.sleep(sleep)
    # if we reach here, all retries failed
    yield _UNCLEAR_PROMPT + f" (api‑error: {last_err})"


# ---------------------------------------------------------------------------
#                           PUBLIC ENTRY POINT
# ---------------------------------------------------------------------------

def stream_chat(user_text: str, conversation: list[dict]) -> Iterable[str]:
    """Stream response tokens for *user_text* while updating *conversation*."""

    # 0️⃣ Memory inspection command
    if _MEMORY_PATTERNS.search(user_text.lower()):
        facts = load_all_facts()
        if facts:
            lines = "\n".join(f"- {f}" for f in facts)
            yield f"אני זוכר את הדברים הבאים עליך:\n{lines}"
        else:
            yield "שום דבר, למרבה הצער. אין לי זיכרונות עליך כרגע."
        return

    # 1️⃣ Noise filter
    if _is_noise(user_text):
        yield _UNCLEAR_PROMPT
        return

    # 2️⃣ Build full context (system + long-term + short-term or summary + user msg)
    messages = build_context(user_text, conversation)

    # 3️⃣ Stream LLM response
    full_reply = ""
    for token in _stream_completion(messages):
        full_reply += token
        yield token

    # 4️⃣ Persist short‑term history
    conversation.extend([
        Message("user", user_text).to_dict(),
        Message("assistant", full_reply).to_dict(),
    ])

    # 5️⃣ Possible fact extraction
    if fact := extract_fact(user_text, full_reply):
        replace_or_add_fact(fact)
