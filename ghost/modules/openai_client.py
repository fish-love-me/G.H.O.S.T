# ghost/openai_client.py
import json
import openai

class Config:
    def __init__(self):
        with open("config.json", "r", encoding="utf-8") as f:
            self._data = json.load(f)
        self.client = openai.OpenAI(api_key=self._data["openai_api_key"])

    def get(self, key: str, default=None):
        return self._data.get(key, default)

config = Config()
