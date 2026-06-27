"""Token-aware chunking. No network. Chunks never cross article boundaries."""
from lib import config

try:
    import tiktoken
    _enc = tiktoken.get_encoding("cl100k_base")   # text-embedding-3-small tokenizer family
    def _encode(t): return _enc.encode(t)
    def _decode(toks): return _enc.decode(toks)
except Exception:
    # Fallback if tiktoken/vocab is unavailable: approximate with whitespace tokens.
    def _encode(t): return t.split()
    def _decode(toks): return " ".join(toks)


def chunk_text(text, chunk_size=None, overlap_ratio=None):
    """One article body -> list of token-bounded, overlapping chunk strings."""
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap_ratio = config.OVERLAP_RATIO if overlap_ratio is None else overlap_ratio
    text = (text or "").strip()
    if not text:
        return []
    toks = _encode(text)
    if len(toks) <= chunk_size:
        return [text]
    stride = max(1, int(chunk_size * (1 - overlap_ratio)))
    chunks, start = [], 0
    while start < len(toks):
        window = toks[start:start + chunk_size]
        chunks.append(_decode(window).strip())
        if start + chunk_size >= len(toks):
            break
        start += stride
    return chunks


def chunk_article(article_id, row):
    """One CSV row -> upsert-ready records (id, chunk text, metadata). No vectors yet."""
    records = []
    for i, ch in enumerate(chunk_text(row.get("text", ""))):
        records.append({
            "id": f"{article_id}-c{i}",
            "chunk": ch,
            "metadata": {
                "article_id": str(article_id),
                "title": row.get("title", "") or "",
                "url": row.get("url", "") or "",
                "authors": row.get("authors", "") or "",
                "chunk": ch,
            },
        })
    return records
