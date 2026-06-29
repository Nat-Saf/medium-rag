"""The ONLY module that touches Pinecone."""
from pinecone import Pinecone, ServerlessSpec
from lib import config

_pc = None
_index = None

def _client():
    global _pc
    if _pc is None:
        _pc = Pinecone(api_key=config.PINECONE_API_KEY)
    return _pc


def _g(m, k, default=None):
    """Read a field from a Pinecone match whether it's a dict or an object."""
    if isinstance(m, dict):
        return m.get(k, default)
    return getattr(m, k, default)


def ensure_index(cloud="aws", region="us-east-1"):
    """Create the serverless index if it doesn't exist (idempotent)."""
    pc = _client()
    names = [ix["name"] for ix in pc.list_indexes()]
    if config.INDEX_NAME not in names:
        pc.create_index(
            name=config.INDEX_NAME,
            dimension=config.EMBED_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud=cloud, region=region),
        )


def get_index():
    global _index
    if _index is None:
        _index = _client().Index(config.INDEX_NAME)
    return _index


def upsert(records, batch=100):
    """records: [{id, values, metadata}] -> total upserted."""
    index, total = get_index(), 0
    for i in range(0, len(records), batch):
        index.upsert(vectors=records[i:i + batch])
        total += len(records[i:i + batch])
    return total


def query(vector, top_k):
    """query vector + k -> [{id, score, metadata}] (sorted by score desc)."""
    res = get_index().query(vector=vector, top_k=top_k, include_metadata=True)
    matches = res["matches"] if isinstance(res, dict) else res.matches
    return [{"id": _g(m, "id"), "score": _g(m, "score"),
             "metadata": _g(m, "metadata", {}) or {}} for m in matches]
