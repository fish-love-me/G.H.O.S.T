import json, time, openai, numpy as np
from pathlib import Path

EMBED_MODEL = "text-embedding-3-small"
DB_FILE = Path("ghost/memory_store.jsonl")

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

client = openai.OpenAI(api_key=CONFIG["openai_api_key"])

def embed(text: str) -> list[float]:
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=[text]
    )
    return response.data[0].embedding


def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def replace_or_add_fact(fact: str, similarity_threshold=0.9):
    new_vec = embed(fact)
    updated = False
    entries = []

    if DB_FILE.exists():
        with open(DB_FILE, "r", encoding="utf-8") as f:
            for line in f:
                item = json.loads(line)
                sim = cosine_similarity(new_vec, item["v"])
                if sim >= similarity_threshold:
                    # מחליף את הזיכרון הישן בחדש
                    entries.append({
                        "t": time.time(),
                        "text": fact,
                        "v": new_vec
                    })
                    updated = True
                else:
                    entries.append(item)

    if not updated:
        # לא מצאנו דומה → מוסיפים חדש
        entries.append({
            "t": time.time(),
            "text": fact,
            "v": new_vec
        })

    with open(DB_FILE, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")

def retrieve(query: str, k=4, threshold=0.8):
    qvec = embed(query)
    if not DB_FILE.exists():
        return []
    
    memories = []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            sim = cosine_similarity(qvec, item["v"])
            if sim >= threshold:
                memories.append((sim, item["text"]))
    memories.sort(reverse=True)
    return [{"role": "system", "content": f"[memory] {text}"} for _, text in memories[:k]]

def extract_fact(user: str, assistant: str) -> str | None:
    prompt = [
        {
            "role": "system",
            "content": "You're a memory engine. If the user's message or your response includes a stable, useful personal fact (like name, location, preferences, family, or lifestyle), extract it as one short sentence. If not, return: null"
        },
        {
            "role": "user",
            "content": f"User: {user}\nAssistant: {assistant}"
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=prompt
    )

    result = response.choices[0].message.content.strip()
    return None if result.lower() == "null" else result


