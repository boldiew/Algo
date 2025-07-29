import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY", "")

async def chat_completion(prompt: str, system: str = "You are a trading assistant") -> str:
    """Query OpenAI chat completion asynchronously."""
    if not openai.api_key:
        raise RuntimeError("OPENAI_API_KEY not provided")
    resp = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return resp.choices[0].message["content"].strip()
