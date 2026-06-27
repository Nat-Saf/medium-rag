"""The ONLY module that calls LLMod embeddings. Batched."""
from openai import OpenAI
from lib import config

_client = None
def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=config.LLMOD_API_KEY, base_url=config.LLMOD_BASE_URL)
    return _client


def embed_texts(texts):
    """list[str] -> list[list[float]] (1536-d), order preserved, EMBED_BATCH per call."""
    if not texts:
        return []
    client, out = _get_client(), []
    for i in range(0, len(texts), config.EMBED_BATCH):
        batch = texts[i:i + config.EMBED_BATCH]
        resp = client.embeddings.create(model=config.EMBED_MODEL, input=batch)
        for item in sorted(resp.data, key=lambda d: d.index):
            out.append(item.embedding)
    return out
