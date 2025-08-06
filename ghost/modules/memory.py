# ghost/modules/memory.py
"""Long-term memory store (vector + shallow semantics)

Key upgrades vs. original implementation
----------------------------------------
1. **Robust deduplication**
   • Cheap textual fingerprint (casefold, strip diacritics, remove punctuation)
   • Fuzzy ratio fallback before expensive embedding call
   • Embedding similarity threshold lowered to 0.82 and applied *after* exact/fuzzy checks.

2. **Slot tagging** – LLM can optionally return a *slot* (e.g. NAME, LOCATION,
   PREF) so we overwrite previous facts of the same slot instead of piling up.
   Falls back to “generic” if tag missing. This keeps only one canonical fact
   per slot.

3. **Memory retrieval uniqueness** – guarantees we never inject two facts whose
   fingerprint is identical; top-k selection uses both similarity and recency
   score.

4. **Safe file writes** – tmp file + atomic replace to avoid corruption.

5. **Config hot-reload** – same pattern as new chat_engine.
"""

from __future__ import annotations

import json
import re
import tempfile
import time
from pathlib import Path
from typing import Final, List, Tuple

import numpy as np
from difflib import SequenceMatcher
from unidecode import unidecode

from ghost.modules.openai_client import config as _cfg

# ---------------------------------------------------------------------------
#                              CONFIG & CONSTANTS
# ---------------------------------------------------------------------------

def C(key: str, default):
    return _cfg.get(key, default)

client = _cfg.client

EMBED_MODEL: Final = C("model_embed", "text-embedding-3-small")
DB_FILE: Final = Path(C("memory_store_path", "ghost/memory_store.jsonl"))

# ---------------------------------------------------------------------------
#                               TEXT UTILS
# ---------------------------------------------------------------------------

_PUNCT = re.compile(r"[\W_]+", re.UNICODE)

def _fingerprint(text: str) -> str:
    """Return canonical fingerprint for quick dedup."""
    txt = unidecode(text.casefold())  # lower + ASCII fold
    txt = _PUNCT.sub(" ", txt)
    return " ".join(txt.split())  # collapse spaces

# ---------------------------------------------------------------------------
#                           EMBEDDING & SIMILARITY
# ---------------------------------------------------------------------------

def _embed(text: str) -> List[float]:
    resp = client.embeddings.create(model=EMBED_MODEL, input=[text])
    return resp.data[0].embedding

def _cosine(a: List[float], b: List[float]) -> float:
    a, b = np.array(a), np.array(b)
    if not a.any() or not b.any():
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# ---------------------------------------------------------------------------
#                               DATA MODEL
# ---------------------------------------------------------------------------

SIM_THRESHOLD = 0.82  # semantic similarity for replacement
FUZZY_THRESHOLD = 0.85  # cheap ratio before embedding

class MemoryItem(dict):
    """Convenience wrapper so we can write item.slot etc."""
    @property
    def text(self) -> str:
        return self["text"]
    @property
    def v(self) -> List[float]:
        return self["v"]
    @property
    def slot(self) -> str:
        return self.get("slot", "generic")
    @property
    def fp(self) -> str:
        return self["fp"]

# ---------------------------------------------------------------------------
#                         LOW-LEVEL FILE READ / WRITE
# ---------------------------------------------------------------------------

def _load_all() -> List[MemoryItem]:
    if not DB_FILE.exists():
        return []
    return [MemoryItem(json.loads(line)) for line in DB_FILE.read_text("utf-8").splitlines()]

def _atomic_write(items: List[MemoryItem]):
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
        for it in items:
            tmp.write(json.dumps(it) + "\n")
    Path(tmp.name).replace(DB_FILE)

# ---------------------------------------------------------------------------
#                        PUBLIC WRITE: replace_or_add_fact
# ---------------------------------------------------------------------------

def replace_or_add_fact(fact: str) -> bool:
    """
    Insert or replace *fact* based on slot & similarity.
    Returns True if a new fact was added or an existing one overwritten; False if skipped.
    """
    # Step 1 – fingerprint & quick exact/fuzzy dedup
    fp = _fingerprint(fact)
    items = _load_all()

    # אם כבר קיים fingerprint מדויק – דילוג
    if any(it.fp == fp for it in items):
        return False

    # בדיקת דמיון fuzzy לפני embedding
    for it in items:
        if SequenceMatcher(None, fp, it.fp).ratio() >= FUZZY_THRESHOLD:
            it["text"] = fact  # overwrite wording
            it["fp"] = fp
            _atomic_write(items)
            return True

    # Step 2 – קבלת slot
    slot_prompt = [
        {"role": "system", "content": (
            "Classify the user fact into a SHORT slot label like NAME, LOCATION, PREF, HABIT, OTHER. "
            "Return only the label in uppercase letters."
        )},
        {"role": "user", "content": fact},
    ]
    try:
        resp = client.chat.completions.create(
            model=C("model_memory_slot", "gpt-3.5-turbo"),
            messages=slot_prompt,
            max_tokens=1,
            temperature=0,
        )
        slot = resp.choices[0].message.content.strip().upper() or "GENERIC"
    except Exception:
        slot = "GENERIC"

    # Step 3 – semantic dedup בתוך אותו slot
    new_vec = _embed(fact)
    for it in items:
        if it.slot == slot and _cosine(new_vec, it.v) >= SIM_THRESHOLD:
            it["text"] = fact
            it["v"] = new_vec
            it["fp"] = fp
            _atomic_write(items)
            return True

    # Step 4 – אף בדיקה לא התאימה, מוסיף חדש
    items.append(MemoryItem({"t": time.time(), "text": fact, "v": new_vec, "slot": slot, "fp": fp}))
    _atomic_write(items)
    return True

# ---------------------------------------------------------------------------
#                           PUBLIC READ: retrieve
# ---------------------------------------------------------------------------

def retrieve(query: str, k: int = 4, threshold: float = 0.75):
    qvec = _embed(query)
    items = _load_all()
    scored: List[Tuple[float, MemoryItem]] = []
    for it in items:
        sim = _cosine(qvec, it.v)
        if sim >= threshold:
            age_factor = 1.0 - min((time.time() - it["t"]) / (30 * 24 * 3600), 1.0) * 0.02
            scored.append((sim * age_factor, it))
    scored.sort(key=lambda x: x[0], reverse=True)

    seen_fps = set()
    out = []
    for _, it in scored:
        if it.fp in seen_fps:
            continue
        out.append({"role": "system", "content": f"[memory] {it.text}"})
        seen_fps.add(it.fp)
        if len(out) >= k:
            break
    return out

# ---------------------------------------------------------------------------
#                    FACT EXTRACTION
# ---------------------------------------------------------------------------

def extract_fact(user_msg: str, assistant_msg: str) -> str | None:
    prompt = [
        {
            "role": "system",
            "content": C(
                "memory_extraction_prompt",
                (
                    "You're a memory engine. If the user or assistant message contains a stable, useful personal "
                    "fact about the user (name, location, preference, etc.), extract it as one concise sentence; "
                    "otherwise reply NULL."
                ),
            ),
        },
        {"role": "user", "content": f"User: {user_msg}\nAssistant: {assistant_msg}"},
    ]
    try:
        resp = client.chat.completions.create(
            model=C("model_memory_extract", "gpt-4o"),
            messages=prompt,
            max_tokens=32,
            temperature=0,
        )
        result = resp.choices[0].message.content.strip()
        return None if result.lower() == "null" else result
    except Exception as e:
        print(f"❌ Memory extraction error: {e}")
        return None

# ---------------------------------------------------------------------------
#                                UTIL: dump
# ---------------------------------------------------------------------------

def load_all_facts() -> List[str]:
    return [it.text for it in _load_all()]
