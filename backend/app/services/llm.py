# Butterbase is the single LLM provider. Its AI gateway is OpenAI-compatible,
# so use the OpenAI client with Butterbase's app-scoped base URL.
# This key stays on the backend — never exposed to web or Roblox.
from openai import OpenAI
from app.config import settings

client = OpenAI(
    api_key=settings.BUTTERBASE_API_KEY,
    base_url=settings.BUTTERBASE_AI_BASE_URL,
)

def complete(system: str, user: str, model: str, max_tokens: int = 2000) -> str:
    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content or ""
