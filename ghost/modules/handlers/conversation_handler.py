import openai, json

def handle(text: str):
    with open("config.json") as f:
        api_key = json.load(f)["openai_api_key"]

    client = openai.OpenAI(api_key=api_key)

    system = "You're a friendly assistant named G.H.O.S.T. Speak casually and naturally."
    response = client.chat.completions.create(
        model="",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content
