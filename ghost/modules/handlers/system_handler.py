def handle(text: str):
    if "shutdown" in text:
        # os.system("shutdown now") # disabled for safety
        return "⚠️ Shutdown command issued (not executed)."
    if "open" in text and "notepad" in text:
        return "📝 Opening Notepad (stub)."
    return "🧭 System command not implemented."
