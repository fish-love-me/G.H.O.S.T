import openai, json

def handle(text: str):
    with open("config.json") as f:
        api_key = json.load(f)["openai_api_key"]

    client = openai.OpenAI(api_key=api_key)

    system = "Answer user questions clearly and concisely. Be correct and helpful."
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content
