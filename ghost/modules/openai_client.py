import json
import openai

with open("config.json", "r") as f:
    config = json.load(f)

client = openai.OpenAI(api_key=config["openai_api_key"])
