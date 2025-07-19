import openai, json

def classify_task(text: str) -> str:
    with open("config.json") as f:
        api_key = json.load(f)["openai_api_key"]

    client = openai.OpenAI(api_key=api_key)

    system_prompt = """Classify the user input as one of:
- command
- conversation
- question
- system_control
- unknown
Respond with one word only."""

    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": text}],
        temperature=0
    )

    return response.choices[0].message.content.strip().lower()
