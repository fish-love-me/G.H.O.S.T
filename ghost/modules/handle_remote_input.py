from modules.handlers import command_handler  # או כל מודול שאתה רוצה להריץ

def handle_remote_input(text: str) -> str:
    return command_handler.handle(text)
