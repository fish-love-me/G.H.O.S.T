from ghost.modules.handlers import (
    command_handler, conversation_handler
)

def route_task(task_type: str, text: str):
    if task_type == "command":
        return command_handler.handle(text)
    elif task_type == "conversation":
        return conversation_handler.handle(text)
    else:
        return "❌ I didn't understand what to do."
