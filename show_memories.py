import json
from pathlib import Path

DB_FILE = Path("ghost/memory_store.jsonl")

def show_memories():
    if not DB_FILE.exists():
        print("❌ קובץ הזיכרון לא קיים.")
        return

    with open(DB_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        print("⚠️ אין כרגע זיכרונות בקובץ.")
        return

    print("\n📚 זיכרונות שמורים:\n")
    for i, line in enumerate(lines, 1):
        try:
            item = json.loads(line)
            print(f"[{i}] {item.get('text', '[ללא טקסט]')}")
        except json.JSONDecodeError:
            print(f"[{i}] ⚠️ שגיאה בפענוח השורה")

if __name__ == "__main__":
    show_memories()
