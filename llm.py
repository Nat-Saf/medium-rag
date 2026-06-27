"""The ONLY module that calls LLMod chat (gpt-5-mini)."""
from openai import OpenAI
from lib import config

_client = None
def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=config.LLMOD_API_KEY, base_url=config.LLMOD_BASE_URL)
    return _client


def generate(system, user):
    """(system, user) -> answer string."""
    resp = _get_client().chat.completions.create(
        model=config.CHAT_MODEL,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
    )
    return resp.choices[0].message.content
