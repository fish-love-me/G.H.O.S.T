import openai
import json

def handle(text: str):
    with open("config.json") as f:
        api_key = json.load(f)["openai_api_key"]

    client = openai.OpenAI(api_key=api_key)

    system = "You're a friendly assistant named G.H.O.S.T. Speak casually and naturally."
    response = client.chat.completions.create(
        model="chatgpt-4o-latest",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content

def handle_streaming(text: str):
    with open("config.json") as f:
        api_key = json.load(f)["openai_api_key"]

    client = openai.OpenAI(api_key=api_key)

    system = "You're a friendly assistant named G.H.O.S.T. Speak casually and naturally."

    stream = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": text}
        ],
        stream=True
    )

    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
